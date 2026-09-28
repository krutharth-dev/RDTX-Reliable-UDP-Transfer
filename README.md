# RDTX VisualLab 2.2

**RDTX VisualLab: Web-Based Reliable File Transfer and Selective Repeat Analysis over Unreliable UDP**

RDTX VisualLab is a Computer Networks experimentation app built around a real Selective Repeat file-transfer protocol over UDP.

## Version 2.2 highlights

### Two-host LAN mode

Run the receiver on Laptop B:

~~~bash
rdtx receive --host 0.0.0.0 --port 9000 --output-dir received --trace
~~~

On Laptop A, start VisualLab, choose **LAN / two-host**, enter Laptop B's LAN IPv4 address and port, then send the file.

Successful LAN completion means Laptop B returned FIN_ACK only after its final size and SHA-256 checks passed.

### Automatic experiment reports

Every completed run provides a **Generate report** action. The Markdown report contains configuration, measured metrics, and cautious observations suitable for a Results and Analysis section.

### Matrix Lab

Use one file and base configuration to sweep:

- window size: 1,4,8,16
- DATA loss: 0,10,20,30
- corruption: 0,5,10,15
- reordering: 0,25,50,100

Each row is a real sequential localhost UDP transfer. A matrix report is generated after completion.

## macOS setup

~~~bash
git pull origin main
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
rdtx-web
~~~

Open:

~~~text
http://127.0.0.1:5000
~~~

## Verification

~~~bash
make test
make verify
~~~

Documentation:

- LAN mode: docs/LAN_MODE.md
- Matrix experiments: docs/MATRIX_EXPERIMENTS.md
- Research gap: docs/RESEARCH_GAP.md
- Web architecture: docs/WEB_ARCHITECTURE.md
- Mini-project report: docs/MINI_PROJECT_REPORT.md
- Demo guide: docs/DEMO_GUIDE.md
- Viva guide: docs/VIVA_GUIDE.md
