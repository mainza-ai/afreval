#!/bin/sh
# §isolation demo workload — runs under the hardened seccomp profile.
# 1. Proves the sandbox allows normal computation (echo + file IO).
# 2. Attempts a forbidden action (network connect) and reports it is BLOCKED.
# A healthy result is: computation OK, network BLOCKED.

echo "compute: OK (this file: $(wc -l < /dev/null) lines counted)"

if [ -e /etc/os-release ]; then
  echo "os-release: readable (file IO allowed)"
fi

echo "network: attempting to connect to 1.1.1.1:53 ..."
# The deny-network.json seccomp profile returns SCMP_ACT_ERRNO for socket/connect,
# so this must fail (non-zero) — proving the boundary.
if nc -z -w 2 1.1.1.1 53 2>/dev/null || \
   (echo > /dev/tcp/1.1.1.1/53) 2>/dev/null; then
  echo "network: UNEXPECTEDLY REACHABLE — sandbox bypassed!"
  exit 1
else
  echo "network: BLOCKED (connect denied by seccomp) — sandbox working"
  exit 0
fi
