#!/usr/bin/env python

import sys
import time
from subprocess import check_output

# ------------------------------------------------------------------------------

# Use argparse if this gets any more complicated
if len(sys.argv) != 3:
    print('python lxc-stress <container name> <target time>')
    exit(0)

CONTAINER_NAME = sys.argv[1]

try:
    TARGET_TIME = float(sys.argv[2])
except TypeError:
    print('<target time> must be a valid float')
    print('')
    print('python lxc-stress <container name> <target time>')
    exit(1)

MAX_NUM_RUNS = 20

calc_pie = 'sum(1/16**k * (4/(8*k+1) - 2/(8*k+4) - 1/(8*k+5) - 1/(8*k+6)) for k in xrange({}))'

# ------------------------------------------------------------------------------

def stress_container_cpu(num_passes=20000):
    start_time = time.time()
    check_output([
        'lxc-attach',
         '-n', CONTAINER_NAME,
          '--', 'python', '-c', calc_pie.format(num_passes)
    ])
    end_time = time.time()
    return end_time - start_time

def set_cgroup_quota(quota=500000):
    check_output(['lxc-cgroup', '-n', CONTAINER_NAME, 'cpu.cfs_quota_us', str(quota)])

# ------------------------------------------------------------------------------

# Ensure the container has been started
check_output(['lxc-start', '--quiet', '-n', CONTAINER_NAME])
# Tell cgroups we want to limit CPU usage per second
check_output(['lxc-cgroup', '-n', CONTAINER_NAME, 'cpu.cfs_period_us', '1000000'])

cur_quota = 500000  # Middle of current cpu.cfs_period_us
cur_quota_delta = 250000  # Middle of cur_quota
margin_of_error = 0.5  # Accept run times +/- this amount
match_found = False

print('\nTarget run time: {}'.format(TARGET_TIME))

for __ in xrange(0, MAX_NUM_RUNS):
    set_cgroup_quota(cur_quota)
    run_time = stress_container_cpu()

    print('')
    print('Current run time: {}'.format(run_time))
    print('Current quota: {}'.format(cur_quota))

    if run_time < TARGET_TIME - margin_of_error:
        cur_quota = cur_quota - cur_quota_delta
    elif run_time > TARGET_TIME + margin_of_error:
        cur_quota = cur_quota + cur_quota_delta
    else: # Found match
        print('')
        print('-----------------------------------')
        print('Final run time: {}'.format(run_time))
        print('Final quota: {}'.format(cur_quota))
        print('-----------------------------------')
        print('')
        match_found = True
        break

    cur_quota_delta = int(cur_quota_delta / 2.0)

if not match_found:
    print('No match found')
