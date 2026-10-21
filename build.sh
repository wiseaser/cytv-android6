#!/usr/bin/env bash
# Build the launcher APK without Gradle.
#
# Usage:  ./build.sh
#
# Requires:
#   - JDK 8+ (javac on PATH)
#   - Android SDK build-tools 34+ (aapt2, zipalign, apksigner) and platform 31
#   - The AndroidX jars described in libs/README.md
#
# Override paths with env vars:
#   ANDROID_SDK   default: $HOME/Android/Sdk
#   BUILD_TOOLS   default: $ANDROID_SDK/build-tools/34.0.0
#   PLATFORM_JAR  default: $ANDROID_SDK/platforms/android-31/android.jar
#   D8_JAR        default: $ANDROID_SDK/build-tools/36.0.0/lib/d8.jar
#
# Use build-tools 36 for d8: the 34 build throws an internal NullPointerException on
# some inner classes (AppAdapter$1 among them).

set -euo pipefail

cd "$(dirname "$0")"

ANDROID_SDK="${ANDROID_SDK:-$HOME/Android/Sdk}"
BUILD_TOOLS="${BUILD_TOOLS:-$ANDROID_SDK/build-tools/34.0.0}"
PLATFORM_JAR="${PLATFORM_JAR:-$ANDROID_SDK/platforms/android-31/android.jar}"
D8_JAR="${D8_JAR:-$ANDROID_SDK/build-tools/36.0.0/lib/d8.jar}"

OUT=build
KEYSTORE="${KEYSTORE:-$OUT/debug.keystore}"
KEY_ALIAS="${KEY_ALIAS:-debug}"
KEY_PASS="${KEY_PASS:-android}"

# javac wants platform-style paths and ';' separators on Windows, ':' elsewhere.
SEP=":"
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) SEP=";" ;;
esac

to_native() {
  if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s' "$1"; fi
}

# Windows ships apksigner/aapt2 as .bat/.exe, so resolve the real command name.
tool() {
  local name="$1"
  for candidate in "$BUILD_TOOLS/$name" "$BUILD_TOOLS/$name.bat" "$BUILD_TOOLS/$name.exe"; do
    if [ -x "$candidate" ] || [ -f "$candidate" ]; then printf '%s' "$candidate"; return; fi
  done
  printf '%s' "$BUILD_TOOLS/$name"
}

rm -rf "$OUT"
mkdir -p "$OUT/res" "$OUT/gen" "$OUT/obj" "$OUT/dex"

echo "==> 1/7 compile resources"
"$(tool aapt2)" compile --dir app/src/main/res -o "$OUT/res/"

echo "==> 2/7 link resources and generate R.java"
"$(tool aapt2)" link \
  -o "$OUT/base.apk" \
  -I "$(to_native "$PLATFORM_JAR")" \
  --manifest app/src/main/AndroidManifest.xml \
  --java "$OUT/gen" \
  --min-sdk-version 23 --target-sdk-version 23 \
  -R "$OUT"/res/*.flat \
  --auto-add-overlay

echo "==> 3/7 generate library R classes"
python3 tools/gen_lib_r.py

echo "==> 4/7 compile Java"
find app/src/main/java -name '*.java' > "$OUT/sources.txt"
echo "$OUT/gen/com/gathin/tvhome/R.java" >> "$OUT/sources.txt"
find "$OUT/libgen" -name 'R.java' >> "$OUT/sources.txt"

CP="$(to_native "$PLATFORM_JAR")"
for j in libs/*/classes.jar libs/*.jar; do
  [ -e "$j" ] && CP="$CP$SEP$(to_native "$j")"
done

javac -source 8 -target 8 -classpath "$CP" -d "$OUT/obj" @"$OUT/sources.txt"

echo "==> 5/7 dex"
mkdir -p "$OUT/androidx"
for j in libs/*/classes.jar libs/*.jar; do
  [ -e "$j" ] || continue
  d="$OUT/androidx/$(basename "$(dirname "$j")")"
  mkdir -p "$d"
  ( cd "$d" && unzip -oq "$(cd "$OLDPWD" && to_native "$j")" '*.class' 2>/dev/null || true )
done

find "$OUT/obj" "$OUT/androidx" -name '*.class' > "$OUT/classes.txt"
java -Xmx2g -cp "$(to_native "$D8_JAR")" com.android.tools.r8.D8 \
  --min-api 23 --lib "$(to_native "$PLATFORM_JAR")" \
  --output "$OUT/dex" @"$OUT/classes.txt"

echo "==> 6/7 package"
cp "$OUT/base.apk" "$OUT/unsigned.apk"
python3 tools/add_dex_assets.py "$OUT/unsigned.apk" "$OUT/dex/classes.dex" app/src/main/assets
"$(tool zipalign)" -f 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"

echo "==> 7/7 sign"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -v -keystore "$KEYSTORE" -alias "$KEY_ALIAS" \
    -keyalg RSA -keysize 2048 -validity 10000 \
    -storepass "$KEY_PASS" -keypass "$KEY_PASS" \
    -dname "CN=Android Debug,O=Android,C=US" >/dev/null 2>&1
fi
"$(tool apksigner)" sign \
  --ks "$KEYSTORE" --ks-key-alias "$KEY_ALIAS" \
  --ks-pass "pass:$KEY_PASS" --key-pass "pass:$KEY_PASS" \
  --out launcher.apk "$OUT/aligned.apk"

echo
echo "Built: $(pwd)/launcher.apk"
"$(tool aapt)" dump badging launcher.apk 2>/dev/null | head -1 || true
