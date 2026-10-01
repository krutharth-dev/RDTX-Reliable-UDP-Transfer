# RDTX VisualLab — 45-second showcase

This repo includes an [animated concept preview](media/rdtx-45s-explainer.svg) that explains the real protocol's features. **It is illustrative, not captured network traffic, a measured benchmark, or proof that a particular impaired run succeeded.** For a genuine demonstration, record the local dashboard following the steps below.

## 45-second recording shot list

| Time | Actual screen and action | Suggested caption / narration |
| :-- | :-- | :-- |
| 00–06 s | Open the local VisualLab dashboard. Show the **REAL UDP** telemetry label. | “Reliable UDP transfer, made observable.” |
| 06–12 s | Select **Local lab**, choose your file and click **Baseline**. | “A Python sender and receiver run under the web dashboard.” |
| 12–19 s | Click **Run UDP experiment**. Show window progression and event timeline. | “Selective Repeat tracks packets and individual ACKs.” |
| 19–27 s | Select **Lossy link** (DATA 20%, ACK 10%, window 8, seed 2026) and run again. | “Controlled impairment lets us investigate recovery.” |
| 27–34 s | Choose the timeline **Drop** and **Retry** filters, and show the real events generated in your run. | “Per-packet timers retry missing DATA.” |
| 34–40 s | Show the completed run's actual **END-TO-END INTEGRITY** result, if it completes. | “Final size and SHA-256 are checked before FIN_ACK.” |
| 40–45 s | Show **Export JSON** and **Generate report**, then your repository URL. | “Repeat the experiment and export the evidence.” |

**Do not edit in a PASS label or fabricated retransmission/throughput counters.** Display whatever the recorded run actually reports. If it fails, say so, troubleshoot, and record a new run instead.

## Reproduce the dashboard locally

On macOS/Linux, from the repo root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
make demo-check
rdtx-web
```

Then visit `http://127.0.0.1:5000`. The provided `demo.txt` can work for a baseline. For a longer timeline with 16 chunks (1024 bytes each), generate deterministic *local demo input* without committing it:

```bash
python3 -c "from pathlib import Path; Path('demo-video.bin').write_bytes(bytes(range(256)) * 64)"
```

Upload `demo-video.bin`; choose **Baseline** first, then **Lossy link**. The loss preset documented in `webapp/static/app.js` uses DATA loss 20%, ACK loss 10%, window 8 and RTO 350 ms. Confirm the seed field is 2026. A fixed seed makes controlled experiments easier to repeat, but does not guarantee every run's exact timing.

## Record, edit and publish

Use macOS **Shift + Command + 5**, OBS, or another screen recorder at a readable resolution. Trim to approximately 45 seconds, add captions, and obscure private local file paths or network addresses. Record the *real* dashboard and use its actual trace/results. Upload the MP4 to a GitHub release or suitable video host, then replace the illustrated preview with a link to that recording.

[Full demo guide](DEMO_GUIDE.md) · [Protocol specification](PROTOCOL.md) · [Reproducibility notes](REPRODUCIBILITY.md).
