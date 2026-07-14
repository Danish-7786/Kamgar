import { apiClient } from "@/shared/api/axios";
import type { Job, Verdict } from "../types";

// Query params accepted by GET /jobs.
export interface JobsFilters {
  min_score?: number;
  verdict?: Verdict;
  page: number;

  page_size: number;
  sort_by?: string;
}

// Backend wraps the paginated payload in this envelope.
interface JobsResponse {
  status: string;
  total_count: number;
  pages: number;
  page: number;
  page_size: number;
  data: Job[];
}

interface JobResponse {
  status: string;
  data: Job;
}

// What the app actually consumes: the jobs plus pagination metadata.
export interface PaginatedJobs {
  jobs: Job[];
  total: number;
  pages: number;
  page: number;
  pageSize: number;
}

export async function fetchJobs(filters: JobsFilters = { page: 1, page_size: 20 }): Promise<PaginatedJobs> {
  const { data } = await apiClient.get<JobsResponse>("/jobs", { params: filters });
  console.log(data);
  
  return {
    jobs: data.data,
    total: data.total_count,
    pages: data.pages,
    page: data.page,
    pageSize: data.page_size,
  };
}

export async function fetchJobById(jobId: number): Promise<Job> {
  const { data } = await apiClient.get<JobResponse>(`/job/${jobId}`);
  return data.data;
}
