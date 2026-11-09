#!/usr/bin/env bash
# Read-only snapshot of the Moriah cluster, printed as Markdown.
#
# Run it ON Moriah. From your own computer:
#
#   ssh moriah 'bash -s' < moriah-snapshot.sh            # public cluster facts
#   ssh moriah 'bash -s -- --me' < moriah-snapshot.sh    # plus private details
#
# Or from a shell already on Moriah (login node or a compute node in a job):
#
#   bash moriah-snapshot.sh [--me]
#
# It only queries Slurm and the filesystem; it never submits, changes or
# cancels anything. Without --me it prints cluster facts for review before
# publishing (references/cluster-snapshot.md). --me adds details that stay
# private: login notices, software versions, scheduler internals,
# reservations, queue load, and the person's own
# account, limits and quota. It never prints other users' jobs or usage.

ME=0
[ "${1:-}" = "--me" ] && ME=1

# Non-interactive SSH sessions skip the login profile that puts Slurm on PATH
# and points it at the cluster configuration.
if ! command -v sinfo >/dev/null 2>&1; then
    # shellcheck disable=SC1091
    . /etc/profile >/dev/null 2>&1 </dev/null
fi
if ! command -v sinfo >/dev/null 2>&1; then
    echo "moriah-snapshot: Slurm commands not found; are you on moriah-gw?" >&2
    exit 1
fi
set -u  # only now: /etc/profile itself reads unset variables

echo "# Moriah cluster snapshot"
echo
echo "Taken: $(date -u '+%Y-%m-%d %H:%M UTC')"
echo

# Notices the administrators put in the login banner (maintenance, upgrades).
if [ "$ME" = 1 ] && [ -r /etc/motd ] && grep -q 'NOTICE' /etc/motd; then
    echo "## Notices from the login banner (private: do not publish)"
    echo
    echo '```'
    sed -n '/NOTICE/,$p' /etc/motd | sed 's/\x1b\[[0-9;]*m//g' | tr -d '#' | sed 's/^ *//; s/ *$//' | grep -v '^$'
    echo '```'
    echo
fi

echo "## Node types"
echo
echo "| Node group | Nodes | CPUs/node | RAM/node | GPUs/node | Nodes usable now |"
echo "|---|---|---|---|---|---|"
# One line per node: name cpus mem_MB gres state
sinfo -N -h -o '%N %c %m %G %T' | sort -u | awk '
{
    group = $1; sub(/-[0-9]+$/, "", group)
    total[group]++
    cpus[group] = $2
    mem[group] = sprintf("%.1f TB", $3 / 1024 / 1024)
    g = $4; if (g == "(null)") g = "none"; else { sub(/^gpu:/, "", g); split(g, p, ":"); g = p[2] " x " toupper(p[1]) }
    gpus[group] = g
    if ($5 !~ /down|drain|fail|maint|reserved/) up[group]++
}
END {
    for (k in total) printf "| %s | %d | %s | %s | %s | %d |\n", k, total[k], cpus[k], mem[k], gpus[k], up[k] + 0
}' | sort
echo
echo "\"Usable now\" excludes nodes that are down, drained or reserved at snapshot time."
echo

echo "## Partitions"
echo
echo "| Partition | Nodes | Default time | Max time | Default | Who can use it |"
echo "|---|---|---|---|---|---|"
scontrol show partition -o | while read -r line; do
    get() { echo "$line" | tr ' ' '\n' | sed -n "s/^$1=//p"; }
    name=$(get PartitionName)
    allow=$(get AllowAccounts)
    if [ "$allow" = "ALL" ] || [ -z "$allow" ]; then
        who="all lab accounts"
    else
        who="killable jobs only (\`--killable\`)"
    fi
    printf '| %s | %s | %s | %s | %s | %s |\n' "$name" "$(get Nodes)" "$(get DefaultTime)" \
        "$(get MaxTime)" "$(get Default)" "$who"
done
echo

echo "## GPU types you can request"
echo
sinfo -h -o '%G' | tr ',' '\n' | grep '^gpu:' | cut -d: -f2 | sort -u | sed 's/.*/- `--gres=gpu:&:1`/'
echo

echo "QoS levels available to regular users: $(sacctmgr -nP show qos format=name 2>/dev/null | grep -E '^(high|normal|low)$' | paste -sd, -)"
echo

[ "$ME" = 1 ] || exit 0

echo "## Live details (private: do not publish)"
echo
echo "- Host: \`$(hostname)\`"
echo "- OS: $(. /etc/os-release && echo "$PRETTY_NAME")"
echo "- Slurm: $(sinfo --version | awk '{print $2}')"
echo

echo "### Scheduler settings"
echo
scontrol show config | awk -F' *= *' '
/^(DefMemPerCPU|MaxArraySize|MaxJobCount|PreemptMode|PriorityDecayHalfLife|SelectTypeParameters)[ =]/ {
    printf "- %s: %s\n", $1, $2
}'
echo

echo "### Reservations"
echo
res=$(scontrol show reservation -o 2>/dev/null | grep -v 'No reservations')
if [ -z "$res" ]; then
    echo "None."
else
    echo "$res" | while read -r line; do
        get() { echo "$line" | tr ' ' '\n' | sed -n "s/^$1=//p"; }
        printf -- '- `%s`: %s to %s, nodes %s, flags %s\n' "$(get ReservationName)" \
            "$(get StartTime)" "$(get EndTime)" "$(get Nodes)" "$(get Flags)"
    done
fi
echo

echo "### Queue load"
echo
echo "- Jobs in queue: $(squeue -h | wc -l) ($(squeue -h -t PD | wc -l) pending)"
echo


echo "## Your account (private: do not publish)"
echo
echo "- User: \`$USER\`, shell: \`$(getent passwd "$USER" | cut -d: -f7)\`"
assoc=$(sacctmgr -nP show assoc user="$USER" format=account,qos,defaultqos 2>/dev/null | head -1)
echo "- Slurm account (lab): \`$(echo "$assoc" | cut -d'|' -f1)\`"
echo "- QoS allowed: $(echo "$assoc" | cut -d'|' -f2), default: $(echo "$assoc" | cut -d'|' -f3)"
echo
echo "Limits (your row, then your lab's):"
echo
echo '```'
# The first two data rows are the user and the lab; the rest are parents.
slimits 2>/dev/null | head -4
echo '```'
echo
echo "Fairshare (1.0 = highest priority, 0 = lowest):"
echo
echo '```'
sshare -U 2>/dev/null
echo '```'
echo
echo "Storage:"
echo
echo "- Home: \`$HOME\`, $(du -sh "$HOME" 2>/dev/null | cut -f1) used of the 5 GB quota"
account=$(echo "$assoc" | cut -d'|' -f1)
for tier in labs nosnap backup archive; do
    d=/sci/$tier/$account
    if [ -d "$d" ]; then
        echo "- \`$d\` exists$( [ -d "$d/$USER" ] && echo ", with your folder \`$d/$USER\`")"
    fi
done
