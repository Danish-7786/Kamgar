import { useState } from "react";
import { ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useStatus, useTriggerScrape } from "../hooks/useScraper";
import {
  DEFAULT_PLATFORMS,
  PLATFORMS,
  type PlatformId,
} from "../api/scraperApi";

export function ScraperPage() {
  const [selected, setSelected] = useState<PlatformId[]>(DEFAULT_PLATFORMS);
  const scrape = useTriggerScrape();
  const { data: status } = useStatus();

  const isRunning = status?.scraper.is_running ?? false;
  const busy = isRunning || scrape.isPending;

  function togglePlatform(id: PlatformId, checked: boolean) {
    setSelected((prev) =>
      checked ? [...prev, id] : prev.filter((p) => p !== id),
    );
  }

  const triggerLabel =
    selected.length === PLATFORMS.length
      ? "All platforms"
      : selected.length === 0
        ? "Select platforms"
        : `${selected.length} platform${selected.length > 1 ? "s" : ""} selected`;

  return (
    <section className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Scraper</h2>
        <p className="text-sm text-muted-foreground">
          Choose which platforms to scrape, then trigger a run.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="w-56 justify-between">
              {triggerLabel}
              <ChevronDown className="opacity-60" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="start">
            <DropdownMenuLabel>Platforms</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {PLATFORMS.map((platform) => (
              <DropdownMenuCheckboxItem
                key={platform.id}
                checked={selected.includes(platform.id)}
                onCheckedChange={(checked) => togglePlatform(platform.id, checked)}
                // Keep the menu open while toggling multiple platforms.
                onSelect={(e) => e.preventDefault()}
              >
                {platform.label}
              </DropdownMenuCheckboxItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Button
          onClick={() => scrape.mutate(selected)}
          disabled={busy || selected.length === 0}
        >
          {isRunning
            ? "Scraping…"
            : scrape.isPending
              ? "Starting…"
              : "Run scraper"}
        </Button>
      </div>

      {selected.length === 0 && (
        <p className="text-sm text-destructive">Select at least one platform.</p>
      )}

      {scrape.isSuccess && (
        <p className="text-sm text-muted-foreground">{scrape.data.message}</p>
      )}

      {scrape.isError && (
        <p className="text-sm text-destructive">
          {scrape.error instanceof Error ? scrape.error.message : "Failed to trigger scrape."}
        </p>
      )}

      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span
          className={
            isRunning
              ? "inline-block size-2 rounded-full bg-green-500 animate-pulse"
              : "inline-block size-2 rounded-full bg-muted-foreground/40"
          }
        />
        {isRunning ? "Scraper is running…" : "Scraper is idle"}
      </div>
    </section>
  );
}
