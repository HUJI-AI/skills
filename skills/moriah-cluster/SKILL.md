---
name: moriah-cluster
description: >-
  Help a Hebrew University researcher get access to and use Moriah, the
  HURCS (Hebrew University Research Computing Services) Slurm cluster at
  moriah-gw.cs.huji.ac.il, whether the agent runs on the person's computer or
  on Moriah itself. Covers registering (PI account, username, OTP login),
  connecting over SSH (VPN, bava jump host, VS Code), the security trade-offs
  of giving an AI agent cluster access, reading the live HURCS wiki,
  discovering the live cluster and the user's own account, sbatch/srun jobs,
  GPUs (L4, L40S, H200), storage tiers and what the lab actually paid for,
  modules and Python environments, and estimating job cost. Use whenever the
  user mentions Moriah, HURCS, moriah-gw, the HUJI cluster, Slurm or sbatch at
  the Hebrew University, or wants to run heavy compute or GPU jobs at HUJI.
metadata:
  title: עבודה עם קלאסטר מוריה
  summary: הרשמה, התחברות ועבודה עם קלאסטר מוריה של HURCS, כולל GPU, אחסון ועלויות, ומה חשוב לדעת לפני שנותנים לסוכן AI גישה לקלאסטר.
  title_en: Working with the Moriah computing cluster
  summary_en: Registering, connecting to and working with HURCS's Moriah cluster, including GPUs, storage and costs, and what to know before giving an AI agent access to it.
  title_ar: العمل مع عنقود الحوسبة موريا
  summary_ar: التسجيل والاتصال والعمل مع عنقود الحوسبة موريا التابع لـ HURCS، بما في ذلك وحدات GPU والتخزين والتكاليف، وما يجب معرفته قبل منح وكيل ذكاء اصطناعي حق الوصول إليه.
  pillar: research
---
# Moriah, the HUJI research computing cluster

Moriah is the Slurm cluster of HURCS (Hebrew University Research Computing
Services), open to research groups across the university. Its documentation is
the HURCS wiki at <https://wiki.rcs.huji.ac.il/hurcs>. General CS Slurm
conventions are at <https://wiki.cs.huji.ac.il/wiki/Slurm>. When this skill and
the wiki disagree on a policy, the wiki wins. When either disagrees with the live
cluster on hardware or limits, the live cluster wins (see "Find out what is
there now").

Moriah is paid for by the lab. Every job and every terabyte of storage is
charged monthly to the PI's HURCS credit. Keep that in mind whenever you
suggest resources.

Assume the person is a researcher in any discipline, not an HPC specialist.
Start from their practical workflow, keep answers short, and state the
cluster assumptions that matter (partition, account, resources, cost, data
safety).

Start by finding where you and the person stand, then go to that section:

0. **You are running on Moriah yourself** (a shell on `moriah-gw` or on a
   compute node; check, don't guess, as in
   [references/on-cluster.md](references/on-cluster.md)): read that file
   first. Registering, connecting and the access options below are already
   behind the person; skip them unless asked.
1. No account yet: **Register**.
2. Has a username but cannot log in: **Connect**, then the troubleshooting
   notes there.
3. Can log in: **Decide how you will reach the cluster**, then **Find out
   what is there now**, then **Run work**.

## Register

Registration is done by people in web forms and by SMS. Explain the steps and
give the links; never fill in ID numbers, SMS codes or passwords yourself.

1. **The lab needs a HURCS account.** Ask whether their PI (lab head) already
   has one. If not, the PI fills the
   [New PI form](https://docs.google.com/forms/d/e/1FAIpQLSenA-KIHexxS8kGSc5ieIyYh6IK8DxlHxvs0AbXFbE2vKZXxA/viewform?usp=sf_link).
   The account is activated only after the lab transfers a minimum amount to
   HURCS ([funds transfer](https://wiki.rcs.huji.ac.il/hurcs/accounts/funds-transfer)).
   Setup takes up to 2 working days.
2. **The PI adds the person** with the
   [Add new group members form](https://docs.google.com/forms/d/e/1FAIpQLSd0-iOFSaPVmLDBJg0BX-UlvyMYaAxuXylJKmwR4BjMRCFtwA/viewform?usp=sf_link),
   also up to 2 working days. Someone who once had a CS username still needs
   this form, because old accounts are usually deactivated.
3. **Create a username and password** at
   <https://registrar.cs.huji.ac.il/account>: enter ID or passport number,
   accept the agreement, enter the SMS code from "HUJICSE", and choose a
   username (permanent) and password. If the SMS doesn't arrive, retry in a
   private (incognito) window.
4. **Set up the one-time password (OTP)** at
   <https://registrar.cs.huji.ac.il/hotp>. Choose "Time-Based hotp - google
   authenticator" and scan the QR code with Google Authenticator; the entry is
   called "CSE-HUJI (username)". A browser extension from
   <https://authenticator.cc/> or SMS codes also work.
   If codes are rejected, check the phone's clock first.
5. **Forgot password:** same registrar page, "Forgot Password"; a temporary
   password arrives by SMS.

Details: <https://wiki.rcs.huji.ac.il/hurcs/accounts/manage-accounts>,
<https://wiki.rcs.huji.ac.il/hurcs/user_management/create_username>,
<https://wiki.rcs.huji.ac.il/hurcs/user_management/otp>.

## Connect

The login node is `moriah-gw.cs.huji.ac.il`. Login asks first for the OTP,
then for the Unix password.

- **On campus (eduroam, university LAN) or on the HUJI VPN**
  ([Rumba](https://ca.huji.ac.il/Rumba)): `ssh <username>@moriah-gw.cs.huji.ac.il`
- **Anywhere else**, through the jump host:
  `ssh -J <username>@bava.cs.huji.ac.il <username>@moriah-gw.cs.huji.ac.il`

The recommended `~/.ssh/config` from the HURCS wiki:

```
Host *
    ServerAliveInterval 180
    ServerAliveCountMax 2

Host hurcs-proxy
    HostName bava.cs.huji.ac.il
    User <username>

Host moriah
    HostName moriah-gw.cs.huji.ac.il
    User <username>
    ProxyJump hurcs-proxy    # remove this line when on campus or VPN
```

Then `ssh moriah`. Windows users can use MobaXterm
([guide](https://wiki.rcs.huji.ac.il/en/hurcs/guides/MobaXterm)) or WSL. For
graphical programs add `-X` (macOS needs XQuartz). For VS Code Remote-SSH follow
<https://wiki.rcs.huji.ac.il/en/hurcs/guides/vscode-remote>. It connects to an
allocated compute node rather than the login node, and it sets
`remote.SSH.serverInstallPath` to the lab folder so the VS Code server does not
fill the 5 GB home.

Troubleshooting: the most common cause of failed or strange logins is a full
home folder (5 GB), usually from `pip install` without a virtual
environment. If the connection just hangs, check VPN versus jump host first.

## Decide how you will reach the cluster

If you are an agent on the person's own computer, you cannot type the OTP, so
by default you cannot run commands on Moriah yourself. Before setting anything
up, read [references/access-and-agents.md](references/access-and-agents.md)
and walk the person through its three options:

1. they run the commands and paste output back;
2. a shared SSH connection that they open with two-factor login and that
   closes once unused (recommended);
3. a dedicated SSH key.

An SSH key is a standing credential: every agent and program on their
computer that can use it gets their full access to their files, the lab's
shared data and the lab's budget, without them being there. Make sure they
understand this before they choose a key, and never create or install one
without their explicit consent.

## Check the HURCS wiki

The wiki is the authoritative, always-current reference; everything written
here is a snapshot of it. Look something up when a cluster fact will change
what the person does: before stating a specific quota, price, path, partition,
policy, module or command they will act on, or when they ask about something
this skill doesn't cover. Don't look things up for general coding help or for
facts that are settled here and don't matter to the decision.

Read it with the bundled script, which needs only `bash` and `curl`:

```
bash scripts/hurcs-wiki.sh search <term>     # find pages by path/title, e.g. quota
bash scripts/hurcs-wiki.sh read <page-path>  # print one page as text
bash scripts/hurcs-wiki.sh list              # every page, if search is too narrow
```

Find the page path with `search` before reading, rather than guessing it.
Prices and quotas are on `hurcs/accounts/quota-management`; storage types and
services on `hurcs/accounts/storage-costs`.

Don't rely on a generic web-fetch or web-search tool for the wiki. It is a
Wiki.js (JavaScript) site, so a plain fetch returns only an empty page shell
or titles, and a search engine returns a stale copy. The script reads the
page's own text. If you catch yourself answering a cluster question from an empty fetch or from
memory, use the script instead.

When an answer comes from the wiki, say so briefly ("per the HURCS wiki"). If
the lookup fails, answer from this skill, say the detail may be out of date,
and don't block the answer on it.

## Find out what is there now

Hardware, limits and notices change: nodes go down, GPUs are added, upgrades
are announced. A dated snapshot is in
[references/cluster-snapshot.md](references/cluster-snapshot.md). Use it only
when you cannot reach the cluster, and say how old it is.

When you can reach the cluster, run the read-only script from this skill's
folder. From the person's computer:

```
ssh moriah 'bash -s -- --me' < scripts/moriah-snapshot.sh
```

From a shell on Moriah itself (login or compute node), run it directly:
`bash scripts/moriah-snapshot.sh --me`.

It prints node types and how many are up, partitions and GPU types. With
`--me` it adds private details: login notices (maintenance, OS upgrades),
software versions, scheduler settings, reservations
(including maintenance windows), queue load, and the person's own lab
account, limits, fairshare and storage folders. The `--me` part is private:
don't publish it or paste it anywhere shared.

If the person agrees, record what you learned where you will find it next
time, such as their project's `AGENTS.md` or `CLAUDE.md`. Record only
non-secret facts:

```
## Moriah
- Username: <username>; Slurm account (lab): <account>
- Lab folder: /sci/labs/<account>/<username>
- Python environment: /sci/labs/<account>/<username>/envs/<name>
- Access method: <person runs commands | shared connection | SSH key | agent runs on Moriah>
- Usual resources: <e.g. 1 x L40S, 8 CPUs, 64G, 12h>
```

Useful read-only commands (login node or compute node): `sinfo -s`, `ssinfo`
(per-node load and GPUs), `slimits` (your and your lab's limits), `sshare -U`
(fairshare), `squeue --me`, `sacct`, `seff <jobid>`. Some commands, such as
`susage` and `squeue` without `--me`, list other people's jobs. Don't copy that
into reports.

## Run work

### Golden rules

- **Nothing heavy on the login node.** `moriah-gw` is a small shared virtual
  machine. Everything else goes through
  Slurm, including compiling, `pip`/`conda` installs, large copies and
  downloads. Use `srun --pty $SHELL` for interactive work and `tmux` or
  `screen` to survive disconnects.
- **Ask before you spend.** Before submitting, show the person the script,
  the resources and an estimated cost (see "Cost"), and wait for their OK.
  Start with a short, small test job.
- **Request what you need, not the maximum.** Oversized requests wait longer,
  lower the lab's priority for everyone, and on Moriah also cost more,
  because billing counts allocated resources, not used ones.
- **Don't hammer the scheduler.** No loops over `sbatch` (use `--array`) and
  no `watch squeue` (use `--mail-type=END,FAIL --mail-user=<email>` or check
  occasionally). Combine jobs shorter than about 5 minutes into one.
- **Results go to persistent storage.** `/tmp` on a compute node is local
  scratch that can be wiped when the job or node ends. Never leave the only
  copy of a result there; copy it to the lab folder and tell the person the
  exact path.

### Defaults you get if you ask for nothing

Checked on 2026-11-05:

- time limit 2 hours, maximum 7 days;
- 7.5 GiB of RAM per CPU (1 CPU unless you ask for more);
- the CPU-only `glacier` partition.

Check the live values with the snapshot script. The last check of the
interactive-job limit (2026-09-24) found at most 2 per user; check `slimits`
for the person's current limits.

### Batch job

```bash
#!/bin/bash
#SBATCH --job-name=myjob
#SBATCH --time=4:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=logs/%x_%j.out    # %x job name, %j job id
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=<email>

. /sci/labs/<account>/<username>/envs/myenv/bin/activate
python train.py
```

Submit with `sbatch job.sh`. Create `logs/` first. For many similar runs use
`#SBATCH --array=0-49%10` (at most 10 at once) and read
`$SLURM_ARRAY_TASK_ID`.

### GPUs

Request a GPU type with `--gres=gpu:<type>:<count>`. On 2026-11-05 the types
were:

| Type | Nodes | GPU memory | Good for |
|---|---|---|---|
| `l4` | catfish, 5 x 8 GPUs | 24 GB | inference, small to medium training |
| `l40s` | salmon, 10 x 8 GPUs | 48 GB | training and fine-tuning |
| `h200` | goldfish, 1 x 8 GPUs | 141 GB | large models, multi-GPU |
| `a100` | dogfish, 2 x 8 GPUs | 80 GB | out of service (drained) at the last check |

Choose the smallest GPU that fits the model in memory. Only ask for more than
one GPU if the code really uses several; idle GPUs are flagged by the cluster's
resource monitor. Guide: <https://wiki.rcs.huji.ac.il/hurcs/guides/gpu>.

### Interactive work

```
srun --time=2:00:00 --cpus-per-task=2 --mem=8G --pty $SHELL
srun --time=2:00:00 --gres=gpu:l4:1 --mem=32G --pty $SHELL
```

Don't leave interactive shells open overnight: they hold, and bill, their
resources until they exit. For Jupyter use the HURCS batch script and SSH
tunnel: <https://wiki.rcs.huji.ac.il/hurcs/software/jupyter>.

### Priority and waiting

Priority comes from the partition, the lab's and person's recent usage
(fairshare, half-life 7 days) and time in queue. `squeue --me` shows the
reason a job waits:

- `Priority` / `Resources`: normal waiting.
- `AssocGrpGRES` or a similar `AssocGrp...` reason: the lab has reached its
  simultaneous-use limit.
- `AssocGrpLicense`: too many interactive jobs.

`squeue --start -j <id>` estimates the start time.

Other options:

- `--qos=high`: jumps the queue. It is limited per lab and shared, so use it
  only when the person asks.
- `--qos=low`: yields to everyone else.
- `--killable --requeue`: can run beyond the lab limit, but may be stopped and
  requeued at any time. Only for jobs that save checkpoints and can resume.

### After a job

Run `seff <jobid>` on completed jobs to see actual CPU and memory efficiency,
then trim the next request (about 10-15% above what was used). Use
`sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS,AllocTRES` for details.
If a job was killed for memory (`OUT_OF_MEMORY`), raise `--mem`. If it hit the
time limit (`TIMEOUT`), raise `--time` or add checkpointing.

## Cost

Compute is billed in CRUs. One CRU is one hour of a whole node. A job is
charged by the largest share of a node it was allocated (not what it used): its CPUs, its RAM,
or its GPU memory. That share is multiplied by the hours and the node's hourly
price:

```
share = max(CPUs / node CPUs, RAM / node RAM, GPU memory / node GPU memory)
cost  = share x hours x price per node-hour
```

For example, 1 L40S GPU, 8 CPUs and 64 GB on a salmon node is
share = max(8/64, 64/1536, 48/384) = 0.125 of the node.

Asking for lots of RAM on a GPU node can make RAM the largest share and raise
the bill. Storage is billed per TB of quota per month, by tier.

Take current prices from the HURCS
[billing page](https://wiki.rcs.huji.ac.il/hurcs/accounts/billing) or the
[cost calculator](https://pages.cs.huji.ac.il/system/hurcs-calculator-deploy/)
each time (the wiki script can read the billing page); don't quote prices from
memory.

## Storage

| Path | What it is | Backup |
|---|---|---|
| `~` (home) | home, 5 GB hard limit; config files and small scripts only | snapshots and backup |
| `/sci/labs/<pi>/<username>` | main working storage, fast | snapshots |
| `/sci/nosnap/<pi>/<username>` | fast scratch and temporary files | none |
| `/sci/backup/<pi>/<username>` | fast, with full backup | snapshots and backup |
| `/sci/archive/<pi>/<username>` | long-term storage, not for computing | none |

Home is usually `/sci/home/<username>`, but some older CS accounts have it
elsewhere (for example `/cs/usr/<username>`); use `~` or `echo $HOME`. A full
home can block login and job submission. It fills from `pip install`, R and
MATLAB packages and VS Code servers unless those go to an environment in the
lab folder. Check what uses the space with `ncdu ~` or `du -sh ~/.[!.]* ~/*`
(run on a compute node).

Each lab gets 1 TB in `/sci/labs` by default; the PI changes quotas with a
form ([quota management](https://wiki.rcs.huji.ac.il/en/hurcs/accounts/quota-management)).
Put code, environments and data in the lab folder, never in home; large
disposable intermediates go in `nosnap`.

**A folder existing proves nothing about what the lab paid for.** Storage is
two types (fast, archive) with services layered on top (snapshots,
no-snapshots, backup). Every user folder holds shortcuts (symlinks) to the
other volumes, so `backup`, `archive` and `nosnap` links are there for
everyone. What differs between labs is the quota and which service is active.
The default allocation is 1 TB of fast storage only, with no backup and no
archiving; backup is a separate paid service. Before telling someone to move
data to backed-up or archive storage, say that it depends on whether their PI
pays for that service, and send them to their PI or HURCS to confirm.

Snapshots are taken every 4 hours (kept 24 hours), nightly (kept 2 weeks) and
monthly (kept 3 months), so recently deleted files in `/sci/labs` can often be
recovered. Snapshots are not a backup: a storage failure loses them too.
Nothing in `nosnap` can be recovered. Ask before deleting anything in lab
storage: other lab members may depend on it.

Raise data-safety warnings when they apply, not on every storage answer:
when the person is about to put something they can't afford to lose (code,
final results, raw data) on an unprotected volume, or to delete or overwrite
data there. When they are only finding, listing or reading files, a neutral
note ("this is on nosnap") is enough. Repeated warnings teach people to
ignore them.

Moving data: `rsync`/`scp` through `moriah`, SFTP
(<https://wiki.rcs.huji.ac.il/hurcs/guides/rcs-sftp>), Globus for large
transfers (<https://wiki.rcs.huji.ac.il/en/hurcs/guides/Globus>), and rclone
for Google Drive (<https://wiki.rcs.huji.ac.il/hurcs/guides/rclone_sync_gdrive>).
Run large transfers as Slurm jobs, not on the login node.

## Software

Modules (Lmod with Spack) are available on compute nodes, not on the login
node. Discover software inside the intended compute allocation. From the
login node, a command such as
`srun zsh -c ". /etc/profile.d/huji-lmod.sh; module avail"`
starts a billed allocation; the approval and resource guidance above applies.
In a non-interactive shell on a compute node (such as an agent's command
tool), `module` may be undefined until you run
`. /etc/profile.d/huji-lmod.sh` in the same command.

Use `module avail spack` to discover software subsets, then
`module load spack/<subset>` with a name from that listing. `spack/all`
exposes the main software catalogue. `module avail` lists the modules in
the selected subset; `module spider <name>` searches for a package and its
versions.

Many packages installed as dependencies are hidden from ordinary listings.
Before concluding that software is unavailable or installing another copy,
include hidden modules in the search:

```bash
module --show_hidden avail
module --show_hidden spider <name>
```

The first command includes hidden modules within the selected subset. To
expose the full dependency catalogue instead, use:

```bash
module load spack/all-dependencies
module avail
```

For a chosen version, `module --show_hidden spider <full-module-name>`
shows any prerequisite subsets to load. Load those first, then
`module load <full-module-name>`. Batch scripts must load their required
subsets and modules themselves. Names and versions change; an older wiki
list does not establish current availability. R, MATLAB and Jupyter have
their own wiki pages.

Some everyday tools are installed directly on compute nodes, with no module:
`git`, Node.js (`node`), `tmux`, `screen` and `ncdu` (checked 2026-11-05).
`rg` (ripgrep) and `fd` are not installed; use `grep -r` and `find`. A tool
missing from `PATH` is not proof it is unavailable: check modules first.

- **Python**: inside the intended compute allocation, check
  `command -v python3` and `python3 --version` after loading any required
  modules. Do not infer the compute environment from the gateway or an
  older wiki version number. Make a virtual environment in the lab folder,
  from inside an `srun` session:
  `python3 -m venv /sci/labs/<pi>/<username>/envs/<name>`. Then activate it
  with `.` (bash, zsh) or `source .../activate.csh` (csh). Plain
  `pip install --user` fills the 5 GB home.
- **After an upgrade**: check the interpreter, required modules and imports
  in an existing environment before restarting a long job. Use a small test
  within an authorised allocation. If the environment no longer works,
  create a new one from the project's dependency specification and verify
  it before replacing the old environment; do not delete it automatically.
- The default login shell varies: check `echo $SHELL`. Batch scripts should
  start with `#!/bin/bash`. In zsh, `read -p` means something else (it reads
  from a coprocess), so give zsh users `printf 'Prompt: '; read VAR` instead.
- More: <https://wiki.rcs.huji.ac.il/hurcs/software/modules>,
  <https://wiki.rcs.huji.ac.il/hurcs/software/python>.

## Help

- HURCS wiki: <https://wiki.rcs.huji.ac.il/hurcs>, including training videos.
- Problems with the cluster: the login banner says to write to `system@cs`
  (the CS system group).
