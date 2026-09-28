"""Experiment orchestration for the RDTX VisualLab web application."""

from __future__ import annotations

import json
import socket
import sqlite3
import threading
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from rdtx.receiver import RDTXReceiver
from rdtx.sender import RDTXSender


class EventJournal:
    """Keep live experiment events and support late SSE subscribers."""

    def __init__(self) -> None:
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._done: set[str] = set()
        self._conditions: dict[str, threading.Condition] = {}
        self._lock = threading.Lock()

    def create(self, run_id: str) -> None:
        with self._lock:
            self._events[run_id] = []
            self._conditions[run_id] = threading.Condition()
            self._done.discard(run_id)

    def publish(self, run_id: str, event: dict[str, Any]) -> None:
        condition = self._conditions[run_id]
        with condition:
            event = {"timestamp": time.time(), **event}
            self._events[run_id].append(event)
            condition.notify_all()

    def finish(self, run_id: str) -> None:
        condition = self._conditions[run_id]
        with condition:
            self._done.add(run_id)
            condition.notify_all()

    def iter_events(self, run_id: str) -> Iterator[dict[str, Any]]:
        condition = self._conditions[run_id]
        index = 0
        while True:
            with condition:
                while index >= len(self._events[run_id]) and run_id not in self._done:
                    condition.wait(timeout=1.0)

                pending = self._events[run_id][index:]
                index = len(self._events[run_id])
                done = run_id in self._done

            yield from pending
            if done and index >= len(self._events[run_id]):
                return


class ExperimentStore:
    """SQLite-backed experiment history."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    params_json TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def create(self, run_id: str, filename: str, params: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute(
                "INSERT INTO experiments VALUES (?, ?, ?, ?, ?, NULL, NULL)",
                (run_id, filename, "queued", time.time(), json.dumps(params)),
            )

    def update(
        self,
        run_id: str,
        *,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        with self._connect() as db:
            db.execute(
                """
                UPDATE experiments
                SET status = ?, result_json = ?, error = ?
                WHERE id = ?
                """,
                (
                    status,
                    json.dumps(result) if result is not None else None,
                    error,
                    run_id,
                ),
            )

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "filename": row["filename"],
            "status": row["status"],
            "created_at": row["created_at"],
            "params": json.loads(row["params_json"]),
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
            "error": row["error"],
        }

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM experiments WHERE id = ?", (run_id,)
            ).fetchone()
        return self._row(row) if row else None

    def history(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row(row) for row in rows]


class VisualSender(RDTXSender):
    def __init__(self, *args: Any, emit, **kwargs: Any) -> None:
        self._emit_web = emit
        super().__init__(*args, **kwargs)

    def _trace(self, message: str) -> None:
        self._emit_web("sender", message)

    def _log(self, message: str) -> None:
        self._emit_web("sender-log", message)


class VisualReceiver(RDTXReceiver):
    def __init__(self, *args: Any, emit, **kwargs: Any) -> None:
        self._emit_web = emit
        super().__init__(*args, **kwargs)

    def _trace(self, message: str) -> None:
        self._emit_web("receiver", message)

    def _log(self, message: str) -> None:
        self._emit_web("receiver-log", message)


def free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class RunManager:
    """Run real localhost UDP transfers and expose events/history to the web UI."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = ExperimentStore(self.data_dir / "visual_lab.sqlite3")
        self.events = EventJournal()

    def start(self, filename: str, payload: bytes, params: dict[str, Any]) -> str:
        run_id = uuid.uuid4().hex[:12]
        safe_name = Path(filename).name or "upload.bin"
        run_dir = self.data_dir / "runs" / run_id
        input_dir = run_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        source = input_dir / safe_name
        source.write_bytes(payload)

        self.events.create(run_id)
        self.store.create(run_id, safe_name, params)
        thread = threading.Thread(
            target=self._run,
            args=(run_id, source, run_dir, params),
            daemon=True,
        )
        thread.start()
        return run_id

    def _emit(self, run_id: str, side: str, message: str) -> None:
        if "DROP" in message:
            kind = "drop"
        elif "ACK" in message:
            kind = "ack"
        elif "REORDER" in message:
            kind = "reorder"
        elif "DATA" in message:
            kind = "data"
        elif "COMPLETE" in message:
            kind = "complete"
        else:
            kind = "info"
        self.events.publish(
            run_id,
            {"kind": kind, "side": side, "message": message},
        )

    def _run(
        self,
        run_id: str,
        source: Path,
        run_dir: Path,
        params: dict[str, Any],
    ) -> None:
        emit = lambda side, message: self._emit(run_id, side, message)
        self.store.update(run_id, status="running")
        self.events.publish(
            run_id,
            {
                "kind": "status",
                "side": "system",
                "message": "Experiment started",
                "status": "running",
            },
        )

        port = free_udp_port()
        output_dir = run_dir / "received"
        receiver_state: dict[str, Any] = {}

        try:
            receiver = VisualReceiver(
                "127.0.0.1",
                port,
                output_dir=output_dir,
                ack_loss=float(params["ack_loss"]),
                ack_corruption=float(params["ack_corruption"]),
                ack_delay_ms=float(params["ack_delay_ms"]),
                seed=int(params["seed"]),
                linger=0.15,
                verbose=False,
                trace=True,
                emit=emit,
            )

            def receive() -> None:
                try:
                    path, stats = receiver.receive_one()
                    receiver_state["path"] = path
                    receiver_state["stats"] = stats
                except BaseException as exc:
                    receiver_state["error"] = exc

            receiver_thread = threading.Thread(target=receive, daemon=True)
            receiver_thread.start()
            time.sleep(0.05)

            sender = VisualSender(
                "127.0.0.1",
                port,
                chunk_size=int(params["chunk_size"]),
                window_size=int(params["window_size"]),
                timeout=float(params["timeout"]),
                max_retries=80,
                loss=float(params["loss"]),
                corruption=float(params["corruption"]),
                delay_ms=float(params["delay_ms"]),
                reorder_rate=float(params["reorder"]),
                seed=int(params["seed"]),
                verbose=False,
                trace=True,
                emit=emit,
            )
            sender_stats = sender.send_file(source)

            receiver_thread.join(timeout=3)
            if receiver_thread.is_alive():
                raise RuntimeError("receiver did not finish after sender completion")
            if "error" in receiver_state:
                raise RuntimeError(f"receiver failed: {receiver_state['error']}")

            received_path = receiver_state["path"]
            receiver_stats = receiver_state["stats"]
            integrity = (
                isinstance(received_path, Path)
                and received_path.read_bytes() == source.read_bytes()
            )
            if not integrity:
                raise RuntimeError("byte-for-byte integrity verification failed")

            result = {
                "integrity": "PASS",
                "output_file": str(received_path),
                "sender": {
                    **asdict(sender_stats),
                    "throughput_kib_s": sender_stats.throughput_kib_s,
                },
                "receiver": {
                    **asdict(receiver_stats),
                    "throughput_kib_s": receiver_stats.throughput_kib_s,
                },
            }
            self.store.update(run_id, status="completed", result=result)
            self.events.publish(
                run_id,
                {
                    "kind": "status",
                    "side": "system",
                    "message": "Transfer completed with byte-for-byte integrity",
                    "status": "completed",
                    "result": result,
                },
            )
        except BaseException as exc:
            message = str(exc)
            self.store.update(run_id, status="failed", error=message)
            self.events.publish(
                run_id,
                {
                    "kind": "status",
                    "side": "system",
                    "message": message,
                    "status": "failed",
                },
            )
        finally:
            self.events.finish(run_id)
