# Viva Guide

## Is LAN mode still the same topic?

Yes. It is the same RDTX Selective Repeat protocol, but the sender and receiver run on different hosts connected through a LAN instead of localhost.

## How does VisualLab know the LAN file is correct?

The remote receiver sends FIN_ACK only after it has all expected chunks, reconstructs the file, checks its byte count, and verifies SHA-256. If those checks fail, normal completion does not occur.

## Why run matrix rows sequentially?

Sequential runs reduce interference between experiments and make parameter comparisons easier to reproduce. The file and seed remain fixed while one selected parameter changes.

## Does the generated report invent conclusions?

No. It reports measured configuration and metrics, then makes limited observations about that specific run. It explicitly warns that throughput depends on the machine, operating-system scheduling, network, and seed.

## What is the research contribution?

Not a new ARQ algorithm. The contribution is integrated observability and experimentation around a real reliable-UDP implementation: real transfer, impairment, live visualization, LAN execution, controlled matrices, and reportable results in one tool.
