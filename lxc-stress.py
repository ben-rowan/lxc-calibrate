#!/usr/bin/env python

import time

NUM_RUNS = 10


def stress_cpu(num_passes=20000):
    sum(1 / 16 ** k *
        (4 / (8 * k + 1) -
         2 / (8 * k + 4) -
         1 / (8 * k + 5) -
         1 / (8 * k + 6)) for k in xrange(num_passes))


start_time = time.time()

for i in xrange(0, NUM_RUNS):
    print('Running stress test {}/{}'.format(i + 1, NUM_RUNS))
    stress_cpu()

end_time = time.time()
delta_time = end_time - start_time
avg_time = delta_time / float(NUM_RUNS)

print('Average run time (s): {}'.format(avg_time))
