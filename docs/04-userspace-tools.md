# Userspace Tools

For a fresh install, `scripts/install.sh` builds and installs these automatically. The commands below are the manual equivalent.

## TBS Helper Tools

Built from the official `media_build` tree:

```bash
cd /home/ubuntu/tbs6903x/src/media_build
make -C tune-s2
make -C szap-s2
make -C femon-s2
sudo install -m 0755 tune-s2/tune-s2 /usr/local/bin/tune-s2
sudo install -m 0755 szap-s2/szap-s2 /usr/local/bin/szap-s2
sudo install -m 0755 femon-s2/femon-s2 /usr/local/bin/femon-s2
```

## Neumo Blindscan Tools

Built from deeptho `blindscan`:

```bash
cd /home/ubuntu/tbs6903x/src/blindscan
cmake -S . -B build
cmake --build build -j"$(nproc)"
sudo install -m 0755 build/src/neumo-blindscan /usr/local/bin/neumo-blindscan
sudo install -m 0755 build/src/neumo-tune /usr/local/bin/neumo-tune
sudo install -m 0755 build/src/neumo-dmx /usr/local/bin/neumo-dmx
sudo install -m 0755 build/src/stid135-blindscan /usr/local/bin/stid135-blindscan
```

The tools expect config files at a path relative to `/usr/local/bin`, so these were installed:

```bash
sudo install -d -m 0755 /usr/config
sudo install -m 0644 config/neumo-blindscan.xml /usr/config/neumo-blindscan.xml
sudo install -m 0644 config/neumo-tune.xml /usr/config/neumo-tune.xml
sudo install -m 0644 config/neumo-dmx.xml /usr/config/neumo-dmx.xml
sudo install -m 0644 config/stid135-blindscan.xml /usr/config/stid135-blindscan.xml
```

## Installed Commands

```bash
command -v neumo-blindscan neumo-tune neumo-dmx stid135-blindscan tune-s2 szap-s2 femon-s2
```

Expected locations:

```text
/usr/local/bin/neumo-blindscan
/usr/local/bin/neumo-tune
/usr/local/bin/neumo-dmx
/usr/local/bin/stid135-blindscan
/usr/local/bin/tune-s2
/usr/local/bin/szap-s2
/usr/local/bin/femon-s2
```
