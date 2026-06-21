# TBS6903x Ubuntu Setup

Repeatable Ubuntu setup for the TBS6903x / TBS6903-X dual DVB-S/S2/S2X PCIe card.

This repo documents the working setup and includes the patches and installer used to bring the card up on Ubuntu 24.04 with kernel `6.8.0-110-generic`.

## Quick Install

On a fresh Ubuntu machine with the card installed and Secure Boot disabled:

```bash
git clone https://github.com/dgriffin831/tbs6903x-ubuntu.git
cd tbs6903x-ubuntu
sudo ./scripts/install.sh
```

Then verify:

```bash
./scripts/verify.sh
```

Expected driver API output:

```text
Neumo Drivers: api_version=1700
```

## Layout

- `scripts/install.sh` - one-shot installer for dependencies, source clones, patches, build, install, and verification.
- `scripts/verify.sh` - quick post-install checks.
- `scripts/live-waterfall.py` - live terminal waterfall for dish aiming with STiD135 spectrum scans.
- `scripts/spectrum-analyzer.py` - compact terminal plotter for generated spectrum `.dat` files.
- `scripts/run-neumodvb.sh` - guarded launcher for a locally built neumoDVB GUI tree.
- `patches/` - local compatibility patches applied by the installer.
- `docs/` - notes documenting the exact setup and fixes applied.

The installer creates upstream source checkouts under `work/` by default. Override this with:

```bash
WORKDIR=/opt/tbs6903x-build sudo -E ./scripts/install.sh
```

## Current Status

- Kernel: Ubuntu `6.8.0-110-generic`.
- Card: `544d:6178`, subsystem `6903:8888`.
- Driver in use: neumo/deeptho `tbsecp3` stack.
- DVB adapters: `/dev/dvb/adapter0` and `/dev/dvb/adapter1`.
- Neumo API: `api_version=1700`.
- Spectrum tests with an LNB but no dish succeeded for adapter 0, RF input 0, V and H polarity.

## Installed Commands

The following are installed in `/usr/local/bin`:

```bash
neumo-blindscan
neumo-tune
neumo-dmx
stid135-blindscan
tune-s2
szap-s2
femon-s2
```

## Local Helpers

For a live terminal waterfall while aiming the dish:

```bash
./scripts/live-waterfall.py -a 1 --rf-in 3 -p H \
  -s 11820000 -e 11870000 \
  --target-freq 11842000 \
  --lnb universal
```

For a static terminal plot of spectrum files generated under `/tmp`:

```bash
./scripts/spectrum-analyzer.py /tmp/spectrum_rf3_H.dat
```

## One-Shot AI Prompt

If using Codex or another shell-capable coding agent, use [docs/AI_PROMPT.md](docs/AI_PROMPT.md).
