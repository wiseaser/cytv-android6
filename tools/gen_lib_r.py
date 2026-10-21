#!/usr/bin/env python3
"""Generate R.java for each AndroidX AAR.

The AndroidX jars in libs/ ship no R class of their own: a Gradle build generates one
per library at package time. Building without Gradle means doing it here.

Each library's R.txt lists the resource names it references. The ids themselves come
from the app's own R.java (which aapt2 produced after the library resources were
merged into app/src/main/res). Names the app does not define fall back to 0.
"""

import os
import re
import sys
import zipfile

LIBS = "libs"
MAIN_R = "build/gen/com/gathin/tvhome/R.java"
OUT = "build/libgen"

# library directory -> Java package of its R class
PACKAGES = {
    "recyclerview": "androidx.recyclerview",
    "core": "androidx.core",
    "customview": "androidx.customview",
    "dynamicanimation": "androidx.dynamicanimation",
}


def read_main_r(path):
    """Return ({kind: {name: hex}}, {(kind, name): [array values]})."""
    ids, arrays = {}, {}
    if not os.path.exists(path):
        return ids, arrays

    lines = open(path, encoding="utf-8").read().splitlines()
    current = None
    i = 0
    while i < len(lines):
        line = lines[i]

        m = re.match(r"\s*public static final class (\w+) \{", line)
        if m:
            current = m.group(1)

        m = re.match(r"\s*public static final int (\w+)\s*=\s*(0x[0-9a-fA-F]+);", line)
        if m and current:
            ids.setdefault(current, {})[m.group(1)] = m.group(2)

        # Arrays may span several lines: int[] Name={ 0x.., 0x.. };
        m = re.match(r"\s*public static final int\[\]\s+(\w+)\s*=\s*\{(.*)$", line)
        if m and current:
            name, buf = m.group(1), m.group(2)
            j = i
            while "};" not in buf and j + 1 < len(lines):
                j += 1
                buf += lines[j]
            arrays[(current, name)] = re.findall(r"0x[0-9a-fA-F]+", buf)
            i = j

        i += 1

    return ids, arrays


def find_source(lib):
    """Locate a library's R.txt.

    Accepts either an .aar still in libs/ (R.txt sits inside the zip) or the unpacked
    layout libs/<lib>-<version>/classes.jar, in which case R.txt must sit next to the jar.
    """
    for name in sorted(os.listdir(LIBS)):
        path = os.path.join(LIBS, name)
        if name.startswith(lib) and name.endswith(".aar"):
            return ("aar", path)
        if os.path.isdir(path) and name.startswith(lib):
            for candidate in ("R.txt", "classes.jar"):
                if os.path.exists(os.path.join(path, candidate)):
                    return ("dir", path)
    return (None, None)


def read_r_txt(kind, path, lib):
    if kind == "aar":
        with zipfile.ZipFile(path) as z:
            if "R.txt" not in z.namelist():
                return None
            return z.read("R.txt").decode("utf-8")

    # Unpacked layout: prefer R.txt, otherwise read it back out of the jar next to it.
    txt = os.path.join(path, "R.txt")
    if os.path.exists(txt):
        return open(txt, encoding="utf-8").read()

    jar = os.path.join(path, "classes.jar")
    if os.path.exists(jar):
        with zipfile.ZipFile(jar) as z:
            for entry in ("R.txt", "META-INF/R.txt"):
                if entry in z.namelist():
                    return z.read(entry).decode("utf-8")
    print(f"    {lib}: no R.txt found next to classes.jar")
    return None


def main():
    ids, arrays = read_main_r(MAIN_R)
    total = sum(len(v) for v in ids.values())
    print(f"    main R: {total} ids, {len(arrays)} arrays")

    for lib, package in PACKAGES.items():
        kind, path = find_source(lib)
        if not path:
            print(f"    {lib}: not found, skipped")
            continue

        rtxt = read_r_txt(kind, path, lib)
        if rtxt is None:
            continue

        kinds, groups = {}, {}
        for line in rtxt.splitlines():
            parts = line.split()
            if len(parts) >= 4 and parts[0] == "int":
                kind, name = parts[1], parts[2]
                kinds.setdefault(kind, []).append(name)
                if kind == "styleable" and "_" in name:
                    groups.setdefault(name.split("_")[0], []).append(name)

        out = [f"package {package};", "", "public final class R {"]
        for kind in sorted(kinds):
            out.append(f"    public static final class {kind} {{")
            for name in sorted(set(kinds[kind])):
                if kind == "styleable" and "_" not in name:
                    continue
                value = ids.get(kind, {}).get(name, "0x0")
                out.append(f"        public static final int {name} = {value};")
            if kind == "styleable":
                for group in sorted(groups):
                    values = arrays.get(("styleable", group))
                    body = ", ".join(values) if values else ""
                    out.append(f"        public static final int[] {group} = {{ {body} }};")
            out.append("    }")
        out.append("}")

        target = os.path.join(OUT, *package.split("."))
        os.makedirs(target, exist_ok=True)
        with open(os.path.join(target, "R.java"), "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        print(f"    {lib}: {len(kinds)} kinds")


if __name__ == "__main__":
    sys.exit(main())
