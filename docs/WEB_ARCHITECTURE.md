# RDTX VisualLab Web Architecture

## 1. Design principle

The web application is an **observability and experiment-control layer**. It does not implement the transport protocol in JavaScript.

~~~text
Browser
  |
  | HTTP + Server-Sent Events
  v
Flask VisualLab
  |
  | launches / observes
  v
RDTX Sender ======== real UDP datagrams ========> RDTX Receiver
  |                                                   |
Selective Repeat                                 seq buffer
per-packet timers                                CRC32 / duplicates
  |                                                   |
  +------------ structured live events ---------------+
                                                      |
                                                   SHA-256
                                                      |
                                                reconstructed file
~~~

## 2. Backend responsibilities

### Flask application

- validates experiment parameters;
- enforces a 32 MiB upload limit by default;
- exposes health, run, event, download, JSON export, history, and CSV endpoints;
- adds basic browser security headers;
- starts only a bounded number of concurrent experiments.

### RunManager

Each experiment receives:
- a unique run ID;
- a dedicated working directory;
- an automatically selected localhost UDP port;
- one RDTX receiver thread;
- one RDTX sender;
- a live event journal;
- a persisted SQLite record.

### Event stream

Protocol trace events are enriched with:
- event kind;
- sender/receiver side;
- sequence number when present;
- sender-window base/range when present;
- timestamp.

The browser receives these events through Server-Sent Events (SSE).

## 3. Front-end responsibilities

The browser:
- selects files and experiment parameters;
- applies scenario presets;
- renders sender-window movement;
- filters protocol events;
- shows live counters;
- compares completed experiments;
- opens historical runs;
- downloads reconstructed output;
- exports JSON/CSV evidence.

No packet reliability logic exists in the browser.

## 4. Persistence

SQLite stores experiment metadata and final results. File bytes remain under `visual_lab_data/runs/<run_id>/`, which is ignored by Git.

The download endpoint validates that the output path belongs to the requested run directory before serving it.

## 5. Local-first scope

The development server binds to `127.0.0.1` by default. This is intentional for a classroom mini-project. Binding to another interface is possible with `rdtx-web --host`, but the app is not positioned as an internet-facing production service.

## 6. Professional boundaries

The project deliberately avoids:
- browser-simulated fake transfers;
- unnecessary front-end frameworks;
- cloud accounts;
- external databases;
- production claims.

This keeps the system reproducible on one laptop and preserves the Computer Networks concepts as the core.
