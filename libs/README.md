# Prebuilt dependency jars

The build does not use Gradle, so the AndroidX artifacts are unpacked here.
Each `.aar` is a zip; `classes.jar` inside it is what the build reads.

Versions are pinned deliberately:

| Library | Version | Why this version |
|---|---|---|
| androidx.recyclerview | **1.2.1** | 1.3.x pulls in `androidx.customview:customview-poolingcontainer`, which is a separate artifact this build would also have to unpack. 1.2.1 has no such dependency. |
| androidx.dynamicanimation | 1.0.0 | Spring animations; unchanged since 2019. |
| androidx.core | 1.12.0 | Last release that does not require compileSdk 34+. |
| androidx.customview | 1.1.0 | Needed by recyclerview 1.2.1. |
| androidx.annotation | 1.3.0 | **Must be a plain jar** — 1.7.x is a Kotlin Multiplatform artifact with no `.class` files, so javac cannot read it. |
| androidx.collection | 1.2.0 | Plain jar, needed by core. |

## Fetching them

```bash
BASE=https://dl.google.com/dl/android/maven2/androidx

fetch() {  # $1=path  $2=name
  curl -sLO "$BASE/$1"
  mkdir -p "$2"
  python3 -c "import zipfile,sys; z=zipfile.ZipFile(sys.argv[1]); open(sys.argv[2]+'/classes.jar','wb').write(z.read('classes.jar'))" \
    "$(basename "$1")" "$2"
}

fetch recyclerview/recyclerview/1.2.1/recyclerview-1.2.1.aar       recyclerview-1.2.1
fetch dynamicanimation/dynamicanimation/1.0.0/dynamicanimation-1.0.0.aar dynamicanimation-1.0.0
fetch core/core/1.12.0/core-1.12.0.aar                             core-1.12.0
fetch customview/customview/1.1.0/customview-1.1.0.aar             customview-1.1.0

curl -sLO "$BASE/annotation/annotation/1.3.0/annotation-1.3.0.jar"
curl -sLO "$BASE/collection/collection/1.2.0/collection-1.2.0.jar"
```

If you replace recyclerview with 1.3.x, you also need
`androidx.customview:customview:1.2.0` and its `customview-poolingcontainer`
dependency unpacked the same way, or the app fails at inflate time with
`ClassNotFoundException: androidx.customview.poolingcontainer.PoolingContainer`.
