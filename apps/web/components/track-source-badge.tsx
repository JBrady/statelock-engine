import { Badge } from "@/components/ui/badge";

type TrackSourceBadgeProps = {
  track: "core" | "observability";
};

export function TrackSourceBadge({ track }: TrackSourceBadgeProps) {
  if (track === "core") {
    return (
      <Badge className="border-gold/30 bg-gold/10 text-gold">
        Core durable memory
      </Badge>
    );
  }

  return (
    <Badge className="border-teal/30 bg-teal/10 text-teal">
      Observability learned memory
    </Badge>
  );
}
