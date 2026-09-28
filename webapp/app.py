"""Flask application for RDTX VisualLab."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
    stream_with_context,
)

from rdtx import __version__
from .engine import RunManager


def _probability_percent(value: str, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 100.0:
        raise ValueError(f"{field} must be between 0 and 100")
    return number / 100.0


def _bounded_int(value: str, field: str, minimum: int, maximum: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be an integer") from exc
    if not minimum <= number <= maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return number


def _bounded_float(value: str, field: str, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{field} must be between {minimum:g} and {maximum:g}")
    return number


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATA_DIR=str(Path.cwd() / "visual_lab_data"),
        MAX_CONTENT_LENGTH=32 * 1024 * 1024,
        MAX_ACTIVE_RUNS=3,
    )
    if config:
        app.config.update(config)

    manager = RunManager(
        app.config["DATA_DIR"],
        max_active_runs=int(app.config["MAX_ACTIVE_RUNS"]),
    )
    app.extensions["rdtx_manager"] = manager

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        return response

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify(
            {
                "error": "File is too large for VisualLab. "
                f"Maximum upload size is {app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)} MiB."
            }
        ), 413

    @app.get("/")
    def index():
        return render_template("index.html", version=__version__)

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "version": __version__,
                "active_runs": manager.active_count,
                "max_active_runs": manager.max_active_runs,
                "transport": "UDP",
                "arq": "Selective Repeat",
            }
        )

    @app.post("/api/runs")
    def create_run():
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return jsonify({"error": "Choose a file to transfer."}), 400

        try:
            label = (request.form.get("label") or "").strip()[:60]
            params = {
                "label": label,
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
                "ack_corruption": _probability_percent(
                    request.form.get("ack_corruption", "0"), "ACK corruption"
                ),
                "delay_ms": _bounded_float(
                    request.form.get("delay_ms", "0"), "delay", 0.0, 5000.0
                ),
                "ack_delay_ms": _bounded_float(
                    request.form.get("ack_delay_ms", "0"), "ACK delay", 0.0, 5000.0
                ),
                "reorder": _probability_percent(
                    request.form.get("reorder", "0"), "reordering"
                ),
                "seed": _bounded_int(
                    request.form.get("seed", "2026"), "seed", 0, 2_147_483_647
                ),
            }
            run_id = manager.start(upload.filename, upload.read(), params)
        except (RuntimeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400

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

    @app.get("/api/runs/<run_id>/export")
    def export_run(run_id: str):
        run = manager.store.get(run_id)
        if run is None:
            return jsonify({"error": "run not found"}), 404
        payload = json.dumps(run, indent=2, sort_keys=True) + "\n"
        return Response(
            payload,
            mimetype="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="rdtx-run-{run_id}.json"'
            },
        )

    @app.get("/api/runs/<run_id>/download")
    def download_output(run_id: str):
        path = manager.output_path(run_id)
        if path is None:
            return jsonify({"error": "completed output file is not available"}), 404
        return send_file(
            path,
            as_attachment=True,
            download_name=path.name,
            max_age=0,
        )

    @app.get("/api/history")
    def history():
        try:
            limit = _bounded_int(request.args.get("limit", "30"), "limit", 1, 100)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(manager.store.history(limit=limit))

    @app.get("/api/history.csv")
    def history_csv():
        rows = manager.store.history(limit=100)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "run_id",
                "label",
                "filename",
                "status",
                "window",
                "data_loss_pct",
                "ack_loss_pct",
                "corruption_pct",
                "reorder_pct",
                "retransmissions",
                "throughput_kib_s",
                "integrity",
            ]
        )
        for run in rows:
            params = run["params"]
            sender = (run["result"] or {}).get("sender", {})
            writer.writerow(
                [
                    run["id"],
                    params.get("label", ""),
                    run["filename"],
                    run["status"],
                    params.get("window_size", ""),
                    round(float(params.get("loss", 0)) * 100, 2),
                    round(float(params.get("ack_loss", 0)) * 100, 2),
                    round(float(params.get("corruption", 0)) * 100, 2),
                    round(float(params.get("reorder", 0)) * 100, 2),
                    sender.get("retransmissions", ""),
                    sender.get("throughput_kib_s", ""),
                    (run["result"] or {}).get("integrity", ""),
                ]
            )
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="rdtx-visual-lab-history.csv"'
            },
        )

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
