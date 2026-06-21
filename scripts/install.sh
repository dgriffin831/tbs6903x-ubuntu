#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKDIR="${WORKDIR:-$REPO_ROOT/work}"
JOBS="${JOBS:-$(nproc)}"
SUDO=""

if [[ "${EUID}" -ne 0 ]]; then
  SUDO="sudo"
fi

log() {
  printf '\n==> %s\n' "$*"
}

run_as_user() {
  if [[ "${EUID}" -eq 0 && -n "${SUDO_USER:-}" ]]; then
    sudo -u "$SUDO_USER" "$@"
  else
    "$@"
  fi
}

ensure_ubuntu() {
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    if [[ "${ID:-}" != "ubuntu" ]]; then
      printf 'This installer was tested on Ubuntu 24.04. Detected ID=%s; continuing anyway.\n' "${ID:-unknown}"
    fi
  fi
}

apt_install() {
  log "Installing Ubuntu packages"
  $SUDO apt-get update
  $SUDO apt-get install -y \
    build-essential git "linux-headers-$(uname -r)" patchutils \
    libproc-processtable-perl v4l-utils dvb-tools dvblast dvb-apps \
    libdvbv5-dev dtv-scan-tables w-scan w-scan-cpp mumudvb \
    dvbstream dvbtune pkg-config make gcc \
    clang cmake libconfig-dev libconfig++-dev mold \
    libfmt-dev liblog4cxx-dev
}

clone_or_update() {
  local branch="$1"
  local url="$2"
  local path="$3"

  if [[ -d "$path/.git" ]]; then
    log "Updating $path"
    run_as_user git -C "$path" fetch --depth=1 origin "$branch"
    run_as_user git -C "$path" checkout "$branch"
    run_as_user git -C "$path" reset --hard "origin/$branch"
  else
    log "Cloning $url"
    run_as_user mkdir -p "$(dirname "$path")"
    run_as_user git clone --depth=1 -b "$branch" "$url" "$path"
  fi
}

apply_patch_once() {
  local tree="$1"
  local patch_file="$2"

  if git -C "$tree" apply --check "$patch_file"; then
    log "Applying $(basename "$patch_file")"
    run_as_user git -C "$tree" apply "$patch_file"
  elif git -C "$tree" apply --reverse --check "$patch_file"; then
    log "Patch already applied: $(basename "$patch_file")"
  else
    printf 'Patch does not apply cleanly: %s\n' "$patch_file" >&2
    exit 1
  fi
}

disable_ccs_modules() {
  local build_dir="$1"

  for cfg in "$build_dir/v4l/.config" "$build_dir/v4l/.myconfig"; do
    [[ -f "$cfg" ]] || continue
    if grep -q '^CONFIG_VIDEO_CCS=' "$cfg"; then
      run_as_user sed -i 's/^CONFIG_VIDEO_CCS=.*/CONFIG_VIDEO_CCS=n/' "$cfg"
    else
      printf 'CONFIG_VIDEO_CCS=n\n' | $SUDO tee -a "$cfg" >/dev/null
    fi
    if grep -q '^CONFIG_VIDEO_CCS_PLL=' "$cfg"; then
      run_as_user sed -i 's/^CONFIG_VIDEO_CCS_PLL=.*/CONFIG_VIDEO_CCS_PLL=n/' "$cfg"
    else
      printf 'CONFIG_VIDEO_CCS_PLL=n\n' | $SUDO tee -a "$cfg" >/dev/null
    fi
  done
}

build_neumo_driver() {
  local driver_root="$WORKDIR/neumo_driver"
  local media_build="$driver_root/media_build"
  local media="$driver_root/media"

  clone_or_update deepthought https://github.com/deeptho/neumo_media_build.git "$media_build"
  clone_or_update deepthought https://github.com/deeptho/linux_media.git "$media"
  apply_patch_once "$media" "$REPO_ROOT/patches/neumo-linux-media/tbs6903x-ubuntu-6.8.patch"

  log "Configuring neumo media build"
  run_as_user make -C "$media_build" dir DIR=../media
  run_as_user make -C "$media_build" release VER="$(uname -r)"
  run_as_user make -C "$media_build" allyesconfig
  disable_ccs_modules "$media_build"

  log "Building neumo media modules"
  run_as_user make -C "$media_build/v4l" -j"$JOBS"

  log "Installing neumo media modules"
  $SUDO modprobe -r tbsecp3 gx1133 tas2101 stid135 dvb_core 2>/dev/null || true
  $SUDO make -C "$media_build" install
  $SUDO depmod -a
  $SUDO modprobe tbsecp3

  log "Installing TBS helper tools"
  run_as_user make -C "$media_build/tune-s2"
  run_as_user make -C "$media_build/szap-s2"
  run_as_user make -C "$media_build/femon-s2"
  $SUDO install -m 0755 "$media_build/tune-s2/tune-s2" /usr/local/bin/tune-s2
  $SUDO install -m 0755 "$media_build/szap-s2/szap-s2" /usr/local/bin/szap-s2
  $SUDO install -m 0755 "$media_build/femon-s2/femon-s2" /usr/local/bin/femon-s2
}

build_blindscan_tools() {
  local blindscan="$WORKDIR/blindscan"

  clone_or_update master https://github.com/deeptho/blindscan.git "$blindscan"
  apply_patch_once "$blindscan" "$REPO_ROOT/patches/blindscan/neumo-ioctl-compat.patch"

  log "Building blindscan userspace tools"
  run_as_user cmake -S "$blindscan" -B "$blindscan/build"
  run_as_user cmake --build "$blindscan/build" -j"$JOBS"

  log "Installing blindscan userspace tools"
  $SUDO install -m 0755 "$blindscan/build/src/neumo-blindscan" /usr/local/bin/neumo-blindscan
  $SUDO install -m 0755 "$blindscan/build/src/neumo-tune" /usr/local/bin/neumo-tune
  $SUDO install -m 0755 "$blindscan/build/src/neumo-dmx" /usr/local/bin/neumo-dmx
  $SUDO install -m 0755 "$blindscan/build/src/stid135-blindscan" /usr/local/bin/stid135-blindscan
  $SUDO install -m 0755 "$blindscan/build/src/libneumoutil.so" /usr/local/lib/libneumoutil.so
  $SUDO ldconfig

  $SUDO install -d -m 0755 /usr/config
  $SUDO install -m 0644 "$blindscan/config/neumo-blindscan.xml" /usr/config/neumo-blindscan.xml
  $SUDO install -m 0644 "$blindscan/config/neumo-tune.xml" /usr/config/neumo-tune.xml
  $SUDO install -m 0644 "$blindscan/config/neumo-dmx.xml" /usr/config/neumo-dmx.xml
  $SUDO install -m 0644 "$blindscan/config/stid135-blindscan.xml" /usr/config/stid135-blindscan.xml
}

verify_install() {
  log "Verifying install"
  command -v neumo-blindscan neumo-tune neumo-dmx stid135-blindscan tune-s2 szap-s2 femon-s2
  neumo-blindscan --api-version || true
  find /dev/dvb -maxdepth 3 \( -type c -o -type l \) -printf '%M %u:%g %p\n' 2>/dev/null | sort || true
}

main() {
  ensure_ubuntu
  apt_install
  build_neumo_driver
  build_blindscan_tools
  verify_install

  log "Done"
  printf 'If /dev/dvb is not present yet, reboot once and run: sudo modprobe tbsecp3\n'
}

main "$@"
