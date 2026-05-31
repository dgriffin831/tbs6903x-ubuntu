# One-Shot Prompt

Paste this into Codex or another shell-capable coding agent on a fresh Ubuntu host with the TBS6903x installed:

```text
Clone https://github.com/dgriffin831/tbs6903x-ubuntu, read the README, then run the installer end to end:

git clone https://github.com/dgriffin831/tbs6903x-ubuntu.git
cd tbs6903x-ubuntu
sudo ./scripts/install.sh

After it finishes, run ./scripts/verify.sh and report whether /dev/dvb/adapter0 and /dev/dvb/adapter1 exist and whether neumo-blindscan --api-version returns api_version=1700.
```

