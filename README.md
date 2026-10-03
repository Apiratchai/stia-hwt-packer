# stia-hwt-packer

Build Huawei `.hwt` watch faces on Linux, no Theme Studio needed.
Targets **HWHD06** (Huawei Watch Fit, 280×456). Ships with a sample face, **ClaudeFit**.

## Quickstart

```sh
git clone https://github.com/Apiratchai/stia-hwt-packer && cd stia-hwt-packer
npm run setup -- /path/to/ThemeStudio.app  # one time, see below
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
npm ci && npm run build                    # -> claude-fit-pixel.hwt
```

`npm run setup` also accepts the official Studio package (`.zip`/`.tar.gz`)
or scans standard install locations. Theme Studio itself must be downloaded
manually (license acceptance) — this repo ships no Huawei files:

- schemas (`template_watch2.proto`, Stia profile) load from your install via
  `STIA_STUDIO_DIR` or `.studio-dir`
- `npm run art` regenerates sample assets only, `npm run pack` packs only

## Install to watch

Via Gadgetbridge (no Huawei account needed):

1. Install Gadgetbridge Nightly, force-stop Huawei Health, pair the Fit.
2. Copy `claude-fit-pixel.hwt` to the phone, tap it → open with Gadgetbridge → Install.
3. Keep the watch screen awake until the transfer finishes.

## Verified

- Installed and rendering on Huawei Watch Fit (Fit-420 / Stia-B09).
- Reference `com.huawei.watchface` SHA-256:
  `5a24e40f1600ce32d665e869cb54c6faf68cc4bd27e12b45092086328cc43fcc`
- Repeated builds are byte-identical (fixed ZIP timestamps, pinned deps).

## License

MIT for this repo's code. Liberation fonts under OFL 1.1 (`fonts/OFL.txt`).
No Huawei files vendored. Not affiliated with Huawei.
