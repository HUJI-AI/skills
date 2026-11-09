# When you are running on Moriah yourself

Read this if your own shell commands run on Moriah: on the login node
`moriah-gw`, or on a compute node inside a Slurm job (as cluster-side
assistants and agents started from an `srun` session do). The person has
already registered and logged in, so the Register, Connect and access sections
of the skill don't apply unless they ask.

## Find out where you are

Don't guess from the hostname alone. Check it together with Slurm's variables:

```bash
hostname; echo "job=${SLURM_JOB_ID:-none} partition=${SLURM_JOB_PARTITION:-none} nodes=${SLURM_NODELIST:-none}"
```

- **On a compute node inside a job** (`SLURM_JOB_ID` set, host such as
  `glacier-27`): you are using an allocation the lab is paying for, with the
  CPUs, memory and time it was given. Modules are available.
- **On the login node** (`moriah-gw`, no job): run nothing heavy here,
  including installs, compiling, large copies and module work. Modules are not
  available on the login node.

A `SLURM_JOB_ID` can be left over from a job that has already ended. If it
matters, confirm the job is still running: `squeue -h -j "$SLURM_JOB_ID" -t RUNNING`.

## Use what is already allocated

- Inside a job, do the work in place. Don't start a second allocation for
  something the current one can do; that doubles the bill and counts against
  the lab's limits.
- If the work needs more than the current job has (a GPU, much more memory,
  many hours), say so and propose a separate `sbatch` job with its resources
  and estimated cost. Wait for the person's OK, as with any submission.
- Don't leave background processes running after the conversation ends
  without telling the person.

## Discover the live cluster directly

You don't need SSH. Run the snapshot script from this skill's folder:

```bash
bash scripts/moriah-snapshot.sh          # public cluster facts
bash scripts/moriah-snapshot.sh --me     # plus the person's own account, limits, storage
```

The login-banner notices it reports are shown on `moriah-gw`, so a compute
node may print none. The `--me` part is private; keep it in the conversation.
`sinfo`, `squeue --me`, `slimits`, `sshare -U`, `seff` and `sacct` work on
compute nodes too.

In a non-interactive shell (an agent's command tool), `module` may be
undefined. Run `. /etc/profile.d/huji-lmod.sh` in the same command before
`module avail` or `module load`.

## The person's files

- **Look before you answer.** If you can read the person's files, read the
  real file, folder or log (`ls`, `cat`, `grep -r`, `find`, `du`) instead of
  guessing from names or memory. If a path you expect is missing or
  unreadable, say so plainly; don't invent its contents.
- **Their folders** are usually their home (`echo $HOME`) and
  `/sci/<tier>/<pi>/<username>/` for each lab they belong to. Their labs are
  their Slurm accounts:
  `sacctmgr -n -P show assoc user=$USER format=Account`.
- **Don't change files on your own.** Creating, editing, moving, renaming or
  deleting the person's files and lab data needs their go-ahead for that
  specific change. Describe the change, or show the command, and let them
  decide. Lab folders are shared, and `nosnap` has no undo.
- **Results:** write outputs to the lab folder, not `/tmp`, and give the
  exact path.

## Network

Compute nodes can reach the web, including the HURCS wiki, so
`bash scripts/hurcs-wiki.sh` works from a job. Large downloads and installs
belong in a job, not on the login node.
