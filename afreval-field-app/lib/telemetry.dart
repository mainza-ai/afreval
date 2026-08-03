// §3.4 on-device eval telemetry — local WER/CER scoring + queued reporting.
// Field conditions ground the eval; results are queued on-device and synced
// when a network is available (air-gapped friendly). Spec scaffold.

import 'dart:collection';

/// Minimal deterministic WER (word error rate). Mirrors the harness semantics.
double wer(String reference, String hypothesis) {
  final ref = reference.trim().split(RegExp(r'\s+'));
  final hyp = hypothesis.trim().split(RegExp(r'\s+'));
  if (ref.isEmpty) return hyp.isEmpty ? 0.0 : 1.0;
  final d = List.generate(ref.length + 1, (i) => List.filled(hyp.length + 1, 0));
  for (var i = 0; i <= ref.length; i++) d[i][0] = i;
  for (var j = 0; j <= hyp.length; j++) d[0][j] = j;
  for (var i = 1; i <= ref.length; i++) {
    for (var j = 1; j <= hyp.length; j++) {
      d[i][j] = [
        d[i - 1][j] + 1,
        d[i][j - 1] + 1,
        d[i - 1][j - 1] + (ref[i - 1] == hyp[j - 1] ? 0 : 1),
      ].reduce((a, b) => a < b ? a : b);
    }
  }
  return d[ref.length][hyp.length] / ref.length;
}

class EvalSample {
  EvalSample({required this.clipId, required this.language, required this.wer});
  final String clipId;
  final String language;
  final double wer;
}

class OnDeviceTelemetry {
  final Queue<EvalSample> _pending = Queue();

  void record({required String clipId, required String language, required String reference, required String hypothesis}) {
    _pending.add(EvalSample(clipId: clipId, language: language, wer: wer(reference, hypothesis)));
  }

  int get pendingCount => _pending.length;

  /// Upload-on-connect placeholder; clears the queue once synced.
  Future<void> sync() async {
    // wire to the AfrEval reporting endpoint when available.
    _pending.clear();
  }
}
