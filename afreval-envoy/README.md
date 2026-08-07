# afreval-envoy — credential-injection sidecar (Phase E1)

The Docker-testable part of the **Envoy credential-injection tier** from
[isolation-tiers](../wiki/infrastructure/isolation-tiers.md): "synthetic
enterprise credentials for tool-use testing are injected dynamically at
request time via an Envoy sidecar — never passed directly to the agent under
test."

## What it does

An Envoy HTTP proxy sits between the agent-under-test and the upstream tool
service. On every request it injects:

- `X-AfrEval-Synthetic-Cred` — the synthetic credential
- `X-AfrEval-Credential-Hint: injected-by-envoy-sidecar`

The agent never holds the credential; it is added at the boundary, exactly
the §4 credential-handling rule. (Production replaces the static demo value
with a real credential broker / vault — Stronghold post-MVP.)

## Run

```bash
docker compose -f afreval-envoy/compose.yml up -d --build
```

## Verify

```bash
curl -s http://localhost:10000/
# injected-headers
# x-afreval-synthetic-cred: synd-8f3k2h9q-waxal-net
# x-afreval-credential-hint: injected-by-envoy-sidecar
```

The `cred_service` echo server prints the headers it received, proving the
injection happened in Envoy before the upstream saw the request.

## Layout

```
envoy.yaml        # Envoy config: HCM + header_mutation filter -> cred_service
compose.yml       # cred_service (echo) + envoy (:10000 -> :9000)
echo_server.py    # upstream echo service (prints injected headers)
Dockerfile.echo
```

## Verified 2026-08-05

- Envoy `v1.32.13` on Docker Desktop (aarch64) — up, config valid, seam live.
- Schema notes: filter type `envoy.extensions.filters.http.header_mutation.v3.HeaderMutation`,
  each `request_mutation` is `{ append: { header: { key, value } } }`; the
  `%ENV()%` substitution is NOT supported in header values (static value used).
- gVisor (runsc) and Firecracker are NOT feasible in Docker Desktop (no KVM);
  those tiers remain server-class only.
