import { QueryClient } from "@tanstack/react-query";

// App-wide query client. Tune defaults here as the app grows.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // 30s before refetch on remount/focus
      retry: 1,
    },
  },
});
