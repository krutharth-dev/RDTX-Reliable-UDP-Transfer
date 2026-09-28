"""Flask application for RDTX VisualLab."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, render_template, request, stream_with_context

from rdtx import __version__
from .engine import RunManager


def _probability_percent(value: str, field: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not 0.0 <= number <= 100.0:
        raise ValueError(f"{field} must be between 0 and 100")
    return number / 100.0


def _bounded_int(value: str, field: str, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return number


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATA_DIR=str(Path.cwd() / "visual_lab_data"),
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
    )
    if config:
        app.config.update(config)

    manager = RunManager(app.config["DATA_DIR"])
    app.extensions["rdtx_manager"] = manager

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/runs")
    def create_run():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"error": "Choose a file to transfer."}), 400

        try:
            params = {
                "window_size": _bounded_int(
                    request.form.get("window_size", "8"), "window size", 1, 64
                ),
                "chunk_size": _bounded_int(
                    request.form.get("chunk_size", "1024"), "chunk size", 128, 60000
                ),
                "timeout": _bounded_int(
                    request.form.get("timeout_ms", "350"), "timeout", 20, 5000
                )
                / 1000.0,
                "loss": _probability_percent(
                    request.form.get("loss", "0"), "packet loss"
                ),
                "ack_loss": _probability_percent(
                    request.form.get("ack_loss", "0"), "ACK loss"
                ),
                "corruption": _probability_percent(
                    request.form.get("corruption", "0"), "corruption"
                ),
                "ack_corruption": 0.0,
                "delay_ms": float(request.form.get("delay_ms", "0")),
                "ack_delay_ms": 0.0,
                "reorder": _probability_percent(
                    request.form.get("reorder", "0"), "reordering"
                ),
                "seed": _bounded_int(
                    request.form.get("seed", "2026"), "seed", 0, 2_147_483_647
                ),
            }
            if not 0.0 <= params["delay_ms"] <= 5000.0:
                raise ValueError("delay must be between 0 and 5000 ms")
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

        run_id = manager.start(upload.filename, upload.read(), params)
        return jsonify({"run_id": run_id}), 202

    @app.get("/api/runs/<run_id>")
    def run_status(run_id: str):
        run = manager.store.get(run_id)
        if run is None:
            return jsonify({"error": "run not found"}), 404
        return jsonify(run)

    @app.get("/api/runs/<run_id>/events")
    def run_events(run_id: str):
        if manager.store.get(run_id) is None:
            return jsonify({"error": "run not found"}), 404

        @stream_with_context
        def generate():
            for event in manager.events.iter_events(run_id):
                yield f"data: {json.dumps(event)}\n\n"

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.get("/api/history")
    def history():
        return jsonify(manager.store.history(limit=20))

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rdtx-web",
        description="Start the local RDTX VisualLab web dashboard.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="web server bind host")
    parser.add_argument("--port", type=int, default=5000, help="web server port")
    parser.add_argument("--version", action="version", version=f"RDTX VisualLab {__version__}")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not 1 <= args.port <= 65_535:
        raise SystemExit("--port must be between 1 and 65535")
    app = create_app()
    print(f"RDTX VisualLab: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True, debug=False)


if __name__ == "__main__":
    main()
