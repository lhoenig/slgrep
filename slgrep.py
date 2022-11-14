#!/usr/bin/env python3

__author__ = "Lukas Hoenig"

if __name__ == '__main__':

    from pyslurm import job
    from sys import stderr
    from os import getuid
    import pwd
    import argparse
    import re

    parser = argparse.ArgumentParser(description='like pgrep, but for slurm jobs. without any arguments, prints job IDs of all running or queued jobs of all users')
    parser.add_argument('expr', metavar='expr', type=str, nargs='?',
                        help='regex to match the job names against')
    parser.add_argument('-u', '--user', dest='user', default=None, type=str,
                        help='only show jobs of specified user')
    parser.add_argument('-U', '--current-user', dest='current_user', action='store_true',
                        help='only show jobs of current user')
    parser.add_argument('-p', '--partition', dest='partition', default=None, type=str,
                        help='only show jobs on specified partition')
    parser.add_argument('-t', '--runtime', dest='runtime', default=None, type=str,
                        help='only show jobs with a specified runtime in minutes. format is similar to cut, eg 5-10, -3 (equal to 3), 1- are all valid ranges (and show jobs running for 5-10 min, <= 3 min and >= 1 min, respectively)')
    parser.add_argument('-r', '--running', dest='running', action='store_true',
                        help='only show running jobs')
    parser.add_argument('-w', '--pending', dest='pending', action='store_true',
                        help='only show pending jobs')
    parser.add_argument('-l', '--list', dest='list', action='store_true',
                        help='print extended job information, see -f/--format')
    parser.add_argument('-c', '--count', dest='count', action='store_true',
                        help='print a count of results instead')
    parser.add_argument('-f', '--format', dest='format', default='job_id name',
                        help='format string to use for -l/--list, see -A/--available-fields, default: "job_id name"')
    parser.add_argument('-A', '--available-fields', dest='available_fields', action='store_true',
                        help='print a list of fields that can be specified in -f/--format')
    args = parser.parse_args()

    fields = ['account', 'accrue_time', 'admin_comment', 'alloc_node', 'alloc_sid', 'array_job_id', 'array_task_id', 'array_task_str', 
        'array_max_tasks', 'assoc_id', 'batch_flag', 'batch_features', 'batch_host', 'billable_tres', 'bitflags', 'boards_per_node', 'burst_buffer', 
        'burst_buffer_state', 'command', 'comment', 'contiguous', 'core_spec', 'cores_per_socket', 'cpus_per_task', 'cpus_per_tres', 'cpu_freq_gov', 'cpu_freq_max', 'cpu_freq_min', 
        'dependency', 'derived_ec', 'eligible_time', 'end_time', 'exc_nodes', 'exit_code', 'features', 'group_id', 'job_id', 'job_state', 'last_sched_eval', 'licenses', 'max_cpus', 'max_nodes', 
        'mem_per_tres', 'name', 'network', 'nodes', 'nice', 'ntasks_per_core', 'ntasks_per_core_str', 'ntasks_per_node', 'ntasks_per_socket', 'ntasks_per_socket_str', 'ntasks_per_board', 'num_cpus', 
        'num_nodes', 'partition', 'mem_per_cpu', 'min_memory_cpu', 'mem_per_node', 'min_memory_node', 'pn_min_memory', 'pn_min_cpus', 'pn_min_tmp_disk', 'power_flags', 'preempt_time', 'priority', 
        'profile', 'qos', 'reboot', 'req_nodes', 'req_switch', 'requeue', 'resize_time', 'restart_cnt', 'resv_name', 'run_time', 'run_time_str', 'sched_nodes', 'shared', 'show_flags', 
        'sockets_per_board', 'sockets_per_node', 'start_time', 'state_reason', 'std_err', 'std_in', 'std_out', 'submit_time', 'suspend_time', 'system_comment', 'time_limit', 'time_limit_str', 
        'time_min', 'threads_per_core', 'tres_alloc_str', 'tres_bind', 'tres_freq', 'tres_per_job', 'tres_per_node', 'tres_per_socket', 'tres_per_task', 'tres_req_str', 'user_id', 'wait4switch', 
        'wckey', 'work_dir', 'cpus_allocated', 'cpus_alloc_layout']

    if args.available_fields:
        print(', '.join(fields))
        exit(0)

    # parse format string
    fspl = args.format.split()
    fmt = args.format
    fmtl = []
    while len(fmt) > 0:
        m = re.search(r'^(\s+)', fmt)
        if m:
            fmtl.append((0, m.groups()[0]))
            fmt = fmt[len(m.groups()[0]):]
        m = re.search(r'^(\S+)', fmt)
        if m:
            # DECIDE if field is unknown the string could just be inserted
            if not m.groups()[0] in fields:
                print(f'unknown field: {m.groups()[0]}', file=stderr)
                exit(1)
            fmtl.append((1, m.groups()[0]))
            fmt = fmt[len(m.groups()[0]):]

    def jformat(jdict):
        fs = ''
        for (fld, s) in fmtl:
            if not fld:
                fs += s
            else:
                fs += str(jdict[s])
        return fs

    if args.user and args.current_user:
        print('only one of -u/--user and -U/--current-user may be specified', file=stderr)
        exit(1)

    if args.user:
        # filter based on user
        try:
            # docs are wrong: find_user needs the UID as int, not the username as str
            jobs = job().find_user(pwd.getpwnam(args.user).pw_uid)
        except KeyError:
            print('user not found', file=stderr)
            exit(1)
    elif args.current_user:
        jobs = job().find_user(getuid())
    else:
        jobs = job().get()

    if args.running and args.pending:
        print('only one of -r/--running and -w/--pending may be specified', file=stderr)
        exit(1)

    if args.pending and args.runtime:
        print('pending jobs always have zero runtime, looking for anything else makes no sense', file=stderr)
        exit(1)

    if args.runtime:
        match = re.search(r'^(\d+)?(-\d*)?$', args.runtime)
        if match:
            special_case = False
            if match.groups()[0]:
                if match.groups()[1]:
                    srange_min = int(match.groups()[0])
                else:
                    srange_min = 0
                    srange_max = int(match.groups()[0])
                    special_case = True
            else:
                srange_min = -1
            if match.groups()[1]:
                if match.groups()[1] == '-':
                    if not match.groups()[0]:
                        print('illegal range specified')
                        exit(1)
                    else:
                        srange_max = -1
                else:
                    srange_max = int(match.groups()[1][1:])
            elif not special_case:
                srange_max = -1
            if srange_min != -1 and srange_max != -1 and srange_min > srange_max:
                print('illegal range specified (min > max)', file=stderr)
                exit(1)
        else:
            print('illegal range specified', file=stderr)
            exit(1)

    expr = re.compile(args.expr) if args.expr else None

    c = 0

    for jnum, jdict in jobs.items():
        # TODO partition could also be a regex
        # filter based on partition
        if not args.partition or jdict['partition'] == args.partition:
            if args.runtime:
                rtime = int(jdict['run_time'])
                if srange_min != -1 and srange_max == -1:
                    rtime_min = srange_min * 60
                    rtime_max = rtime + 1
                elif srange_min != -1 and srange_max != -1:
                    rtime_min = srange_min * 60
                    rtime_max = srange_max * 60
                elif srange_min == -1 and srange_max != -1:
                    rtime_min = 0
                    rtime_max = srange_max * 60
            # filter based on runtime
            if not args.runtime or rtime_min <= rtime <= rtime_max:
                # filter based on job state
                if (not (args.running or args.pending) or \
                    (args.running and jdict['job_state'] == 'RUNNING') or \
                    (args.pending and jdict['job_state'] == 'PENDING')) and \
                    jdict['job_state'] != 'CANCELLED' and \
                    jdict['job_state'] != 'COMPLETED' and \
                    jdict['job_state'] != 'FAILED':
                    # filter based on name
                    if not args.expr or expr.match(jdict['name']):
                        if args.count:
                            c += 1
                        else:
                            if args.list:
                                try:
                                    print(jformat(jdict))
                                except BrokenPipeError:
                                    exit(0)
                            else:
                                try:
                                    print(jnum)
                                except BrokenPipeError:
                                    exit(0)   
    if args.count:
        print(c)
