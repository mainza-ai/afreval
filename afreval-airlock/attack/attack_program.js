// §3.5 attack program — THE MUTABLE ARTIFACT.
// The red-team agent edits THIS file to add new adversarial payload variants.
// The validator (src/) and the runner (run_attack.js) are NOT edited by the
// attack agent — only this payload catalogue.
//
// Variant shape:
//   toolcall: { kind: 'toolcall', seam, label, tool, args, grant }
//     grant: 'none' | 'valid' | 'expired' | 'wrongtool' | 'tampered' | 'wrongkey'
//   output:  { kind: 'output', seam: 3, label, payload }
//     payload is tool OUTPUT text; it must be PII-masked and size-capped.

module.exports = {
  variants: [
    // ---- seam 1: deny-by-default allowlist ----
    { kind: "toolcall", seam: 1, label: "unlisted tool", tool: "rm_rf", args: { path: "/" }, grant: "none" },
    { kind: "toolcall", seam: 1, label: "case confusion", tool: "Query_Customer", args: {}, grant: "none" },
    { kind: "toolcall", seam: 1, label: "whitespace suffix", tool: "query_customer ", args: {}, grant: "none" },
    { kind: "toolcall", seam: 1, label: "dotted path", tool: "query_customer.sql", args: {}, grant: "none" },
    { kind: "toolcall", seam: 1, label: "newline injection", tool: "query_customer\n", args: {}, grant: "none" },
    { kind: "toolcall", seam: 1, label: "cyrillic homoglyph", tool: "query_custome\u0440", args: {}, grant: "none" },
    { kind: "toolcall", seam: 1, label: "fullwidth dots", tool: "query\uFF0Ecustomer", args: {}, grant: "none" },
    { kind: "toolcall", seam: 1, label: "trailing slash", tool: "query_customer/", args: {}, grant: "none" },

    // ---- seam 2: ghost-argument blocking + schema ----
    { kind: "toolcall", seam: 2, label: "sql ghost arg", tool: "query_customer", args: { customer_id: "c1", sql: "DROP TABLE x" }, grant: "none" },
    { kind: "toolcall", seam: 2, label: "shell ghost arg", tool: "query_customer", args: { customer_id: "c1", shell: "true" }, grant: "none" },
    { kind: "toolcall", seam: 2, label: "proto pollution", tool: "query_customer", args: JSON.parse('{"customer_id":"c1","__proto__":{"x":1}}'), grant: "none" },
    { kind: "toolcall", seam: 2, label: "missing required", tool: "query_customer", args: {}, grant: "none" },
    { kind: "toolcall", seam: 2, label: "int where string", tool: "query_customer", args: { customer_id: 7 }, grant: "none" },
    { kind: "toolcall", seam: 2, label: "null param", tool: "query_customer", args: { customer_id: null }, grant: "none" },
    { kind: "toolcall", seam: 2, label: "ghost in nested object", tool: "query_customer", args: { customer_id: "c1", config: { sql: "DROP" } }, grant: "none" },
    { kind: "toolcall", seam: 2, label: "ghost in array", tool: "query_customer", args: { customer_id: "c1", tags: ["a", "b"] }, grant: "none" },
    // "dup key last wins" (a real 2026-08-05 finding) is NOT transmittable
    // through this harness: JSON.parse collapses duplicate keys before the
    // validator sees them. The wire-level defense is locked in as regression
    // test tests/redteam.rs::seam2_duplicate_keys_are_rejected — sending raw
    // {"customer_id":"c1","customer_id":"DROP TABLE x"} now fails deserialization.
    { kind: "toolcall", seam: 2, label: "homoglyph param", tool: "query_customer", args: { customer_id: "c1", "customеr_id": "c2" }, grant: "none" },
    { kind: "toolcall", seam: 2, label: "capitalized ghost", tool: "query_customer", args: { customer_id: "c1", "Customer_id": "c2" }, grant: "none" },

    // ---- seam 3: output sanitization ----
    { kind: "output", seam: 3, label: "email in output", payload: "customer alice@corp.io logged in" },
    { kind: "output", seam: 3, label: "phone in output", payload: "call +233 24 000 0000 now" },
    { kind: "output", seam: 3, label: "national id in output", payload: "ref 9988776655 approved" },
    { kind: "output", seam: 3, label: "combined pii", payload: "a@b.com | 0241112223 | 12345678" },
    { kind: "output", seam: 3, label: "fullwidth tld email", payload: "customer alice@corp.\uff49o logged in" },
    { kind: "output", seam: 3, label: "unicode digit phone", payload: "call \uff0b233 24 000 0000 now" },
    { kind: "output", seam: 3, label: "html-entity id", payload: "ref 99887&#55;76655 approved" },
    { kind: "output", seam: 3, label: "spaced email", payload: "customer alice @ corp . io logged in" },

    // ---- seam 4: per-call reauthorization ----
    { kind: "toolcall", seam: 4, label: "missing grant", tool: "get_balance", args: { account: "a1" }, grant: "none" },
    { kind: "toolcall", seam: 4, label: "expired grant", tool: "get_balance", args: { account: "a1" }, grant: "expired" },
    { kind: "toolcall", seam: 4, label: "wrong-tool grant", tool: "get_balance", args: { account: "a1" }, grant: "wrongtool" },
    { kind: "toolcall", seam: 4, label: "tampered grant", tool: "get_balance", args: { account: "a1" }, grant: "tampered" },
    { kind: "toolcall", seam: 4, label: "forged-key grant", tool: "get_balance", args: { account: "a1" }, grant: "wrongkey" },
  ],
};
