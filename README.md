# sgrep
could be described as "pgrep for Slurm"

Slurm's `squeue` command is useful, but lacks some features I always missed, for example simply searching jobs by name.
That's why I wrote this little script. It is similar to `pgrep` in the sense that it outputs the Slurm job IDs of matching jobs line by line, by default. 
It is also capable of outputting any number of fields of a Slurm job by supplying a format string.

Jobs can be filtered by
  * regex of the job name
  * user
  * partition
  * job state
  * runtime

and any combination of the above.

## Prerequisites

  * Python 3
  * PySlurm (`pip install --user pyslurm`)

## Usage

```
usage: sgrep [-h] [-u USER] [-U] [-p PARTITION] [-t RUNTIME] [-r] [-w] [-l]
             [-c] [-f FORMAT] [-A]
             [expr]

like pgrep, but for slurm jobs. without any arguments, prints job IDs of all
running or queued jobs of all users

positional arguments:
  expr                  regex to match the job names against

optional arguments:
  -h, --help            show this help message and exit
  -u USER, --user USER  only show jobs of specified user
  -U, --current-user    only show jobs of current user
  -p PARTITION, --partition PARTITION
                        only show jobs on specified partition
  -t RUNTIME, --runtime RUNTIME
                        only show jobs with a specified runtime in minutes.
                        format is similar to cut, eg 5-10, -3 (equal to 3), 1-
                        are all valid ranges (and show jobs running for 5-10
                        min, <= 3 min and >= 1 min, respectively)
  -r, --running         only show running jobs
  -w, --pending         only show pending jobs
  -l, --list            print extended job information, see -f/--format
  -c, --count           print a count of results instead
  -f FORMAT, --format FORMAT
                        format string to use for -l/--list, see
                        -A/--available-fields, default: "job_id name"
  -A, --available-fields
                        print a list of fields that can be specified in
                        -f/--format
```

## Tips

### Filtering by runtime

Runtime filtering is pretty useful I think, as this is sometimes the only clear discriminator of some group of jobs versus another.
For example, the following command will display the executing user's jobs with a runtime <= 5 minutes:

`sgrep -Ut -5`

### Changing partitions

Another usecase is further processing of the output using `xargs`. For example, I often use this to change the partitions of submitted jobs:

`sgrep -Uwp c0 | xargs -I {} scontrol update jobid={} partition=c1`

This will move all jobs of the executing user pending on partition c0 to partition c1.

### Canceling jobs

Cancel all jobs on partition c0 matching the regex "^long_job_no_\d+$":

`sgrep -p c0 "^long_job_no_\d+$" | xargs scancel`

I suggest you play around with the options. You will discover your personal favourites. 
For example, you could build a custom output format as your personal replacement for `squeue`.
