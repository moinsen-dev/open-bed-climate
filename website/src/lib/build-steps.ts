// Build-guide navigation helpers (pure, so pages and tests agree).
export interface StepRef { id: string; title: string; n: number }

/** "Step 3: Power path" → "Power path". */
export const stepTitle = (h1: string) => h1.replace(/^Step\s+\d+\s*[:.–-]\s*/i, "").trim();

export const firstHeading = (body: string | undefined, fallback: string) => /^#\s+(.+)$/m.exec(body ?? "")?.[1]?.trim() ?? fallback;

export function orderSteps(entries: { id: string; body?: string }[]): StepRef[] {
  return entries
    .filter((e) => /^\d{2}-/.test(e.id))
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((e, i) => ({ id: e.id, n: i + 1, title: stepTitle(firstHeading(e.body, e.id)) }));
}
