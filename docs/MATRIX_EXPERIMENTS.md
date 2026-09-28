# Matrix Experiments

Matrix Lab runs controlled sequential RDTX transfers using one input file, one random seed, and one base configuration.

Supported sweeps:

- Selective Repeat window size
- DATA loss percentage
- corruption percentage
- reordering percentage

Each matrix accepts between 2 and 8 values.

Recommended examples:

~~~text
Window:     1,4,8,16
DATA loss:  0,10,20,30
Corruption: 0,5,10,15
Reordering: 0,25,50,100
~~~

Sequential execution avoids experiments competing with one another for the same localhost resources. The generated report records throughput, retransmissions, drops, and integrity.

The report may identify the highest or lowest measured value within that matrix run, but it deliberately does not claim a universal best window or guaranteed performance law.
