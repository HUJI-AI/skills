# Giving an AI agent access to Moriah

Read this before you set up any way for an agent (including yourself) to run
commands on Moriah without the person typing their credentials each time.

## What normal login looks like

Moriah uses two-factor login: a 6-digit one-time password (OTP) from Google
Authenticator, a browser extension or SMS, then the person's Unix password.
The OTP changes every minute, so an agent cannot log in on its own. The person
types both in their own terminal, never in the chat.

## What an SSH key changes

An SSH key is a standing credential. Two-factor login needs the person at
the keyboard every time; a key installed on Moriah works whenever whoever
holds it wants. Whoever can use the private key can:

- read, change and delete the person's files and the lab's shared data in
  `/sci/labs/<pi>/`, including other lab members' folders the person can write
  to;
- submit jobs that are billed to the PI's research budget;
- copy data off the cluster.

"Whoever can use the key" includes every AI agent, editor extension, script
and package install that runs as the person on their computer. They can read
`~/.ssh/`. If the key is loaded into `ssh-agent`, anything that can reach the
agent socket can use it, even with a passphrase set. A stolen laptop or a
malicious dependency gets the same access.

## The options, safest first

Present these to the person, recommend one, and let them choose. Do not
create keys or edit SSH configuration before they have chosen.

### 1. No standing access (safest)

The person logs in themselves. The agent writes job scripts and commands for
them to paste, and reads the output they paste back. Good for occasional use
and for anyone handling sensitive data.

### 2. A shared connection (recommended for agent work)

OpenSSH can keep one authenticated connection open and let later `ssh`
commands reuse it. The person logs in once in their own terminal, with OTP and
password. After that, `ssh moriah <command>` from the agent rides on that
connection without asking again. The connection closes once it has gone unused
for the `ControlPersist` time (4 hours below), or when the person closes it.
As long as the agent keeps using it, it stays open.

Add to `~/.ssh/config` (macOS, Linux or WSL; native Windows OpenSSH does not
support this):

```
Host moriah
    HostName moriah-gw.cs.huji.ac.il
    User <username>
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 4h
```

The person then runs `ssh moriah` once in their own terminal and enters the
OTP and password. Check it with `ssh -O check moriah`, and end it early with
`ssh -O exit moriah`.

Say clearly: while the connection is open, the agent has the same full access
as with a key. The gain is that access needs the person to start it, and ends
on its own once the connection sits unused. Close it with `ssh -O exit moriah`
when the work is done.

### 3. A dedicated SSH key (convenient, and standing access)

Only if the person has understood the section above and still wants it. Then
make it as narrow as possible:

- A separate key used only for Moriah, never their GitHub or general key:
  `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_moriah -C "moriah $(hostname)"`.
- **Set a passphrase.** Then a copied key file is useless on its own, and
  nothing can use it until the person unlocks it.
- In `~/.ssh/config`, add under `Host moriah`:
  `IdentityFile ~/.ssh/id_ed25519_moriah` and `IdentitiesOnly yes`.
- **The person installs it themselves**, because installing needs a normal
  two-factor login: `ssh-copy-id -i ~/.ssh/id_ed25519_moriah.pub moriah`,
  then OTP and password when asked.
- Tell them how to revoke it: on Moriah, delete the matching line from
  `~/.ssh/authorized_keys` (the comment at the end of the line says which
  computer it came from). Do this whenever a laptop is lost, reinstalled or
  retired.
- Suggest they tell their PI, since the key also reaches the lab's data and
  budget.

## Rules for the agent, whatever option is chosen

- Never ask for, accept, store or type the OTP or the Unix password. If the
  person pastes one into the chat, tell them to change the password at
  <https://registrar.cs.huji.ac.il/account>.
- Never generate a key, install one, or edit `~/.ssh/config` or
  `~/.ssh/authorized_keys` without the person's explicit go-ahead for that
  specific change.
- Never copy a private key anywhere, and never put one in a repository, a
  cloud service or a chat.
- Treat every command on Moriah as acting with the person's full rights over
  lab data and budget. Confirm before deleting, overwriting, or submitting
  anything bigger than a small test.
