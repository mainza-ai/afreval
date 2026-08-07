// §3.4 on-device telemetry WER tests — verify the local scoring semantics
// match the harness before the app is field-built (Docker build 2026-08-05).
import 'package:flutter_test/flutter_test.dart';

import 'package:afreval_field_app/telemetry.dart';

void main() {
  test('wer: exact match is 0.0', () {
    expect(wer('mama anasema habari', 'mama anasema habari'), 0.0);
  });

  test('wer: empty reference handles gracefully', () {
    expect(wer('', ''), 0.0);
    expect(wer('', 'mama'), 1.0);
  });

  test('wer: one word error is 1/3', () {
    expect(wer('mama anasema habari', 'mama anasema jambo'), closeTo(1 / 3, 1e-9));
  });

  test('wer: full deletion is 1.0', () {
    expect(wer('mama anasema', ''), 1.0);
  });

  test('telemetry queues and syncs', () async {
    final t = OnDeviceTelemetry();
    t.record(clipId: 'c1', language: 'swa', reference: 'a b', hypothesis: 'a b');
    t.record(clipId: 'c2', language: 'swa', reference: 'a b', hypothesis: 'a');
    expect(t.pendingCount, 2);
    await t.sync();
    expect(t.pendingCount, 0);
  });
}
