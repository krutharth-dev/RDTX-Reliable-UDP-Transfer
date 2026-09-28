"""Flask application for RDTX VisualLab."""

from __future__ import annotations
import argparse, csv, io, json, math
from pathlib import Path
from typing import Any

from flask import Flask, Response, jsonify, render_template, request, send_file, stream_with_context

from rdtx import __version__
from .engine import MatrixManager, RunManager
from .reports import build_matrix_report, build_run_report


def _probability_percent(value: str, field: str) -> float:
    try: number = float(value)
    except (TypeError, ValueError) as exc: raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or not 0.0 <= number <= 100.0:
        raise ValueError(f"{field} must be between 0 and 100")
    return number / 100.0


def _bounded_int(value: str, field: str, minimum: int, maximum: int) -> int:
    try: number = int(value)
    except (TypeError, ValueError) as exc: raise ValueError(f"{field} must be an integer") from exc
    if not minimum <= number <= maximum: raise ValueError(f"{field} must be between {minimum} and {maximum}")
    return number


def _bounded_float(value: str, field: str, minimum: float, maximum: float) -> float:
    try: number = float(value)
    except (TypeError, ValueError) as exc: raise ValueError(f"{field} must be numeric") from exc
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise ValueError(f"{field} must be between {minimum:g} and {maximum:g}")
    return number


def _params(form) -> dict[str, Any]:
    mode = (form.get("mode") or "local").strip().lower()
    if mode not in {"local","lan"}: raise ValueError("mode must be local or lan")
    params = {
        "mode": mode,
        "label": (form.get("label") or "").strip()[:60],
        "window_size": _bounded_int(form.get("window_size","8"),"window size",1,64),
        "chunk_size": _bounded_int(form.get("chunk_size","1024"),"chunk size",128,60000),
        "timeout": _bounded_int(form.get("timeout_ms","350"),"timeout",20,5000)/1000.0,
        "loss": _probability_percent(form.get("loss","0"),"packet loss"),
        "ack_loss": _probability_percent(form.get("ack_loss","0"),"ACK loss"),
        "corruption": _probability_percent(form.get("corruption","0"),"corruption"),
        "ack_corruption": _probability_percent(form.get("ack_corruption","0"),"ACK corruption"),
        "delay_ms": _bounded_float(form.get("delay_ms","0"),"delay",0,5000),
        "ack_delay_ms": _bounded_float(form.get("ack_delay_ms","0"),"ACK delay",0,5000),
        "reorder": _probability_percent(form.get("reorder","0"),"reordering"),
        "seed": _bounded_int(form.get("seed","2026"),"seed",0,2_147_483_647),
    }
    if mode == "lan":
        host = (form.get("target_host") or "").strip()
        if not host: raise ValueError("LAN mode requires a receiver host/IP")
        params["target_host"] = host
        params["target_port"] = _bounded_int(form.get("target_port","9000"),"target port",1,65535)
    return params


def _matrix_values(raw: str, dimension: str) -> list[float]:
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if not 2 <= len(parts) <= 8:
        raise ValueError("matrix values must contain between 2 and 8 comma-separated values")
    values = []
    for part in parts:
        try: value = float(part)
        except ValueError as exc: raise ValueError(f"invalid matrix value: {part}") from exc
        if not math.isfinite(value): raise ValueError("matrix values must be finite")
        if dimension == "window_size":
            if value != int(value) or not 1 <= value <= 64:
                raise ValueError("window matrix values must be integers between 1 and 64")
        elif not 0 <= value <= 100:
            raise ValueError("percentage matrix values must be between 0 and 100")
        values.append(value)
    return values


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(DATA_DIR=str(Path.cwd()/"visual_lab_data"),MAX_CONTENT_LENGTH=32*1024*1024,MAX_ACTIVE_RUNS=3)
    if config: app.config.update(config)
    manager = RunManager(app.config["DATA_DIR"],max_active_runs=int(app.config["MAX_ACTIVE_RUNS"]))
    matrices = MatrixManager(manager)
    app.extensions["rdtx_manager"] = manager
    app.extensions["rdtx_matrix_manager"] = matrices

    @app.after_request
    def security_headers(response):
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="same-origin"
        response.headers["X-Frame-Options"]="SAMEORIGIN"
        return response

    @app.errorhandler(413)
    def too_large(_error):
        size=app.config["MAX_CONTENT_LENGTH"]//(1024*1024)
        return jsonify({"error":f"File is too large for VisualLab. Maximum upload size is {size} MiB."}),413

    @app.get("/")
    def index(): return render_template("index.html",version=__version__)

    @app.get("/api/health")
    def health():
        return jsonify({"status":"ok","version":__version__,"active_runs":manager.active_count,
                        "max_active_runs":manager.max_active_runs,"transport":"UDP",
                        "arq":"Selective Repeat","modes":["local","lan"]})

    @app.post("/api/runs")
    def create_run():
        upload=request.files.get("file")
        if upload is None or not upload.filename: return jsonify({"error":"Choose a file to transfer."}),400
        try: run_id=manager.start(upload.filename,upload.read(),_params(request.form))
        except (RuntimeError,ValueError) as exc: return jsonify({"error":str(exc)}),400
        return jsonify({"run_id":run_id}),202

    @app.get("/api/runs/<run_id>")
    def run_status(run_id):
        run=manager.store.get(run_id)
        return jsonify(run) if run else (jsonify({"error":"run not found"}),404)

    @app.get("/api/runs/<run_id>/events")
    def run_events(run_id):
        if manager.store.get(run_id) is None: return jsonify({"error":"run not found"}),404
        @stream_with_context
        def generate():
            for event in manager.events.iter_events(run_id):
                yield f"data: {json.dumps(event)}\n\n"
        return Response(generate(),mimetype="text/event-stream",headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})

    @app.get("/api/runs/<run_id>/export")
    def export_run(run_id):
        run=manager.store.get(run_id)
        if run is None: return jsonify({"error":"run not found"}),404
        return Response(json.dumps(run,indent=2,sort_keys=True)+"\n",mimetype="application/json",
            headers={"Content-Disposition":f'attachment; filename="rdtx-run-{run_id}.json"'})

    @app.get("/api/runs/<run_id>/report.md")
    def run_report(run_id):
        run=manager.store.get(run_id)
        if run is None: return jsonify({"error":"run not found"}),404
        if run["status"]!="completed": return jsonify({"error":"report is available after completion"}),409
        return Response(build_run_report(run),mimetype="text/markdown",
            headers={"Content-Disposition":f'attachment; filename="rdtx-report-{run_id}.md"'})

    @app.get("/api/runs/<run_id>/download")
    def download_output(run_id):
        path=manager.output_path(run_id)
        if path is None: return jsonify({"error":"local reconstructed file is not available for this run"}),404
        return send_file(path,as_attachment=True,download_name=path.name,max_age=0)

    @app.get("/api/history")
    def history():
        try: limit=_bounded_int(request.args.get("limit","30"),"limit",1,100)
        except ValueError as exc: return jsonify({"error":str(exc)}),400
        return jsonify(manager.store.history(limit=limit))

    @app.get("/api/history.csv")
    def history_csv():
        out=io.StringIO(); w=csv.writer(out)
        w.writerow(["run_id","label","mode","filename","status","window","data_loss_pct","ack_loss_pct","corruption_pct","reorder_pct","retransmissions","throughput_kib_s","integrity"])
        for run in manager.store.history(limit=100):
            p=run["params"]; s=(run["result"] or {}).get("sender",{})
            w.writerow([run["id"],p.get("label",""),p.get("mode","local"),run["filename"],run["status"],
                p.get("window_size",""),round(float(p.get("loss",0))*100,2),round(float(p.get("ack_loss",0))*100,2),
                round(float(p.get("corruption",0))*100,2),round(float(p.get("reorder",0))*100,2),
                s.get("retransmissions",""),s.get("throughput_kib_s",""),(run["result"] or {}).get("integrity","")])
        return Response(out.getvalue(),mimetype="text/csv",headers={"Content-Disposition":'attachment; filename="rdtx-visual-lab-history.csv"'})

    @app.post("/api/matrix")
    def create_matrix():
        upload=request.files.get("file")
        if upload is None or not upload.filename: return jsonify({"error":"Choose a file for the matrix experiment."}),400
        try:
            params=_params(request.form); params["mode"]="local"
            dimension=(request.form.get("dimension") or "window_size").strip()
            if dimension not in MatrixManager.DIMENSIONS: raise ValueError("unsupported matrix dimension")
            values=_matrix_values(request.form.get("values",""),dimension)
            matrix_id=matrices.start(upload.filename,upload.read(),params,dimension,values)
        except (RuntimeError,ValueError) as exc: return jsonify({"error":str(exc)}),400
        return jsonify({"matrix_id":matrix_id}),202

    @app.get("/api/matrix/<matrix_id>")
    def matrix_status(matrix_id):
        job=matrices.get(matrix_id)
        return jsonify(job) if job else (jsonify({"error":"matrix not found"}),404)

    @app.get("/api/matrix/<matrix_id>/report.md")
    def matrix_report(matrix_id):
        job=matrices.get(matrix_id)
        if job is None: return jsonify({"error":"matrix not found"}),404
        if not str(job["status"]).startswith("completed"): return jsonify({"error":"matrix report is available after completion"}),409
        return Response(build_matrix_report(job),mimetype="text/markdown",
            headers={"Content-Disposition":f'attachment; filename="rdtx-matrix-{matrix_id}.md"'})

    return app


def build_parser():
    parser=argparse.ArgumentParser(prog="rdtx-web",description="Start the local RDTX VisualLab web dashboard.")
    parser.add_argument("--host",default="127.0.0.1",help="web server bind host")
    parser.add_argument("--port",type=int,default=5000,help="web server port")
    parser.add_argument("--version",action="version",version=f"RDTX VisualLab {__version__}")
    return parser


def main():
    args=build_parser().parse_args()
    if not 1<=args.port<=65535: raise SystemExit("--port must be between 1 and 65535")
    app=create_app(); print(f"RDTX VisualLab: http://{args.host}:{args.port}")
    app.run(host=args.host,port=args.port,threaded=True,debug=False)


if __name__=="__main__": main()
