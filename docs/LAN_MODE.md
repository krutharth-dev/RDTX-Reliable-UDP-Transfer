# LAN / Two-Host Mode

LAN mode runs the RDTX sender on the VisualLab laptop and the RDTX receiver on a second machine.

~~~text
Laptop A                                      Laptop B
VisualLab -> RDTX Sender ==== Wi-Fi/LAN ==== RDTX Receiver -> file
                UDP DATA              UDP ACK / FIN_ACK
~~~

On Laptop B:

~~~bash
rdtx receive --host 0.0.0.0 --port 9000 --output-dir received --trace
~~~

On macOS, a common command for the Wi-Fi IPv4 address is:

~~~bash
ipconfig getifaddr en0
~~~

Enter that address in VisualLab on Laptop A.

Sender-side DATA loss, corruption, delay, and reordering are applied on Laptop A. ACK-side impairment must be applied on Laptop B; VisualLab generates the matching receiver command.

Successful completion is meaningful even though Laptop A cannot directly read Laptop B's output file: the receiver sends FIN_ACK only after validating final byte count and SHA-256.

If macOS asks whether Python may accept incoming connections, allow it on the private or local network. Use the same UDP port on both laptops.
