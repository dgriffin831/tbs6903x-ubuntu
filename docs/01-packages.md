# Packages Installed

Base build and DVB runtime packages:

```bash
sudo apt install -y \
  build-essential git linux-headers-$(uname -r) patchutils \
  libproc-processtable-perl v4l-utils dvb-tools dvblast dvb-apps \
  libdvbv5-dev dtv-scan-tables w-scan w-scan-cpp mumudvb \
  dvbstream dvbtune pkg-config make gcc
```

Blindscan/neumo userspace build dependencies:

```bash
sudo apt install -y \
  clang cmake libconfig-dev libconfig++-dev mold \
  libfmt-dev liblog4cxx-dev
```

