# Patches Applied

These are local compatibility fixes needed on this Ubuntu 24.04 / kernel 6.8 host.

The installer applies these patch files automatically:

```text
patches/neumo-linux-media/tbs6903x-ubuntu-6.8.patch
patches/blindscan/neumo-ioctl-compat.patch
```

## Disable CCS Camera Driver

Both official TBS and neumo media builds failed in the unrelated CCS camera driver. The practical workaround was to disable it in the generated media build config:

```text
CONFIG_VIDEO_CCS=n
CONFIG_VIDEO_CCS_PLL=n
```

Files adjusted in each media build tree:

```text
v4l/.config
v4l/.myconfig
```

## TBS ECP3 DMA Fix

The unpatched TBS/neumo `tbsecp3` driver failed probing this card with:

```text
dma: memory alloc failed
probe of 0000:21:00.0 failed with error -12
```

The fix was applied to both official and neumo `tbsecp3` trees.

In `tbsecp3-core.c`, use the coherent DMA mask API:

```c
if (dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(64)))
	if (dma_set_mask_and_coherent(&pdev->dev, DMA_BIT_MASK(32)))
```

In `tbsecp3-dma.c`, program the upper 32 bits of the DMA address instead of forcing zero:

```c
tbs_write(adapter->dma.base, TBSECP3_DMA_ADDRH,
	  upper_32_bits(adapter->dma.dma_addr));
```

This changed probe behavior from DMA allocation failure to successful registration of both DVB adapters.

## Neumo `rc-main.c` Version Logging Fix

The neumo driver build failed in `rc-main.c`:

```text
function declaration isn't a prototype
'ref' undeclared
```

Fixes:

```c
static void version_log(void)
```

and:

```c
printk(KERN_ERR "neumodvb blindscan drivers %s; %s;%s;\n", rev, tag, branch);
```

The call to `version_log();` was added in `rc_core_init()` after successful class registration. This also confirms in dmesg that the neumo driver path is loaded:

```text
neumodvb blindscan drivers GIT-REV = "5f0b5d683"; ... GIT-BRANCH = "deepthought";
```

## Blindscan Userspace Ioctl Compatibility

The `blindscan` userspace headers did not match the installed neumo kernel header for this driver tree. Symptoms:

```text
FE_GET_EXTENDED_INFO failed: card does not support blindscan?
unsupported ioctl
problem setting rf_input=0 as_master=1 ret=-1
```

Patched `src/blindscan/src/neumo-frontend.h` to match the neumo driver header:

```c
#define FE_SET_PROPERTY              _IOW('o', 82, struct dtv_properties)
#define FE_GET_PROPERTY              _IOR('o', 83, struct dtv_properties)
#define FE_ALGO_CTRL                 _IOW('o', 84, struct dtv_algo_ctrl)
#define FE_SET_RF_INPUT              _IOW('o', 85, struct fe_rf_input_control)
#define FE_GET_EXTENDED_INFO         _IOR('o', 86, struct dvb_frontend_extended_info)
#define FE_DISEQC_SEND_LONG_MASTER_CMD _IOW('o', 87, struct dvb_diseqc_long_master_cmd)
```

Also patched `src/blindscan/src/stid135-blindscan.cc` so a nonessential delivery-system capability query does not abort after `FE_GET_EXTENDED_INFO` has already succeeded:

```c
scanner.xprintf("FE_GET_PROPERTY capability query failed: %s; continuing with extended frontend info\n",
		strerror(errno));
```

After rebuilding and reinstalling the tools, STiD135 blindscan/spectrum acquisition worked and produced spectrum files.
