# Notes And Limits

## What Is Working

- PCI card detection.
- Neumo/deeptho kernel driver loading.
- Both DVB adapters exposed under `/dev/dvb`.
- Neumo API visible from userspace.
- STiD135 RF input selection.
- LNB-powered spectrum acquisition.
- Vertical and horizontal voltage paths.
- No-dish noise-floor spectrum files.

## What Needs A Dish

The following cannot be meaningfully verified until a dish is pointed at a satellite:

- real transponder peak detection;
- DVB-S/S2/S2X lock;
- MPEG-TS capture;
- MIS/PLS behavior;
- BBFRAME demux;
- useful IQ/constellation samples;
- blindscan performance against real carriers.

## Safety Notes

An open RF input is safe. An LNB and coax with no dish is also fine for short tests.

Avoid running LNB-voltage commands into a cable or adapter where the center conductor is shorted to shield. Stop scans before connecting or disconnecting F-connectors.

## Port Mapping

The card has two independent coax inputs. They are not in/out ports.

For current tests:

```text
adapter 0, rf-in 0
```

was used successfully. To test the second physical port, move the coax and run equivalent commands with:

```text
adapter 1, rf-in 0
```

or inspect the driver behavior if RF input mapping differs on this board revision.

