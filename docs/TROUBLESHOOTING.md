# Troubleshooting

Use this page during setup and keep it available during the final demo.

## rdtx or rdtx-web: command not found

Activate the virtual environment and reinstall the project:

~~~bash
source .venv/bin/activate
python3 -m pip install -e .
rdtx --version
~~~

## Port 5000 is already in use

Start the web dashboard on another port:

~~~bash
rdtx-web --port 5050
~~~

Then open:

~~~text
http://127.0.0.1:5050
~~~

## UDP receiver port is already in use

Stop the old receiver with Ctrl+C or choose another port on both sender and receiver, for example 9100.

## LAN sender cannot reach the receiver

Check:

1. both laptops are on the same LAN/Wi-Fi;
2. the receiver is running before the sender starts;
3. the receiver uses `--host 0.0.0.0`;
4. both sides use the same UDP port;
5. the sender is using the receiver laptop's LAN IPv4 address;
6. the receiver firewall allows Python/UDP traffic on the local network.

On macOS, a common Wi-Fi IPv4 command is:

~~~bash
ipconfig getifaddr en0
~~~

Some institutional/guest Wi-Fi networks isolate clients. If peer-to-peer traffic is blocked, use a personal hotspot or demonstrate localhost mode.

## Matrix run takes too long

Use a small file and moderate impairment values. Recommended classroom matrix:

~~~text
Window size: 1,4,8,16
~~~

Avoid extreme loss combined with very short timeouts during a live evaluation.

## Browser shows old UI after git pull

Stop the web process, reinstall editable mode, restart, and hard-refresh the browser:

~~~bash
source .venv/bin/activate
python3 -m pip install -e .
rdtx-web
~~~

## Generated experiment history is confusing

The local SQLite/history data lives under `visual_lab_data/`.

To start with a clean local demo state:

~~~bash
rm -rf visual_lab_data
~~~

This does not change source code.

## Final fallback

If LAN networking is blocked, switch to **Local lab**. The localhost path still uses real UDP sockets and exercises the same Selective Repeat implementation.
