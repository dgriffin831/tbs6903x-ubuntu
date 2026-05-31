# Test Commands

## Basic Verification

```bash
lspci -nnk -s 21:00.0
find /dev/dvb -maxdepth 3 \( -type c -o -type l \) -printf '%M %u:%g %p\n' | sort
neumo-blindscan --api-version
```

Expected:

```text
Neumo Drivers: api_version=1700
```

## No Dish / LNB Connected Tests

These tests are useful to verify the RF input, spectrum path, and H/V voltage switching. With no dish, expect noise-floor spectrum data and no peaks or locks.

Vertical polarity, adapter 0, RF input 0:

```bash
sudo timeout 45s stid135-blindscan \
  -c blindscan \
  -a 0 \
  --rf-in 0 \
  -p V \
  --spectrum-method fft \
  --spectral-resolution 100 \
  -s 10700000 \
  -e 10800000 \
  universal
```

Horizontal polarity:

```bash
sudo timeout 45s stid135-blindscan \
  -c blindscan \
  -a 0 \
  --rf-in 0 \
  -p H \
  --spectrum-method fft \
  --spectral-resolution 100 \
  -s 10700000 \
  -e 10800000 \
  universal
```

Generated files:

```text
/tmp/spectrum_rf0_V.dat
/tmp/spectrum_rf0_H.dat
/tmp/peaks_rf0_V.dat
/tmp/peaks_rf0_H.dat
/tmp/blindscan_rf0.dat
```

## Once A Dish Is Available

Run a wider spectrum scan against the known satellite position:

```bash
sudo timeout 120s stid135-blindscan \
  -c blindscan \
  -a 0 \
  --rf-in 0 \
  -p BOTH \
  --spectrum-method fft \
  --spectral-resolution 100 \
  universal
```

If the dish is aligned, `/tmp/peaks_rf0_*.dat` should contain candidate peaks and `/tmp/blindscan_rf0.dat` should contain locked transponders.

## IQ / Constellation Sample Path

This requires a real carrier to be useful:

```bash
sudo neumo-tune \
  -a 0 \
  --rf-in 0 \
  -c iq \
  -f 10719000 \
  -p V \
  -n 8000
```

The TBS6903x/STiD135 path supports constellation/IQ sample capture through the neumo API. It is not a general wideband SDR raw RF IQ capture device.
