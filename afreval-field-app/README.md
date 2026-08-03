# afreval-field-app

Dart/Flutter field data-collection app for the WAXAL-NET loop (§3.4).
Collects **image-prompted spontaneous speech** in the field (matching WAXAL's
own elicitation methodology) and reports on-device eval telemetry.

Builds **in parallel** with the training loop — it depends only on the WAXAL
elicitation methodology being nailed down, not on training finishing.

> Requires the Flutter SDK to build/run (not installed on this machine yet).
> The structure below is the spec; compile once Flutter is available.

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
