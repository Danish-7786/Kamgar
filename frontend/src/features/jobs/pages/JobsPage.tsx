import { useState } from "react";
import { JobCard } from "../components/JobCard";
import { useJobs } from "../hooks/useJobs";
import { JobsPagination } from "../components/Pagination";

const PAGE_SIZE = 20;

export function JobsPage() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError, error, isPlaceholderData } = useJobs({
    page,
    page_size: PAGE_SIZE,
  });

  const jobs = data?.jobs ?? [];
  const totalPages = data?.pages ?? 1;

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Jobs</h2>
        <p className="text-sm text-muted-foreground">
          Scored postings from the scraper.
        </p>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Loading jobs…</p>}

      {isError && (
        <p className="text-sm text-destructive">
          Failed to load jobs: {error instanceof Error ? error.message : "Unknown error"}
        </p>
      )}

      {data && jobs.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No jobs yet — run the scraper to populate results.
        </p>
      )}

      {jobs.length > 0 && (
        <>
          <div className="flex flex-col gap-4">
            {jobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>

          {/* <div className="rounded-lg border">
            <JobsTable jobs={jobs} />
          </div> */}

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Page {page} of {totalPages}
              {data ? ` · ${data.total} total` : ""}
            </p>

            <JobsPagination
              page={page}
              totalPages={totalPages}
              onPageChange={setPage}
              disabled={isPlaceholderData}
            />
          </div>
        </>
      )}
    </section>
  );
}
