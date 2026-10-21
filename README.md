# CleanYourTV for Android 6

A fork of [Gathin23/cleanyourtv](https://github.com/Gathin23/cleanyourtv) that runs on
**Android 6.0.1 (API 23)**.

Upstream targets API 26+. Older TVs — including many 2017–2019 China-market sets that
still ship Android 6 — cannot install it. This fork lowers the floor so those devices
can use the launcher too.

The launcher replaces the stock home screen: a dark tile grid, a dock, three pills
(Inputs / network / Settings), a clock, and a clock screensaver. No ads, no content
rows, no background service.

---

## What differs from upstream

| Area | Upstream | This fork |
|---|---|---|
| `minSdk` | 26 | **23** |
| Fonts | `res/font` XML font resources | `assets/fonts` + `Typeface.createFromAsset` |
| Date/time | `java.time` | `JTime`, a small `Calendar`-based shim |
| Connectivity callbacks | `registerDefaultNetworkCallback` only | version-guarded fallback |
| RecyclerView | 1.3.2 | **1.2.1** (see `libs/README.md`) |
| App discovery | `LEANBACK_LAUNCHER` only | also merges `LAUNCHER` when few TV entries are found |
| Input switching | passthrough channel URI | falls back to the vendor source panel on firmware that needs it |
| F1 race calendar | included | **removed** |

Fonts, festival skins, sunrise/sunset backsplash and the clock screensaver all still work.

The F1 race-weekend panel is gone, together with its code, layout and the `java.time`
calls it depended on. It was a personal feature rather than a compatibility concern.

## Supported devices

Verified by hand on one device:

- **Xiaomi Mi TV 4 (MiTV4-ANSM0, `xmen`)**, Android 6.0.1, firmware `2057`, Amlogic platform

That is the only configuration tested. Other Android 6 sets will probably work, but the
panel layout and the input-switching fallback were tuned against this one. If you try it
elsewhere and something misbehaves, an issue with `adb logcat` output is welcome.

## Install

```bash
adb connect <tv-ip>:5555
adb install -r launcher.apk
adb shell input keyevent KEYCODE_HOME
```

The launcher declares `CATEGORY_HOME`, so after installing it becomes a home candidate.
On most sets pressing Home once and choosing "always" is enough.

### Before you start

Some sets will not hand Home to a third-party launcher while the stock one is enabled.
If Home keeps going to the stock launcher after installing:

1. Note the stock launcher package first: `adb shell pm list packages | grep -i home`
2. Disable it for the current user: `adb shell pm uninstall --user 0 <that.package>`
3. Press Home again

**Back up first.** User-level uninstall is reversible, but you want the APK on hand:

```bash
adb shell pm path <that.package>            # prints package:/data/app/.../base.apk
adb pull /data/app/.../base.apk stock-launcher.apk
```

To undo:

```bash
adb install -r -d stock-launcher.apk
```

If you installed over the top and want the old Home back without uninstalling this one,
just re-enable the stock launcher and pick it from the Home chooser.

## Build

No Gradle. `build.sh` drives `aapt2`, `javac`, `d8`, `zipalign` and `apksigner` directly.

```bash
./build.sh
```

Requires JDK 8+, Android SDK build-tools 34+ and platform 31, plus the jars described in
`libs/README.md`. Use **build-tools 36** for `d8` — the 34 build fails on some inner
classes with an internal `NullPointerException`.

Set `ANDROID_SDK`, `BUILD_TOOLS`, `PLATFORM_JAR` or `D8_JAR` to override the defaults.

Two helper scripts live in `tools/`:

- `gen_lib_r.py` — writes the `R` class each AndroidX library needs (Gradle normally does this)
- `add_dex_assets.py` — merges `classes.dex` and `assets/` into the aapt2 output

## Configuration

A theme can drop a `config.json` into the app's external files directory:

```
/sdcard/Android/data/com.gathin.tvhome/files/config.json
```

It controls dock apps, grid columns, wallpaper rotation, theme colours and card modules.
See upstream's `themes/` for examples.

## Notes

- The launcher is plain Java with two small AndroidX dependencies; it holds no wake lock
  and starts no service.
- `HomeKeyService` / `InputKeyService` are optional accessibility helpers, off unless you
  enable them.
- If the grid only shows a few apps, the set's boot entries probably declare only
  `CATEGORY_LAUNCHER`. This fork merges those in when the TV list is short — if you still
  see too few, check `adb shell pm list packages` for what is actually installed.
- Disabling the stock launcher means firmware updates are the only thing that will bring
  it back. Whatever you disable stays disabled until you reinstall it.

## Licence

MIT, same as upstream. See `LICENSE`.

Original work Copyright (c) 2026 Gathin.
The Outfit typeface is under the SIL Open Font License 1.1 — see `FONT-LICENSE-OFL.txt`.

This fork is not affiliated with Xiaomi or with the upstream author. It is provided as
is, without warranty of any kind.
