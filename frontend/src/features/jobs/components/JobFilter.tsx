import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

interface JobFilterProps {
  value?: string;
  onSelect: (value: string) => void;
}

export function JobFilter({ value, onSelect }: JobFilterProps) {
  return (
    <Select value={value} onValueChange={onSelect}>
      <SelectTrigger className="w-full max-w-48">
        <SelectValue placeholder="Sort" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Sort By</SelectLabel>
          <SelectItem value="created_at">Date</SelectItem>
          <SelectItem value="score">AI score</SelectItem>
        </SelectGroup>
      </SelectContent>
    </Select>
  )
}

