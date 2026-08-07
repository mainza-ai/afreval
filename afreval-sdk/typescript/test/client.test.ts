import { test } from "node:test";
import assert from "node:assert";
import { AfrevalClient } from "../src/client";

// Smoke test against a mock fetch: verifies the client shapes the request
// correctly and parses responses. No network, no live API.
test("certifyApi posts the request and parses the cert", async () => {
  const calls: Array<{ path: string; body: unknown }> = [];
  const client = new AfrevalClient("https://example.invalid", {
    fetch: (input, init) => {
      calls.push({ path: String(input), body: JSON.parse(String(init?.body)) });
      return Promise.resolve(
        new Response(
          JSON.stringify({
            model: "m1",
            context_score: 61.5,
            vectors: { linguistic_fidelity: 57.4, cultural_safety: 35.0, structural_economics: 62.8 },
            pass_: false,
            cert_sha256: "abc123",
            input_sources: { wer: "eval_baseline.py --from-qa (n=18)" },
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      );
    },
  });

  const cert = await client.certifyApi({
    model_id: "m1",
    tokenizer_candidate: "EfficientRouteCandidate",
    bias_corrected_judge_score: 35.0,
    auto_inputs: true,
  });

  assert.strictEqual(calls.length, 1);
  assert.strictEqual(calls[0].path, "https://example.invalid/v1/certify");
  assert.strictEqual(cert.context_score, 61.5);
  assert.strictEqual(cert.cert_sha256, "abc123");
  assert.strictEqual(cert.pass_, false);
});

test("securityReport gets /v1/security", async () => {
  const client = new AfrevalClient("https://example.invalid", {
    fetch: () =>
      Promise.resolve(
        new Response(JSON.stringify({ timestamp: "t", totalVariants: 31, totalBypasses: 0, perSeam: {} })),
      ),
  });
  const r = await client.securityReport();
  assert.strictEqual(r.totalVariants, 31);
});

test("compliance gets /v1/compliance", async () => {
  const client = new AfrevalClient("https://example.invalid", {
    fetch: () => Promise.resolve(new Response(JSON.stringify({ exit: 0, lines: [], current: true }))),
  });
  const r = await client.compliance();
  assert.strictEqual(r.current, true);
});
