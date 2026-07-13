import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

interface JobsPaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  // True while a page transition is in flight — disables the controls.
  disabled?: boolean;
}

// Presentational pager: owns no data, just reports the page the user wants.
export function JobsPagination({
  page,
  totalPages,
  onPageChange,
  disabled = false,
}: JobsPaginationProps) {
  const canPrev = page > 1 && !disabled;
  const canNext = page < totalPages && !disabled;

  return (
    <Pagination className="mx-0 w-auto">
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            onClick={() => canPrev && onPageChange(page - 1)}
            aria-disabled={!canPrev}
            className={
              canPrev ? "cursor-pointer" : "pointer-events-none opacity-50"
            }
          />
        </PaginationItem>
        <PaginationItem>
          <PaginationNext
            onClick={() => canNext && onPageChange(page + 1)}
            aria-disabled={!canNext}
            className={
              canNext ? "cursor-pointer" : "pointer-events-none opacity-50"
            }
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}
