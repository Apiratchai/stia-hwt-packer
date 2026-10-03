# stia-hwt-packer

Build Huawei `.hwt` watch faces on Linux without running Theme Studio.

**STIA** is the watch profile name used in Huawei Theme Studio's schema. This
packer currently targets **HWHD06**, the 280×456 Huawei Watch Fit profile.
`ClaudeFit` is the example face name; it is not the packer's format or scope.

The builder implements the export pieces needed by this profile: protobuf
encoding, indexed RLE images, the watch-face binary wrapper, and the `.hwt`
ZIP. It is a focused builder, not a visual editor or a universal Huawei face
converter.

## Quickstart

```sh
git clone <this-repo> && cd stia-hwt-packer
npm run setup -- /path/to/ThemeStudio.app   # one time (see Build)
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
npm ci && npm run build                      # -> claude-fit-pixel.hwt
```

## Install to watch

Via Gadgetbridge (no Huawei account, no modded app needed):

1. Install Gadgetbridge Nightly (`freeyourgadget.codeberg.page/fdroid/repo`).
2. Force-stop Huawei Health (avoids Bluetooth fights), pair the Fit in Gadgetbridge.
3. Copy `claude-fit-pixel.hwt` to the phone, tap it → open with Gadgetbridge → Install.
4. Keep the watch screen awake until the transfer finishes, then select the face on the watch.

## Build

Requirements: Python 3.10+, pip, Node.js 18+, and a local Huawei Theme
Studio install (Windows/macOS) for the schema files — this repo ships none.
Point the packer at it (one time):

```sh
npm run setup -- /path/to/ThemeStudio.app
# or straight from the downloaded official package (extracted to cache):
npm run setup -- /path/to/downloaded-package.(zip|tar.gz)
# e.g. the official macOS package (a .zip):
# https://contentcenter-vali-drcn.dbankcdn.cn/pvt_2/DeveloperAlliance_package_901_9/de/v3/Hk2CWELpTX6WEcofPpSPPQ/themestudio-mac-tool-11.0.20.310.zip?HW-CC-KV=V1&HW-CC-Date=20240611T055612Z&HW-CC-Expire=315360000&HW-CC-Sign=EB9D63F021ED400DDB3498A2DD12E5510DCAD3E92F75E54D1BCC3571629616D3
```

(`npm run setup` alone scans conventional install locations. It saves to
`.studio-dir`; `STIA_STUDIO_DIR` env var also works and takes precedence.
The official package itself must be downloaded manually so you accept
Huawei's license — the script never fetches it.)

Then install the pinned Python dependency and Node packages:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
npm ci
npm run build
```

This runs `make_face.py` to generate the ClaudeFit sample and then `pack.js`.
The output is `claude-fit-pixel.hwt`. `npm run art` regenerates the sample
assets and `npm run pack` packs the generated face without regenerating it.

The packer checks the protobuf round trip, Stia jump targets, image references,
RLE pixel round trips, and ZIP entries. ClaudeFit has also been installed and
checked on a physical watch (see Tested devices below). Other watch models
and firmware are not covered by that device check.

## Tested devices

- Huawei Watch Fit, model Fit-420 (codename Stia-B09), 280x456 (HWHD06).
  Firmware version not recorded yet — read from watch Settings > About.

## Reproducibility reference

Reference build (ClaudeFit sample, Stia/HWHD06):

- `com.huawei.watchface` SHA-256:
  `5a24e40f1600ce32d665e869cb54c6faf68cc4bd27e12b45092086328cc43fcc`
- Produced by `npm run build` from this repo's `make_face.py` + `face.json`
  inputs against the user's own Theme Studio 11 schemas; verified installed
  and rendering on Huawei Watch Fit (Fit-420 / Stia-B09).
- ZIP entry timestamps are fixed, so repeated builds are byte-identical for
  the whole `.hwt`, given the same dependency versions (see lockfiles).

## Inputs and scope

- Schema files (`template_watch2.proto`, Stia profile JSON) load from the
  user's own Theme Studio install via `STIA_STUDIO_DIR`. This repo vendors
  no Huawei files; field numbers used were cross-confirmed by decoding
  shipping `.hwt` binaries and Huawei's public widget/data reference.

- `fonts/` contains the two SIL Open Font License fonts used by the sample.
- `requirements.txt` pins the sample-art generator dependency.
- `make_face.py` generates the ClaudeFit example and its `face.json`.

STIA is the profile/type name in Huawei's schema; it is not presented
here as an acronym. The profile maps HWHD06 to 280×456. `ClaudeFit` is only the
sample face name.

## ClaudeFit sample

ClaudeFit includes a live 24-hour clock, date, heart rate, step count, burned
calories, battery, synced weather, tap shortcuts, and an animated mascot.
Weather comes from Huawei Health. Enable Weather reports and location access
there for current conditions.

Install `claude-fit-pixel.hwt` on the watch with the sideload workflow supported
by your Huawei Health/HookUtils setup. The `.hwt` is generated locally and is
not committed.

## Licensing and provenance

The root MIT license covers the project's original packer and sample-generator
code. It does not establish rights to Huawei's watch-face format or trademarks.
The Liberation fonts are under SIL OFL 1.1; see `fonts/OFL.txt`. No Huawei
schema, spec, image, or font files are vendored in this repository.

This repository does not claim Huawei approval. Review redistribution rights
before publishing.
