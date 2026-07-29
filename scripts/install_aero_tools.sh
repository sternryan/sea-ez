#!/bin/bash
# Idempotent installer for the sea-ez aero lane (darwin arm64).
# OpenVSP 3.51.2 ARM64 + bundled py3.13 API, XFOIL 6.97 from source.
# Everything lands in tools/ (gitignored). Re-run safely anytime.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p tools && cd tools

VSP_ZIP="openvsp-3.51.2-arm64-py313.zip"
VSP_URL="https://openvsp.org/download.php?file=zips/current/mac/OpenVSP-3.51.2-macos-14-ARM64-Python3.13.zip"
[ -d OpenVSP-3.51.2-MacOS ] || {
  [ -f "$VSP_ZIP" ] || curl -sL -o "$VSP_ZIP" "$VSP_URL"
  unzip -q "$VSP_ZIP"
}

command -v python3.13 >/dev/null || { echo "need brew python@3.13"; exit 1; }
command -v gfortran   >/dev/null || { echo "need brew gcc"; exit 1; }
command -v cmake      >/dev/null || { echo "need brew cmake"; exit 1; }

[ -d venv313 ] || python3.13 -m venv venv313
# Bundled sibling packages are NOT on PyPI; install in dependency order.
./venv313/bin/pip -q install \
  ./OpenVSP-3.51.2-MacOS/python/degen_geom \
  ./OpenVSP-3.51.2-MacOS/python/utilities \
  ./OpenVSP-3.51.2-MacOS/python/openvsp_config \
  ./OpenVSP-3.51.2-MacOS/python/openvsp
./venv313/bin/pip -q install pytest  # required by `make aero-test`

[ -d xfoil-src ] || git clone -q --depth 1 https://github.com/RobotLocomotion/xfoil.git xfoil-src
[ -x xfoil-src/build/src/xfoil ] || {
  mkdir -p xfoil-src/build && cd xfoil-src/build
  cmake .. -DCMAKE_BUILD_TYPE=Release >/dev/null && make -j8 >/dev/null
  cd ../..
}

./venv313/bin/python -c "import openvsp as v; print('openvsp', v.GetVSPVersion())"
[ -x xfoil-src/build/src/xfoil ] && echo "xfoil OK"
echo "aero tools ready"
