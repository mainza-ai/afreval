// afreval-dashboard — renders state.json (produced by scripts/export_state.js).
fetch("state.json")
  .then((r) => r.json())
  .then(render)
  .catch((e) => {
    document.body.insertAdjacentHTML(
      "beforeend",
      `<p>state.json unavailable (${e.message}). Run: node scripts/export_state.js</p>`
    );
  });

function esc(s) {
  return String(s).replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" }[c]));
}

function render(state) {
  const certs = document.querySelector("#certs tbody");
  (state.certifications || []).forEach((c) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${esc(c.model)}</td>
      <td><strong>${c.context_score.toFixed(2)}</strong></td>
      <td>${c.vectors.linguistic_fidelity.toFixed(1)} / ${c.vectors.cultural_safety.toFixed(1)} / ${c.vectors.structural_economics.toFixed(1)}</td>
      <td class="${c.pass ? "pass" : "fail"}">${c.pass ? "PASS" : "FAIL"}</td>
      <td><code>${c.cert_sha256.slice(0, 16)}</code></td>`;
    certs.appendChild(row);
  });

  const seams = document.querySelector("#seams tbody");
  const sec = state.security || {};
  Object.entries(sec.per_seam || {}).forEach(([seam, s]) => {
    const pct = s.rate * 100;
    const row = document.createElement("tr");
    row.innerHTML = `<td>Seam ${esc(seam)}</td><td>${s.bypasses} / ${s.total}</td>
      <td>${pct.toFixed(1)}%</td>
      <td><div class="bar"><i class="${s.bypasses === 0 ? "zero" : ""}" style="width:${pct}%"></i></div></td>`;
    seams.appendChild(row);
  });
  document.querySelector("#security-meta").textContent = sec.timestamp
    ? `Last hardening-loop run: ${sec.timestamp} — ${sec.total_bypasses} bypasses across ${sec.total_variants} variants.`
    : "No security report yet (run afreval-airlock/attack/run_attack.js).";
}
