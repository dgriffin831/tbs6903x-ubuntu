#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
neumodvb_root="$repo_root/src/neumodvb"

if [[ ! -f "$neumodvb_root/gui/neumodvb.py" ]]; then
  echo "NeumoDVB source tree not found at: $neumodvb_root" >&2
  exit 1
fi

if [[ ! -d "$neumodvb_root/build/src" ]]; then
  echo "NeumoDVB has not been built yet. Run this first:" >&2
  echo "  cd $neumodvb_root && mkdir -p build build_ext && cd build && cmake .. && make -j\"\\$(nproc)\"" >&2
  exit 1
fi

if ! command -v neumo-blindscan >/dev/null 2>&1; then
  echo "neumo-blindscan is not installed. Run: sudo ./scripts/install.sh" >&2
  exit 1
fi

if ! neumo-blindscan --api-version >/dev/null 2>&1; then
  echo "Neumo blindscan tools are installed but cannot load the Neumo driver API." >&2
  echo "Run ./scripts/verify.sh for details, then rerun sudo ./scripts/install.sh if needed." >&2
  exit 1
fi

if [[ ! -d /dev/dvb ]]; then
  echo "/dev/dvb is missing; no DVB adapters are available to NeumoDVB." >&2
  echo "Check that the running kernel has the neumo tbsecp3 driver installed and loaded:" >&2
  echo "  sudo modprobe tbsecp3" >&2
  echo "  ./scripts/verify.sh" >&2
  exit 1
fi

if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY is not set. Connect with X11 forwarding first, for example:" >&2
  echo "  ssh -Y ubuntu@<server-ip>" >&2
  exit 1
fi

cd "$neumodvb_root/gui"
exec python3 ./neumodvb.py "$@"
