# afreval-isolation — hardened sandbox tier (Podman/seccomp substitute)

The Docker-runnable standard tier for executing untrusted candidate models.
gVisor (`runsc`) and Firecracker require **KVM** — absent in Docker Desktop —
so this is the strongest **open-source, no-KVM** isolation available:

- A **strict seccomp profile** (`seccomp/deny-network.json`): network syscalls
  return `SCMP_ACT_ERRNO`, dangerous syscalls (`reboot`, `ptrace`, `mount`,
  `chroot`, `setns`, …) return `SCMP_ACT_KILL`, everything else allowed (so
  the container runtime's own init works).
- Applied per-workload via `docker run --security-opt seccomp=...` (or the
  identical `podman run` on a real Linux host).

This is a **shared-kernel, reduced-guarantee** tier vs gVisor — it layers
namespace/cgroup isolation (Docker/Podman) + syscall filtering (seccomp). It
is the strongest boundary without KVM; gVisor/Firecracker remain the
server-class target on real Linux hosts.

## Usage

```bash
./run_sandboxed.sh            # run the demo workload under the profile
./run_sandboxed.sh --verify   # assert compute-OK + network-BLOCKED
./run_sandboxed.sh --verify-kill  # assert a forbidden syscall is KILLed
```

## What it proves

- `workload/demo.sh` — normal computation + file IO succeed; a network
  connect is **denied** (ERRNO) → exit 0 with `network: BLOCKED`.
- `workload/forbidden.sh` — a `reboot(2)` attempt is **terminated**
  (`Bad system call`, SCMP_ACT_KILL).

## Verified 2026-08-05 (Docker Desktop, aarch64)

- `--verify`: **PASS** (compute allowed, network denied)
- `--verify-kill`: **PASS** (forbidden syscall terminated)

## Podman on a real host

```bash
podman run --rm --security-opt seccomp="$PWD/seccomp/deny-network.json" \
    -v "$PWD/workload:/workload:ro" alpine:3 sh /workload/demo.sh
```

## Layout

```
run_sandboxed.sh              # runner + verify
seccomp/deny-network.json     # the hardened profile (mutable artifact)
workload/demo.sh              # boundary demo (compute vs network)
workload/forbidden.sh         # KILL-class demo (reboot)
```

## Related
- [Isolation tiers](../wiki/infrastructure/isolation-tiers.md)
- [Zero-trust sandboxing](../wiki/concepts/zero-trust-sandboxing.md)
- [Gap analysis — E1](../wiki/build-plan/gap-analysis.md)
