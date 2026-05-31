#!/usr/bin/env bash
set -euo pipefail

command -v neumo-blindscan neumo-tune neumo-dmx stid135-blindscan tune-s2 szap-s2 femon-s2
neumo-blindscan --api-version
lspci -nnk | grep -A3 -E '544d:6178|TBS.*DVB|Multimedia controller' || true
find /dev/dvb -maxdepth 3 \( -type c -o -type l \) -printf '%M %u:%g %p\n' | sort

