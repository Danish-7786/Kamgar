import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { VerdictBadge } from "./VerdictBadge";
import type { Job } from "../types";

export function JobsTable({ jobs }: { jobs: Job[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Title</TableHead>
          <TableHead>Company</TableHead>
          <TableHead className="text-right">Score</TableHead>
          <TableHead>Verdict</TableHead>
          <TableHead className="text-right">Link</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {jobs.map((job) => (
          <TableRow key={job.id}>
            <TableCell className="font-medium">{job.title}</TableCell>
            <TableCell>{job.company}</TableCell>
            <TableCell className="text-right tabular-nums">{job.ai_score}</TableCell>
            <TableCell>
              <VerdictBadge verdict={job.verdict} />
            </TableCell>
            <TableCell className="text-right">
              <Button asChild variant="ghost" size="sm">
                <a href={job.link} target="_blank" rel="noreferrer">
                  Open
                </a>
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
