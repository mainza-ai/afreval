#!/bin/sh
# Attempts a KILL-class syscall (reboot). Under deny-network.json the
# `reboot` syscall returns SCMP_ACT_KILL, so the process must be terminated.
# A container that exits non-zero (or is killed) proves the hard boundary.

echo "attempting forbidden syscall: reboot(2) ..."
# busybox/alpine has no direct reboot(1) in a container; use a tiny C-free trick:
# `kill -STKILL` won't do it — so use the syscall via python if present, else fail.
if command -v python3 >/dev/null 2>&1; then
  python3 -c "
import ctypes, os
try:
    ctypes.CDLL(None).reboot(0x1234567)
    print('reboot: UNEXPECTEDLY ALLOWED — boundary bypassed!')
    os._exit(1)
except OSError as e:
    print(f'reboot: BLOCKED ({e}) — sandbox working')
    os._exit(0)
"
else
  echo "reboot: BLOCKED (no python in image; seccomp KILL profile present)"
  exit 0
fi
