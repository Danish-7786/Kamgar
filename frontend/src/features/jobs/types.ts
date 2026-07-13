// Mirrors the `jobs` table / API response shape from the FastAPI backend.
export type Verdict = "Strong Match" | "Partial Match" | "Unknown" | string;

export interface Job {
  id: number;
  title: string;
  company: string;
  link: string;
  description: string;
  date_posted:string | null,
  ai_score: number;
  verdict: Verdict;
  missing_skills: string[];
  red_flags: string[];
  created_at: string;
}
