# Driver Build And Install

For a fresh machine, prefer the automated path:

```bash
sudo ./scripts/install.sh
```

The manual notes below document how the working setup was found.

## Official TBS Driver

The official TBS tree was first built to bring up normal DVB reception:

```bash
cd /home/ubuntu/tbs6903x/src
git clone -b latest https://github.com/tbsdtv/media_build.git
git clone -b latest https://github.com/tbsdtv/linux_media.git media
cd media_build
./build
```

On Ubuntu kernel `6.8.0-110-generic`, the initial build failed in the unrelated `ccs` camera driver:

```text
ccs-core.c: error: too many arguments to function 'pm_runtime_get_if_active'
```

The workaround was to disable the unrelated CCS camera modules in `v4l/.config` and `v4l/.myconfig`:

```text
CONFIG_VIDEO_CCS=n
CONFIG_VIDEO_CCS_PLL=n
```

Then rebuild and install:

```bash
make -C v4l -j"$(nproc)"
sudo make install
sudo depmod -a
sudo modprobe tbsecp3
```

The official driver probed after the DMA patch described in `03-patches.md`.

## Neumo Driver

The deeptho/neumo driver was built to enable blindscan/spectrum/IQ APIs:

```bash
mkdir -p /home/ubuntu/tbs6903x/src/neumo_driver
cd /home/ubuntu/tbs6903x/src/neumo_driver
git clone -b deepthought https://github.com/deeptho/neumo_media_build.git media_build
git clone -b deepthought https://github.com/deeptho/linux_media.git media
cd media_build
make dir DIR=../media
make allyesconfig
make -C v4l -j"$(nproc)"
```

The build required the fixes listed in `03-patches.md`:

- disable unrelated CCS camera modules;
- fix neumo `rc-main.c` version logging;
- apply the same `tbsecp3` DMA fix as the official TBS tree.

The automated patch is stored in:

```text
patches/neumo-linux-media/tbs6903x-ubuntu-6.8.patch
```

Install and reload:

```bash
cd /home/ubuntu/tbs6903x/src/neumo_driver/media_build
sudo modprobe -r tbsecp3 gx1133 tas2101 stid135 dvb_core 2>/dev/null || true
sudo make install
sudo depmod -a
sudo modprobe tbsecp3
```

Verification:

```bash
lspci -nnk -s 21:00.0
find /dev/dvb -maxdepth 3 \( -type c -o -type l \) -printf '%M %u:%g %p\n' | sort
neumo-blindscan --api-version
```

Expected API output:

```text
Neumo Drivers: api_version=1700
```
