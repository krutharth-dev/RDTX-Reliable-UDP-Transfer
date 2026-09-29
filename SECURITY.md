# Security and Deployment Notes

RDTX VisualLab is an **educational local-first application**, not a hardened internet-facing service.

## Default web exposure

`rdtx-web` binds to:

~~~text
127.0.0.1:5000
~~~

by default. This means the dashboard is accessible only from the same machine.

Do not expose the development server to the public internet.

## Binding the web UI to another interface

The launcher supports `--host`, but binding the Flask development server to `0.0.0.0` exposes the dashboard to other devices that can reach the machine. The app does not implement user accounts, authentication, authorization, TLS termination, or production web-server hardening.

For the mini-project, keep the web UI on localhost.

## LAN receiver exposure

Two-host mode intentionally starts the **UDP receiver** with:

~~~bash
rdtx receive --host 0.0.0.0 --port 9000
~~~

This exposes the selected UDP port to reachable peers. Use it only on a trusted/private classroom or personal network and stop the receiver after the experiment.

## Uploaded files

Uploaded and reconstructed experiment files are stored under the local ignored `visual_lab_data/` directory. Do not use sensitive or confidential files for demonstrations.

## Protocol security

RDTX demonstrates reliability, not secure transport. It does not provide:

- encryption;
- authentication;
- peer identity verification;
- confidentiality;
- congestion control;
- resistance to hostile network traffic.

Use non-sensitive demo data only.
