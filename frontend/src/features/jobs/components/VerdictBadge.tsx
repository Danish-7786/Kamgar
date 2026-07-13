import { Badge } from "@/components/ui/badge";
import type { Verdict } from "../types";

// Maps a scoring verdict to a badge variant. Falls back to "outline"
// for unknown/free-text verdicts coming from the AI scorer.
const VARIANT_BY_VERDICT: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
  "Strong Match": "default",
  "Partial Match": "secondary",
  Unknown: "outline",
};

export function VerdictBadge({ verdict }: { verdict: Verdict }) {
  const variant = VARIANT_BY_VERDICT[verdict] ?? "outline";
  return <Badge variant={variant}>{verdict}</Badge>;
}
