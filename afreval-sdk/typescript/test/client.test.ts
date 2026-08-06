import { test } from "node:test";
import assert from "node:assert";
import { AfrevalClient } from "../src/client";

// Smoke test against a mock fetch: verifies the client shapes the request
// correctly and parses responses. No network, no live API.
test("certify posts the request and parses the cert", async () => {
  const calls: Array<{ path: string; body: unknown }> = [];
  const client = new AfrevalClient("https://example.invalid", {
    fetch: (input, init) => {
      calls.push({ path: String(input), body: JSON.parse(String(init?.body)) });
      return Promise.resolve(
        new Response(
          JSON.stringify({
            modelId: "m1",
            vertical: "telco",
            contextScore: 61.5,
            linguisticFidelity: 57.4,
            culturalSafety: 35.0,
            structuralEconomics: 62.8,
            pass: false,
            certSha256: "abc123",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
      );
    },
  });

  const cert = await client.certify({
    modelId: "m1",
    waxalMacroWer: 0.4097,
    afrobenchLiteAccuracy: 0.55,
    biasCorrectedJudgeScore: 35.0,
    meanFertilityPremium: 1.59,
    harnessPins: { afri_fertility_pin: "p", afrobench_lite_pin: "p", waxal_pin: "p" },
    weightsYaml: "vertical: telco\n",
  });

  assert.strictEqual(calls.length, 1);
  assert.strictEqual(calls[0].path, "https://example.invalid/v1/certify");
  assert.strictEqual(cert.contextScore, 61.5);
  assert.strictEqual(cert.certSha256, "abc123");
  assert.strictEqual(cert.pass, false);
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
