# afreval-field-app

Dart/Flutter field data-collection app for the WAXAL-NET loop (§3.4).
Collects **image-prompted spontaneous speech** in the field (matching WAXAL's
own elicitation methodology) and reports on-device eval telemetry.

Builds **in parallel** with the training loop — it depends only on the WAXAL
elicitation methodology being nailed down, not on training finishing.

## Build & test status — verified in Docker (2026-08-05)

The scaffold is now **compile-verified and tested** via the official Flutter
container (no host Flutter SDK needed):

```bash
docker run --rm -v "$PWD/afreval-field-app:/app" -w /app \
  ghcr.io/cirruslabs/flutter:3.32.5 flutter test
docker run --rm -v "$PWD/afreval-field-app:/app" -w /app \
  ghcr.io/cirruslabs/flutter:3.32.5 flutter analyze
```

Result: **`flutter analyze` clean, all 5 tests pass** (`test/telemetry_test.dart`
verifies the on-device WER semantics + telemetry queue). Note: the
`flutter:stable` (3.44.0) image has a broken `vector_math`/`star_border` SDK
compile path in the container; **use the `3.32.5` tag**.

## Spec (from §3.4 / WAXAL methodology)

- **Elicitation screen**: show the speaker an image; record their spoken
  description; capture ≥15s clips with speaker age/gender/language/environment
  metadata.
- **On-device eval telemetry**: run the deployed edge ASR on-device, compute
  WER/CER (`harness/waxal_eval` semantics), and report results (queued,
  upload-on-connect) so field conditions ground the eval.
- Local-first: recordings + telemetry are stored on-device until a network
  sync (air-gapped friendly).

## Layout

```
lib/main.dart              # app entry — ties elicitation + telemetry
lib/elicitation_screen.dart  # image prompt -> record -> metadata
lib/telemetry.dart         # on-device WER/CER eval + queued reporting
pubspec.yaml
```

## Related

- [WAXAL-NET subsystem](../wiki/subsystems/waxal-net.md)
- [WAXAL methodology](../wiki/substrates/waxal.md)
- [Phases — Phase 4](../wiki/build-plan/phases.md)
