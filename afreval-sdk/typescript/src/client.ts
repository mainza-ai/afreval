// Client API shape for the AfrEval SaaS surface (not yet live — Phase 5).
// Mirrors the Python SDK: certify / score / securityReport.

export interface HarnessPins {
  afri_fertility_pin: string;
  afrobench_lite_pin: string;
  waxal_pin: string;
}

export interface CertRequest {
  modelId: string;
  waxalMacroWer: number;
  afrobenchLiteAccuracy: number;
  biasCorrectedJudgeScore: number;
  meanFertilityPremium: number;
  harnessPins: HarnessPins;
  weightsYaml: string;
}

export interface Cert {
  modelId: string;
  vertical: string;
  contextScore: number;
  linguisticFidelity: number;
  culturalSafety: number;
  structuralEconomics: number;
  pass: boolean;
  certSha256: string;
}

export interface SecurityReport {
  timestamp: string;
  totalVariants: number;
  totalBypasses: number;
  perSeam: Record<string, { total: number; bypasses: number; rate: number }>;
}

export class AfrevalClient {
  constructor(private readonly baseUrl: string) {}

  async certify(req: CertRequest): Promise<Cert> {
    return this.post("/v1/certify", req);
  }

  async securityReport(): Promise<SecurityReport> {
    return this.get("/v1/security");
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    const r = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    return r.json() as Promise<T>;
  }

  private async get<T>(path: string): Promise<T> {
    const r = await fetch(`${this.baseUrl}${path}`);
    return r.json() as Promise<T>;
  }
}
