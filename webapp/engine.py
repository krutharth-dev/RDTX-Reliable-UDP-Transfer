"""Experiment orchestration for RDTX VisualLab."""

from __future__ import annotations
import json, re, socket, sqlite3, threading, time, uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterator

from rdtx.receiver import RDTXReceiver
from rdtx.sender import RDTXSender


class EventJournal:
    def __init__(self, max_events_per_run: int = 5000) -> None:
        self.max_events_per_run = max_events_per_run
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
            events = self._events[run_id]
            events.append({"timestamp": time.time(), **event})
            if len(events) > self.max_events_per_run:
                del events[: len(events) - self.max_events_per_run]
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
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL, status TEXT NOT NULL,
                created_at REAL NOT NULL, params_json TEXT NOT NULL, result_json TEXT, error TEXT)""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def create(self, run_id: str, filename: str, params: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO experiments VALUES (?, ?, ?, ?, ?, NULL, NULL)",
                       (run_id, filename, "queued", time.time(), json.dumps(params)))

    def update(self, run_id: str, *, status: str, result=None, error=None) -> None:
        with self._connect() as db:
            db.execute("UPDATE experiments SET status=?, result_json=?, error=? WHERE id=?",
                       (status, json.dumps(result) if result is not None else None, error, run_id))

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        return {"id": row["id"], "filename": row["filename"], "status": row["status"],
                "created_at": row["created_at"], "params": json.loads(row["params_json"]),
                "result": json.loads(row["result_json"]) if row["result_json"] else None,
                "error": row["error"]}

    def get(self, run_id: str):
        with self._connect() as db:
            row = db.execute("SELECT * FROM experiments WHERE id=?", (run_id,)).fetchone()
        return self._row(row) if row else None

    def history(self, limit: int = 20):
        with self._connect() as db:
            rows = db.execute("SELECT * FROM experiments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row(row) for row in rows]


class VisualSender(RDTXSender):
    def __init__(self, *args, emit, **kwargs):
        self._emit_web = emit
        super().__init__(*args, **kwargs)
    def _trace(self, message): self._emit_web("sender", message)
    def _log(self, message): self._emit_web("sender-log", message)


class VisualReceiver(RDTXReceiver):
    def __init__(self, *args, emit, **kwargs):
        self._emit_web = emit
        super().__init__(*args, **kwargs)
    def _trace(self, message): self._emit_web("receiver", message)
    def _log(self, message): self._emit_web("receiver-log", message)


def free_udp_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class RunManager:
    def __init__(self, data_dir: str | Path, max_active_runs: int = 3) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.store = ExperimentStore(self.data_dir / "visual_lab.sqlite3")
        self.events = EventJournal()
        self.max_active_runs = max_active_runs
        self._active: set[str] = set()
        self._active_lock = threading.Lock()

    @property
    def active_count(self) -> int:
        with self._active_lock:
            return len(self._active)

    def start(self, filename: str, payload: bytes, params: dict[str, Any]) -> str:
        run_id = uuid.uuid4().hex[:12]
        with self._active_lock:
            if len(self._active) >= self.max_active_runs:
                raise RuntimeError(f"VisualLab is already running {self.max_active_runs} experiments.")
            self._active.add(run_id)
        safe_name = Path(filename).name or "upload.bin"
        run_dir = self.data_dir / "runs" / run_id
        source = run_dir / "input" / safe_name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(payload)
        self.events.create(run_id)
        self.store.create(run_id, safe_name, params)
        threading.Thread(target=self._run, args=(run_id, source, run_dir, params),
                         daemon=True, name=f"rdtx-run-{run_id}").start()
        return run_id

    def output_path(self, run_id: str):
        run = self.store.get(run_id)
        if not run or run["status"] != "completed" or not run["result"]:
            return None
        raw = run["result"].get("output_file")
        if not raw:
            return None
        candidate = Path(raw).resolve()
        allowed = (self.data_dir / "runs" / run_id).resolve()
        return candidate if allowed in candidate.parents and candidate.is_file() else None

    def _emit(self, run_id: str, side: str, message: str) -> None:
        upper = message.upper()
        kind = ("retransmission" if "RETRANSMISSION" in upper else
                "drop" if "DROP" in upper else "reorder" if "REORDER" in upper else
                "ack" if "ACK" in upper else "data" if "DATA" in upper else
                "complete" if "COMPLETE" in upper else "info")
        event: dict[str, Any] = {"kind": kind, "side": side, "message": message}
        seq = re.search(r"seq=(\d+)", message)
        if seq: event["seq"] = int(seq.group(1))
        window = re.search(r"window base (\d+)->(\d+) range=\[(\d+),(\d+)\)", message)
        if window:
            event["window"] = {"old_base": int(window.group(1)), "base": int(window.group(2)),
                               "start": int(window.group(3)), "end": int(window.group(4))}
        self.events.publish(run_id, event)

    def _sender(self, run_id, params, host, port):
        emit = lambda side, message: self._emit(run_id, side, message)
        return VisualSender(host, port, chunk_size=int(params["chunk_size"]),
            window_size=int(params["window_size"]), timeout=float(params["timeout"]),
            max_retries=80, loss=float(params["loss"]), corruption=float(params["corruption"]),
            delay_ms=float(params["delay_ms"]), reorder_rate=float(params["reorder"]),
            seed=int(params["seed"]), verbose=False, trace=True, emit=emit)

    def _run(self, run_id, source, run_dir, params):
        mode = params.get("mode", "local")
        self.store.update(run_id, status="running")
        self.events.publish(run_id, {"kind":"status","side":"system",
            "message":f"Experiment started in {mode.upper()} mode","status":"running"})
        try:
            if mode == "lan": self._run_lan(run_id, source, params)
            else: self._run_local(run_id, source, run_dir, params)
        except BaseException as exc:
            self.store.update(run_id, status="failed", error=str(exc))
            self.events.publish(run_id, {"kind":"status","side":"system","message":str(exc),"status":"failed"})
        finally:
            with self._active_lock: self._active.discard(run_id)
            self.events.finish(run_id)

    def _run_local(self, run_id, source, run_dir, params):
        emit = lambda side, message: self._emit(run_id, side, message)
        port = free_udp_port()
        state = {}
        receiver = VisualReceiver("127.0.0.1", port, output_dir=run_dir/"received",
            ack_loss=float(params["ack_loss"]), ack_corruption=float(params["ack_corruption"]),
            ack_delay_ms=float(params["ack_delay_ms"]), seed=int(params["seed"]), linger=0.15,
            verbose=False, trace=True, emit=emit)
        def receive():
            try: state["path"], state["stats"] = receiver.receive_one()
            except BaseException as exc: state["error"] = exc
        thread = threading.Thread(target=receive, daemon=True)
        thread.start(); time.sleep(0.05)
        sender_stats = self._sender(run_id, params, "127.0.0.1", port).send_file(source)
        thread.join(timeout=3)
        if thread.is_alive(): raise RuntimeError("receiver did not finish")
        if "error" in state: raise RuntimeError(f"receiver failed: {state['error']}")
        path, receiver_stats = state["path"], state["stats"]
        if path.read_bytes() != source.read_bytes(): raise RuntimeError("byte-for-byte integrity failed")
        result = {"mode":"local","integrity":"PASS","verification":"byte-for-byte + receiver SHA-256",
            "output_file":str(path),
            "sender":{**asdict(sender_stats),"throughput_kib_s":sender_stats.throughput_kib_s},
            "receiver":{**asdict(receiver_stats),"throughput_kib_s":receiver_stats.throughput_kib_s}}
        self._complete(run_id, result, "Local transfer completed with byte-for-byte integrity")

    def _run_lan(self, run_id, source, params):
        host, port = str(params["target_host"]), int(params["target_port"])
        self.events.publish(run_id, {"kind":"info","side":"system","message":f"Sending to remote receiver {host}:{port}"})
        sender_stats = self._sender(run_id, params, host, port).send_file(source)
        result = {"mode":"lan","integrity":"PASS",
            "verification":"remote FIN_ACK after receiver size + SHA-256 verification",
            "output_file":None,"remote_host":host,"remote_port":port,
            "sender":{**asdict(sender_stats),"throughput_kib_s":sender_stats.throughput_kib_s},
            "receiver":{}}
        self._complete(run_id, result, "LAN transfer completed; remote receiver returned verified FIN_ACK")

    def _complete(self, run_id, result, message):
        self.store.update(run_id, status="completed", result=result)
        self.events.publish(run_id, {"kind":"status","side":"system","message":message,
                                    "status":"completed","result":result})


class MatrixManager:
    DIMENSIONS = {"window_size", "loss", "corruption", "reorder"}
    def __init__(self, run_manager: RunManager) -> None:
        self.run_manager = run_manager
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start(self, filename, payload, base_params, dimension, values):
        if dimension not in self.DIMENSIONS: raise ValueError("unsupported matrix dimension")
        if not 2 <= len(values) <= 8: raise ValueError("matrix requires between 2 and 8 values")
        job_id = uuid.uuid4().hex[:10]
        job = {"id":job_id,"filename":Path(filename).name or "matrix.bin","status":"queued",
               "dimension":dimension,"values":values,"rows":[],"created_at":time.time()}
        with self._lock: self._jobs[job_id] = job
        threading.Thread(target=self._run,args=(job_id,filename,payload,base_params,dimension,values),
                         daemon=True).start()
        return job_id

    def get(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            return json.loads(json.dumps(job)) if job else None

    def _run(self, job_id, filename, payload, base, dimension, values):
        with self._lock: self._jobs[job_id]["status"] = "running"
        for i, raw in enumerate(values):
            params = dict(base); params["mode"]="local"; params["label"]=f"matrix {dimension}={raw:g}"
            if dimension == "window_size":
                params[dimension]=int(raw); display=str(int(raw))
            else:
                params[dimension]=float(raw)/100.0; display=f"{raw:g}%"
            row={"value":raw,"display_value":display,"status":"running","run_id":None}
            with self._lock: self._jobs[job_id]["rows"].append(row)
            try:
                run_id=self.run_manager.start(filename,payload,params); row["run_id"]=run_id
                deadline=time.time()+30
                while time.time()<deadline:
                    run=self.run_manager.store.get(run_id)
                    if run and run["status"] in {"completed","failed"}:
                        row.update({"status":run["status"],"result":run["result"],"error":run["error"]}); break
                    time.sleep(0.05)
                else: row.update({"status":"failed","error":"matrix row timed out"})
            except BaseException as exc:
                row.update({"status":"failed","error":str(exc)})
            with self._lock: self._jobs[job_id]["rows"][i]=dict(row)
        with self._lock:
            rows=self._jobs[job_id]["rows"]
            self._jobs[job_id]["status"]="completed" if all(r["status"]=="completed" for r in rows) else "completed_with_errors"
