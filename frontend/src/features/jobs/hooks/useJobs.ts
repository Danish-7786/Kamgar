import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { fetchJobById, fetchJobs, type JobsFilters } from "../api/jobsApi";

// Centralized query keys so mutations can invalidate them precisely.
export const jobKeys = {
  all: ["jobs"] as const,
  list: (filters: JobsFilters) => [...jobKeys.all, "list", filters] as const,
  detail: (id: number) => [...jobKeys.all, "detail", id] as const,
};

export function useJobs(filters: JobsFilters = { page: 1, page_size: 20 }) {
  return useQuery({
    queryKey: jobKeys.list(filters),
    queryFn: () => fetchJobs(filters),
    // Keep the previous page's rows on screen while the next page loads,
    // so the table doesn't flash empty on every page change.
    placeholderData: keepPreviousData,
  });
}

export function useJob(jobId: number) {
  return useQuery({
    queryKey: jobKeys.detail(jobId),
    queryFn: () => fetchJobById(jobId),
    enabled: Number.isFinite(jobId),
  });
}
