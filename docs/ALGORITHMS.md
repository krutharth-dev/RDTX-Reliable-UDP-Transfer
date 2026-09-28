# RDTX Algorithms

This document gives report-friendly pseudocode for the core RDTX logic.

## Sender — Selective Repeat

~~~text
INPUT: file, window size W, timeout RTO

read file
split file into numbered chunks 0..N-1
calculate SHA-256

send HELLO until HELLO_ACK arrives

base <- 0
next_seq <- 0

while not all N packets acknowledged:

    while next_seq < N AND next_seq < base + W:
        create DATA(next_seq)
        send packet
        start/restart its timer
        next_seq <- next_seq + 1

    if ACK(n) arrives from the configured receiver:
        mark n acknowledged
        remove n from outstanding retransmission set

        while base is acknowledged:
            base <- base + 1

    for each outstanding packet n:
        if timer(n) expired:
            retransmit only DATA(n)
            restart timer(n)

send FIN until FIN_ACK arrives
~~~

The key Selective Repeat rule is that later ACKs may be remembered, but they do not permit the sender to slide past a missing base packet.

## Receiver

~~~text
wait for HELLO
validate filename, size, chunk size, chunk count, window and SHA-256
send HELLO_ACK

while transfer is active:
    receive UDP datagram

    if CRC32 is invalid:
        discard

    if DATA(n):
        verify session, peer, sequence range and expected chunk length

        if n is new:
            buffer payload at sequence n

        send ACK(n) even when n is a duplicate

    if FIN:
        verify FIN metadata
        require every sequence 0..N-1
        reassemble chunks in sequence order
        verify byte count and SHA-256
        write file
        send FIN_ACK
        linger briefly to re-ACK duplicate FIN packets
~~~

## Complexity

For a file split into N chunks:

- Packet construction/reassembly is O(N) excluding payload-copy cost.
- ACK lookup and in-flight packet lookup use hash-based structures with expected O(1) operations.
- Receiver memory is O(file size) because the educational implementation buffers all chunks.
- Sender retransmission scanning is O(W) per loop iteration, where W is the configured window size.

## Why not Go-Back-N?

If DATA(4) is lost but DATA(5) and DATA(6) arrive, the receiver retains and ACKs 5 and 6. The sender retransmits only 4. Go-Back-N would normally retransmit 4 and subsequent unacknowledged packets.
