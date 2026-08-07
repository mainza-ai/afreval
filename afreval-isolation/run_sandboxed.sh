#!/usr/bin/env bash
# afreval-isolation — hardened sandbox runner (Podman/seccomp tier, 2026-08-05).
#
# gVisor/Firecracker need KVM (absent in Docker Desktop). This is the strongest
# Docker-compatible isolation: a strict seccomp profile (deny network + kill
# dangerous syscalls) applied via `docker run --security-opt seccomp=...`.
# On a real Linux host with Podman, use the same profile via podman (see below).
#
# Usage:
#   ./run_sandboxed.sh                 # run the demo workload under the profile
#   ./run_sandboxed.sh --verify        # assert compute-OK + network-BLOCKED
#
# Podman equivalent (real host):
#   podman run --rm --security-opt seccomp=seccomp/deny-network.json \
#       -v "$PWD/workload:/workload:ro" \
#       alpine:3 sh /workload/demo.sh

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PROFILE="$HERE/seccomp/deny-network.json"
IMAGE="${IMAGE:-alpine:3}"

run() {
  docker run --rm --security-opt seccomp="$PROFILE" \
    -v "$HERE/workload:/workload:ro" "$IMAGE" sh /workload/demo.sh
}

if [ "${1:-}" = "--verify" ]; then
  out="$(run 2>&1 || true)"
  echo "$out"
  echo "--- verify ---"
  if echo "$out" | grep -q "compute: OK" && echo "$out" | grep -q "network: BLOCKED"; then
    echo "PASS: compute allowed, network denied by seccomp"
    exit 0
  else
    echo "FAIL: boundary not enforced"
    exit 1
  fi
elif [ "${1:-}" = "--verify-kill" ]; then
  # A KILL-class syscall (reboot) must terminate the process.
  echo "--- kill-boundary check ---"
  out="$(docker run --rm --security-opt seccomp="$PROFILE" \
      -v "$HERE/workload:/workload:ro" python:3.12-alpine sh /workload/forbidden.sh 2>&1 || true)"
  echo "$out"
  if echo "$out" | grep -q "Bad system call"; then
    echo "PASS: forbidden syscall terminated (SCMP_ACT_KILL)"
    exit 0
  else
    echo "FAIL: forbidden syscall not killed"
    exit 1
  fi
else
  run
fi
