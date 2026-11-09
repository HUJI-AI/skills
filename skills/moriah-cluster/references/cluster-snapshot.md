# Moriah cluster snapshot

Taken: 2026-11-05 14:03 UTC

## Node types

| Node group | Nodes | CPUs/node | RAM/node | GPUs/node | Nodes usable now |
|---|---|---|---|---|---|
| catfish | 5 | 64 | 1.0 TB | 8 x L4 | 5 |
| dogfish | 2 | 256 | 2.0 TB | 8 x A100 | 0 |
| glacier | 38 | 128 | 1.0 TB | none | 31 |
| goldfish | 1 | 128 | 1.8 TB | 8 x H200 | 1 |
| salmon | 10 | 64 | 1.5 TB | 8 x L40S | 9 |

"Usable now" excludes nodes that are down, drained or reserved at snapshot time.

## Partitions

| Partition | Nodes | Default time | Max time | Default | Who can use it |
|---|---|---|---|---|---|
| catfish-k | catfish-[01-05] | 02:00:00 | 7-00:00:00 | NO | killable jobs only (`--killable`) |
| catfish | catfish-[01-05] | 02:00:00 | 7-00:00:00 | NO | all lab accounts |
| salmon-k | salmon-[01-10] | 02:00:00 | 7-00:00:00 | NO | killable jobs only (`--killable`) |
| salmon | salmon-[01-10] | 02:00:00 | 7-00:00:00 | NO | all lab accounts |
| goldfish-k | goldfish-01 | 02:00:00 | 7-00:00:00 | NO | killable jobs only (`--killable`) |
| goldfish | goldfish-01 | 02:00:00 | 7-00:00:00 | NO | all lab accounts |
| dogfish-k | dogfish-[01-02] | 02:00:00 | 7-00:00:00 | NO | killable jobs only (`--killable`) |
| dogfish | dogfish-[01-02] | 02:00:00 | 7-00:00:00 | NO | all lab accounts |
| glacier-k | glacier-[01-38] | 02:00:00 | 7-00:00:00 | NO | killable jobs only (`--killable`) |
| glacier | glacier-[01-38] | 02:00:00 | 7-00:00:00 | YES | all lab accounts |

## GPU types you can request

- `--gres=gpu:a100:1`
- `--gres=gpu:h200:1`
- `--gres=gpu:l4:1`
- `--gres=gpu:l40s:1`

QoS levels available to regular users: normal,high,low
