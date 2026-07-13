import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Job } from "../types";

// Tints the whole card by match score: green (great) → orange (borderline)
// → red (poor), getting redder the lower a sub-50 score is.
function scoreCardClasses(score: number): string {
  if (score >= 80) return "bg-green-100 border-green-500 dark:bg-green-950/50 dark:border-green-700";
  if (score >= 70) return "bg-green-50 border-green-300 dark:bg-green-950/30 dark:border-green-800";
  if (score >= 60) return "bg-orange-100 border-orange-400 dark:bg-orange-950/50 dark:border-orange-700";
  if (score >= 50) return "bg-orange-50 border-orange-300 dark:bg-orange-950/30 dark:border-orange-800";
  if (score >= 40) return "bg-red-50 border-red-300 dark:bg-red-950/30 dark:border-red-900";
  if (score >= 30) return "bg-red-100 border-red-400 dark:bg-red-950/50 dark:border-red-800";
  return "bg-red-200 border-red-500 dark:bg-red-950/70 dark:border-red-700";
}

// Matching color for the score text so it pops against the card tint.
function scoreTextClasses(score: number): string {
  if (score >= 70) return "text-green-700 dark:text-green-400";
  if (score >= 50) return "text-orange-600 dark:text-orange-400";
  return "text-red-700 dark:text-red-400";
}

export function JobCard({ job }: { job: Job }) {
  return (
    <Card className={cn("w-full", scoreCardClasses(job.ai_score))}>
      <CardHeader>
        <div>

        <CardTitle className="text-lg font-bold">{job.title}</CardTitle>
        <CardTitle>{job.date_posted}</CardTitle>
        </div>
        <CardDescription className="font-bold text-foreground">
          {job.company}
        </CardDescription>
        <CardAction>
          <span className={cn("text-lg font-bold tabular-nums", scoreTextClasses(job.ai_score))}>
            {job.ai_score}/100
          </span>
        </CardAction>
      </CardHeader>

      <div className="flex flex-wrap items-center gap-4 px-4 pb-4">
        <Button
          asChild
          className="w-fit p-4 px-16 bg-black font-bold text-white hover:bg-black/90"
        >
          <a href={job.link} target="_blank" rel="noreferrer">
            Apply
          </a>
        </Button>

        {job.missing_skills.length > 0 && (
          <div className="flex flex-col gap-1">
            <p className="text-xs font-medium text-muted-foreground">Missing skills</p>
            <div className="flex flex-wrap gap-1">
              {job.missing_skills.map((skill) => (
                <Badge key={skill} variant="outline">
                  {skill}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
