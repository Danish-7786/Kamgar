import { apiClient } from "@/shared/api/axios";

// Platforms the backend accepts (must match ALLOWED_PLATFORMS in app.py).
export const PLATFORMS = [
  { id: "indeed", label: "Indeed" },
  { id: "linkedin", label: "LinkedIn" },
  { id: "google", label: "Google" },
  { id: "glassdoor", label: "Glassdoor" },
  { id: "zip_recruiter", label: "ZipRecruiter" },
  { id: "bayt", label: "Bayt" },
  { id: "naukri", label: "Naukri" },
  { id: "bdjobs", label: "BDJobs" },
] as const;

export type PlatformId = (typeof PLATFORMS)[number]["id"];

// Selected by default when the page loads.
export const DEFAULT_PLATFORMS: PlatformId[] = ["indeed", "linkedin", "google"];

export interface ScrapeResult {
  status: string;
  message: string;
  platforms?: string[];
}

export interface StatusResult {
  scraper: { is_running: boolean; [key: string]: unknown };
  database: "connected" | "disconnected";
}

export async function triggerScrape(platforms: PlatformId[]): Promise<ScrapeResult> {
  const { data } = await apiClient.post<ScrapeResult>("/scrape", { platforms });
  return data;
}

export async function fetchStatus(): Promise<StatusResult> {
  const { data } = await apiClient.get<StatusResult>("/status");
  return data;
}
