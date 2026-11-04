#!/usr/bin/env bash
# Execute with: source scripts/env_camera_ubuntu2404.sh
# Environment for the libcamera 0.2.0 + Picamera2 0.3.17 setup tested on this Pi.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo 'Use: source scripts/env_camera_ubuntu2404.sh' >&2
    exit 2
fi

_followbot_project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
_followbot_camera_root=${FOLLOWBOT_LIBCAMERA_ROOT:-"$HOME/followbot-camera-check/runtime"}
_followbot_camera_lib="$_followbot_camera_root/lib/aarch64-linux-gnu"

if [[ ! -f "$_followbot_camera_lib/libcamera.so.0.2" ||
      ! -f "$_followbot_camera_lib/libcamera/ipa_rpi_vc4.so" ||
      ! -f "$_followbot_project/.venv/bin/activate" ]]; then
    echo 'Ambiente de câmera ainda não preparado. Consulte a seção 8 de INSTALL_TEST.md.' >&2
    unset _followbot_project _followbot_camera_root _followbot_camera_lib
    return 1
fi

source "$_followbot_project/.venv/bin/activate"
export LD_LIBRARY_PATH="$_followbot_camera_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBCAMERA_IPA_MODULE_PATH="$_followbot_camera_lib/libcamera"
export LIBCAMERA_IPA_PROXY_PATH="$_followbot_camera_root/libexec/libcamera"
export LIBCAMERA_IPA_CONFIG_PATH="$_followbot_camera_root/share/libcamera/ipa"
export PATH="$_followbot_camera_root/bin:$PATH"
unset _followbot_project _followbot_camera_root _followbot_camera_lib
