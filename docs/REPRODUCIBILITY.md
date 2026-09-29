# Experimental Reproducibility

RDTX VisualLab is designed so that classroom demonstrations can be repeated and compared without presenting local measurements as universal networking results.

## Fixed variables

When comparing two configurations, keep these unchanged unless they are the variable under study:

- input file and file contents;
- chunk size;
- retransmission timeout;
- random seed;
- receiver ACK impairment;
- machine/network topology.

Matrix Lab automatically keeps the file, seed, and non-swept parameters constant across rows.

## Random seed

Loss, corruption, delay, and reordering simulation use deterministic pseudo-random behavior when a seed is provided.

A fixed seed helps reproduce the same impairment pattern. Changing the seed is useful when testing whether an observation is robust across different loss/corruption patterns.

## Suggested experiment groups

### Window-size study

~~~text
Window: 1,4,8,16
DATA loss: 10%
Seed: 2026
~~~

### DATA-loss study

~~~text
DATA loss: 0,10,20,30%
Window: 8
Seed: 2026
~~~

### Reordering study

~~~text
Reordering: 0,25,50,100%
Window: 8
Seed: 2026
~~~

## What to record

For every run, record:

- file size;
- window/chunk/RTO settings;
- impairment settings;
- seed;
- elapsed time;
- throughput;
- retransmissions;
- simulated drops/corruptions;
- reordered pairs;
- duplicates/checksum errors when available;
- final integrity status.

Use the built-in JSON, CSV, and Markdown exports rather than copying values manually when possible.

## Interpreting results

Do not claim that a window size or impairment setting is universally "best" based on a localhost or single-LAN measurement.

Timing can be affected by:

- operating-system scheduling;
- CPU load;
- Python runtime overhead;
- wireless conditions;
- firewall/network behavior;
- timer resolution;
- random impairment pattern.

A correct report should say **"in this measured experiment"** and preserve the configuration alongside the result.

## Minimum evidence set

For a compact mini-project report, a useful minimum is:

1. one baseline run;
2. one DATA-loss run;
3. one combined DATA/ACK-loss run;
4. one corruption run;
5. one reordering run;
6. one window-size matrix;
7. one two-host LAN transfer if a second laptop is available.
