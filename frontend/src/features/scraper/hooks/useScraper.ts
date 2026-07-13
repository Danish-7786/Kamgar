import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobKeys } from "@/features/jobs/hooks/useJobs";
import { fetchStatus, triggerScrape } from "../api/scraperApi";

// Triggers a background scrape; on success, invalidates the jobs cache
// so any mounted jobs list refetches automatically.
export function useTriggerScrape() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: triggerScrape,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: jobKeys.all });
    },
  });
}

// Polls /status. Refetches every 5s while a scrape is running so the UI
// reflects progress without manual refresh.
export function useStatus() {
  return useQuery({
    queryKey: ["status"],
    queryFn: fetchStatus,
    refetchInterval: (query) =>
      query.state.data?.scraper.is_running ? 5_000 : false,
  });
}
