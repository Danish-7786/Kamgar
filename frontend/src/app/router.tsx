import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "./AppLayout";
import { JobsPage } from "../features/jobs/pages/JobsPage";
import { ScraperPage } from "../features/scraper/pages/ScraperPage";

// Central route table. Each feature owns its pages; the router just wires them in.
export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/jobs" replace /> },
      { path: "jobs", element: <JobsPage /> },
      { path: "scraper", element: <ScraperPage /> },
    ],
  },
]);
