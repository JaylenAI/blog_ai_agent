import { usePipelineStore } from "../../stores/pipeline-store";

interface OutlineSection {
  section_number: number;
  heading: string;
  key_points: string[];
  estimated_words: number;
}

export function OutlinePreview() {
  const events = usePipelineStore((s) => s.events);

  const gateEvent = events.find(
    (e) => e.event_type === "gate_pending" && e.stage === "gate_one",
  );
  const data = gateEvent?.data as
    | { outline?: OutlineSection[]; total_sections?: number; estimated_total_words?: number }
    | undefined;

  const outline = data?.outline ?? [];

  if (outline.length === 0) {
    return (
      <p style={{ color: "var(--color-text-muted)" }}>
        아웃라인 데이터가 없습니다.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      <div
        className="flex gap-4 text-xs"
        style={{ color: "var(--color-text-faint)" }}
      >
        <span>섹션 {data?.total_sections ?? outline.length}개</span>
        <span>
          예상 {(data?.estimated_total_words ?? 0).toLocaleString()}자
        </span>
      </div>

      <div className="space-y-2">
        {outline.map((section) => (
          <div
            key={section.section_number}
            className="p-3 rounded-md"
            style={{ backgroundColor: "var(--color-bg-sub)" }}
          >
            <div className="text-sm font-medium">{section.heading}</div>
            {section.key_points.length > 0 && (
              <ul
                className="mt-1 space-y-0.5 text-xs list-disc list-inside"
                style={{ color: "var(--color-text-muted)" }}
              >
                {section.key_points.map((pt, i) => (
                  <li key={i}>{pt}</li>
                ))}
              </ul>
            )}
            <div
              className="mt-1 text-xs"
              style={{ color: "var(--color-text-faint)" }}
            >
              ~{section.estimated_words}자
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
