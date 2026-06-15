# Fitness Boxing 3 (Switch) — custom music & custom charts

Reverse-engineering notes + tooling for modding **Fit Boxing 3 / Fitness Boxing 3** (JP) on a
jailbroken Nintendo Switch. Lets you replace the in-game songs with your own music and author
custom punch charts ("beatmaps"), served via Atmosphère LayeredFS — no rebuild of the game.

> ⚠️ This repo contains **only our own scripts and findings**. It deliberately excludes console
> keys (`prod.keys`/`title.keys`), the game's RomFS dump, the CRIWARE audio banks, and any
> copyrighted music — see `.gitignore`. You supply those from your own console/dump.

## TL;DR — what works
- ✅ **Custom charts** (which punches/dodges happen, when) — edit a Unity ScriptableObject, repack, LayeredFS.
- ✅ **Custom music** — re-encode your track to CRI HCA, inject into the AWB wave bank, LayeredFS.
- ✅ **Custom song names** — edit a text bundle.
- ✅ Live iteration over Wi-Fi (sys-ftpd), no SD swapping.

## The console / environment
- Switch with Picofly modchip, **Atmosphère on emuMMC**, firmware **20.5.0**.
- Game: **Fit Boxing 3 (JP)**. Base title id **`0100AC101BFA2000`** (update `…2800`, v1.3.0).
- Engine: **Unity, IL2CPP**. Asset bundles keep type-trees, so [UnityPy](https://github.com/K0lb3/UnityPy)
  reads/writes them as clean JSON — no Il2CppDumper needed.
- Audio: **CRIWARE ADX2** (`BGM.acb` cue sheet + `BGM.awb` wave bank, HCA codec, **unencrypted**).
- **LayeredFS works**: mods go in `sd:/atmosphere/contents/0100AC101BFA2000/romfs/Data/…`
  and apply on game launch. (Verified by a deliberate `globalgamemanagers` corruption test.)

## How the chart (beatmap) works
Runtime charts live at `…/StreamingAssets/aa/Switch/defaultassets_assets_database/scores/<id>_conv.bundle`
(MonoBehaviour class `ExerciseScore`). **Not** the authoring source `<id>.bundle` (`ExerciseScoreSource`) —
editing the source has no effect; the game loads the `_conv` form.

Format: `Table` of rows, each row = **32 beat-slots**; each slot has:
- **`Note`** = the actual punch/action the player throws. IDs from `exerciseactiondata`:
  `LS`=Left Jab, `RS`=Right Straight, `LH`/`RH`=Hooks, `LU`/`RU`=Uppercuts,
  `LD`/`RD`/`CD`=Duck L/R/Center, `LG`/`RG`=Block, `LW`/`RW`=Weave, `SB`=Sway, `POS`=Stand, …
- **`Message`** = the trainer's *voice/coaching cue* (IDs from `exercisemessagedata`, e.g. `i001`→voice clip). NOT a punch.
- `MessageCombo`, `Step`, `Zone` = combo grouping / sparse section markers.

Authoring rule learned the hard way: **swap punch identities inside the existing dense structure;
don't clear to sparse notes** — the note density drives the trainer's continuous motion and the
countdown/step accounting, so a sparse chart freezes the timer and idles the trainer.

`straightCombi1` (UI "Straight Combo #1", intensity low/normal/high = Intensity 0/1/2) →
ScoreId `ExerciseScore00` → `scores/exercisescore00_conv.bundle`.

## How the audio works
- `musiclistdata` (Music_001…) → `musicfiledata` → CRI cue `bgm03xx`. Each song has 3 length
  variants **f/h/s = 172.1 / 156.0 / 184.9 s** (the three intensities). Full-length tracks, not loops.
- All songs are arranged to a **shared fixed tempo ≈ 161.5 BPM** (measured: 9/10 songs identical).
- `BGM.awb` is **AFS2**: 95 subsongs, 4-byte offsets, **32-byte data alignment** (the stored offset
  is the *end of the previous blob*; real data starts at `align_up(offset, 32)` — this detail matters
  for repacking). HCA headers are plain (`HCA\0`), version differs (game v3 / VGAudio v2) but the
  game accepts v2.
- Song titles: `…/labeledrulebaseassets_assets_label/text/<lang>.bundle` → `MusicData` records
  (`_label` MD_mN_No3xx → `_text`). English UI font lacks CJK glyphs (Chinese names → tofu); use
  Latin names on `usen`, or switch the console to Chinese and edit `cnzh`.

## Pipeline / tools (in this repo)
| File | Purpose |
|---|---|
| `fb3/peek.py`, `peek2.py`, `poc_roundtrip.py` | Inspect / edit chart bundles with UnityPy (read→modify→repack lz4). |
| `fb3/hcaenc/` | C# (dotnet + VGAudio NuGet) WAV→HCA encoder: `dotnet run -- in.wav out.hca`. |
| `fb3/awb_inject.py` | Replace one subsong's HCA inside an AFS2/AWB wave bank (handles the 32-byte alignment). |
| `fb3/host/nxdt_host.py` | nxdumptool USB host, **patched for macOS** (skip `cur_dev.reset()` on Darwin — it re-enumerates the device and makes `set_configuration()` fail with errno 19). |
| `qlaunch_research/` | HOME-menu mod research: `extract_szs.py` (pure-Python Yaz0+SARC), `parse_bflyt.py`, and `CenteredCleanBottomRow_fw20.json` (layout patch to hide NSO/News/eShop/Share/Virtual-Game-Card and center the rest). |

### Custom-music recipe (one song)
1. `ffmpeg -i track.mp3 -t <variant_len> -ar 48000 -ac 2 out.wav` (match f/h/s length).
2. `dotnet run --project fb3/hcaenc -- out.wav out.hca`.
3. `python fb3/awb_inject.py BGM.awb out.hca BGM_new.awb <subsong_index>`.
4. (optional) edit the song name in the `usen` text bundle (UnityPy).
5. Push `BGM.awb` (+ text bundle) to `sd:/atmosphere/contents/0100AC101BFA2000/romfs/Data/StreamingAssets/…` via FTP, relaunch the game.

## Live workflow (no SD swapping)
- **sys-ftpd-light** installed (`sd:/atmosphere/contents/420000000000000E/`, anonymous, port 5000) →
  FTP always on in the background, even in-game.
- From the Mac (a VPN/TUN can hijack LAN routing, so bind the LAN interface):
  `curl --interface <lan-ip> --retry 5 --retry-connrefused -T file ftp://<switch-ip>:5000/<path>`
- LayeredFS reads at **game launch** → push, then close & relaunch the game. (A 509 MB AWB takes
  ~2.5 min over Wi-Fi; for fast iteration on big audio, a card reader is quicker.)

## Open questions / next
- Capacity: replacing existing slots is easy (~the game's song count); *adding* new slots needs
  extending the ACB cue sheet (harder).
- Beat sync: our DJ tracks (~129 BPM) vs the game's ~161.5 grid — either time-stretch the music or
  author charts whose notes land on the slower track's beats. The game's timing is loose enough that
  "good enough" is very playable as-is.
- HOME menu: build the `.nxtheme` from `CenteredCleanBottomRow_fw20.json` (SwitchThemeInjector CLI via
  dotnet, or Windows GUI), install via NXThemes Installer. Recovery = delete `contents/0100000000001000/`.
