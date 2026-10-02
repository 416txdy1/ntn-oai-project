#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd -- "$(dirname -- "$0")/.." && pwd)
python3 "$ROOT/scripts/prepare_sources.py"
JOBS=${JOBS:-6}
PREFIX="$ROOT/.runtime/tools"
if [ ! -x "$PREFIX/bin/asn1c" ]; then
  ASN_SRC=$(find "$ROOT/.runtime/asn1c" -mindepth 1 -maxdepth 1 -type d | head -n 1)
  (cd "$ASN_SRC"; autoreconf -iv; ./configure --prefix="$PREFIX"; make -j "$JOBS"; make install)
fi
cmake -S "$ROOT/.runtime/oai" -B "$ROOT/.runtime/oai/cmake_targets/ran_build/build" -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo -DE2_AGENT=OFF -DENABLE_TESTS=OFF \
  -DASN1C_EXEC="$PREFIX/bin/asn1c" -DAUTO_DOWNLOAD_ASN1C=OFF \
  -DCMAKE_C_FLAGS="-I$ROOT/.runtime/simde" -DCMAKE_CXX_FLAGS="-I$ROOT/.runtime/simde"
cmake --build "$ROOT/.runtime/oai/cmake_targets/ran_build/build" \
  --target nr-softmodem nr-uesoftmodem rfsimulator params_libconfig -j "$JOBS"