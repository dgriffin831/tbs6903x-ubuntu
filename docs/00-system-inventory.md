# System Inventory

## Host

- OS: Ubuntu 24.04.3 LTS.
- Kernel: `6.8.0-110-generic`.
- Secure Boot: disabled.
- User: `ubuntu`.
- DVB device group: `video`.

The user was added to the `video` group:

```bash
sudo usermod -aG video ubuntu
```

A new login session, or `newgrp video`, is needed before non-root access to `/dev/dvb/*` works in a shell that was already open.

## Card

Detected PCI device:

```text
21:00.0 Multimedia controller [0480]: TBS Technologies DVB Tuner PCIe Card [544d:6178]
Subsystem: TBS6903x (Dual DVB-S/S2/S2X) [6903:8888]
```

Loaded driver after setup:

```text
Kernel driver in use: TBSECP3 driver
Kernel modules: tbsecp3
```

DVB nodes:

```text
/dev/dvb/adapter0/{demux0,dvr0,frontend0,net0}
/dev/dvb/adapter1/{demux0,dvr0,frontend0,net0}
```

## Source Layout

The project source trees are under:

```text
/home/ubuntu/tbs6903x/src
```

Subdirectories:

- `media_build/` - official TBS media_build tree.
- `media/` - official TBS linux_media tree.
- `neumo_driver/media_build/` - deeptho/neumo media_build tree.
- `neumo_driver/media/` - deeptho/neumo linux_media tree.
- `blindscan/` - deeptho blindscan userspace tools.
- `neumodvb/` - deeptho neumodvb source checkout.

