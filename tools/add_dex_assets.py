#!/usr/bin/env python3
"""Add classes.dex and the assets tree to a linked resource APK.

aapt2 produces an APK that contains only resources; javac/d8 produce the dex. This
puts them together without needing a zip binary, which is not always available.

Usage: add_dex_assets.py <apk> <dex> <assets-dir>
"""

import os
import sys
import zipfile


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2

    apk, dex, assets_dir = argv[1], argv[2], argv[3]

    with zipfile.ZipFile(apk, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(dex, "classes.dex")

        if os.path.isdir(assets_dir):
            for root, _dirs, files in os.walk(assets_dir):
                for name in files:
                    path = os.path.join(root, name)
                    rel = os.path.relpath(path, assets_dir).replace(os.sep, "/")
                    z.write(path, "assets/" + rel)

    with zipfile.ZipFile(apk) as z:
        entries = z.namelist()

    for required in ("classes.dex", "AndroidManifest.xml", "resources.arsc"):
        if required not in entries:
            print(f"error: {required} missing from {apk}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
