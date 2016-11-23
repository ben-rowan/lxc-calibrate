#!/usr/bin/env python

import sys
import time
import argparse
from subprocess import check_output
from subprocess import CalledProcessError

# ------------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument(
    'container_name',
    help='The name of the container you wish to calibrate.',
    type=str
)
parser.add_argument(
    'target_time',
    help='The target run time to calibrate the container with (float).',
    type=float
)
parser.add_argument(
    '--max_num_runs', '-m',
    help='Set the maximum number of times the search algorithm will run.',
    default=20,
    type=int
)
parser.add_argument(
    '--cfs_period', '-p',
    help='Set the cgroups cpu.cfs_period_us',
    default=1000000,  # 1 sec
    type=int
)
parser.add_argument(
    '--margin_of_error', '-e',
    help='Accept run times +/- this amount (seconds)',
    default=0.5,
    type=float
)

args = parser.parse_args()

CONTAINER_NAME = args.container_name
TARGET_TIME = args.target_time
MAX_NUM_RUNS = args.max_num_runs
CFS_PERIOD = args.cfs_period
MARGIN_OF_ERROR = args.margin_of_error

CALC_PIE = 'sum(1/16**k * (4/(8*k+1) - 2/(8*k+4) - 1/(8*k+5) - 1/(8*k+6)) for k in xrange({}))'

# ------------------------------------------------------------------------------

def stress_container_cpu(num_passes=20000):
    start_time = time.time()
    check_output([
        'lxc-attach',
         '-n', CONTAINER_NAME,
          '--', 'python', '-c', CALC_PIE.format(num_passes)
    ])
    end_time = time.time()
    return end_time - start_time

def set_cgroup_quota(quota=500000):
    check_output(['lxc-cgroup', '-n', CONTAINER_NAME, 'cpu.cfs_quota_us', str(quota)])

def halve(n):
    return int(n / 2.0)

# ------------------------------------------------------------------------------

try:
    # Ensure container has been started
    check_output(['lxc-start', '--quiet', '-n', CONTAINER_NAME])
except CalledProcessError:
    print('Failed to start container \'{}\''.format(CONTAINER_NAME))
    exit(1)

try:
    # Tell cgroups how we want to limit CPU usage (default is per second)
    check_output(['lxc-cgroup', '-n', CONTAINER_NAME, 'cpu.cfs_period_us', str(CFS_PERIOD)])
except CalledProcessError:
    print('Unable to set a cpu.cfs_period_us of \'{}\''.format(CFS_PERIOD))
    exit(1)

cur_cfs_quota = halve(CFS_PERIOD)  # Middle of current cpu.cfs_period_us
cur_cfs_quota_delta = halve(cur_cfs_quota)  # Middle of cur_cfs_quota
match_found = False

print('\nTarget run time: {}'.format(TARGET_TIME))

for __ in xrange(0, MAX_NUM_RUNS):
    set_cgroup_quota(cur_cfs_quota)
    run_time = stress_container_cpu()

    print('')
    print('Current run time: {}'.format(run_time))
    print('Current quota: {}'.format(cur_cfs_quota))

    if run_time < TARGET_TIME - MARGIN_OF_ERROR:
        cur_cfs_quota = cur_cfs_quota - cur_cfs_quota_delta
    elif run_time > TARGET_TIME + MARGIN_OF_ERROR:
        cur_cfs_quota = cur_cfs_quota + cur_cfs_quota_delta
    else: # Found match
        print('')
        print('-----------------------------------')
        print('Final run time: {}'.format(run_time))
        print('Final quota: {}'.format(cur_cfs_quota))
        print('-----------------------------------')
        print('')
        match_found = True
        break

    cur_cfs_quota_delta = halve(cur_cfs_quota_delta)

if not match_found:
    print('No match found')
