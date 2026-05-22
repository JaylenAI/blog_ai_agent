import { usePipelineStore } from "../../stores/pipeline-store";

interface OutlineImage {
  type: "mmd" | "svg";
  caption?: string;
}

interface OutlineSection {
  section_number: number;
  heading: string;
  key_points: string[];
  estimated_words: number;
  images?: OutlineImage[];
}

export function OutlinePreview() {
  const events = usePipelineStore((s) => s.events);

  const gateEvent = events.find(
    (e) => e.event_type === "gate_pending" && e.stage === "gate_one",
  );
  const data = gateEvent?.data as
    | {
        outline?: OutlineSection[];
        total_sections?: number;
        estimated_total_words?: number;
      }
    | undefined;

  const outline = data?.outline ?? [];

  if (outline.length === 0) {
    return (
      <p style={{ color: "var(--text-muted)" }}>
        아웃라인 데이터가 없습니다.
      </p>
    );
  }

  return (
    <>
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <div className="vstat" style={{ flex: 1 }}>
          <div className="label">섹션</div>
          <div className="value">{data?.total_sections ?? outline.length}</div>
        </div>
        <div className="vstat" style={{ flex: 1 }}>
          <div className="label">예상 분량</div>
          <div className="value">
            {((data?.estimated_total_words ?? 0) / 1000).toFixed(1)}K자
          </div>
        </div>
      </div>

      <div className="outline-list">
        {outline.map((s) => (
          <div key={s.section_number} className="outline-item">
            <div className="outline-num">{s.section_number}.</div>
            <div>
              <div className="outline-h2">{s.heading}</div>
              {s.key_points.length > 0 && (
                <div className="outline-key">
                  {s.key_points.length <= 3
                    ? s.key_points.join(" · ")
                    : `${s.key_points.slice(0, 3).join(" · ")} 외 ${s.key_points.length - 3}건`}
                </div>
              )}
            </div>
            <div className="outline-tags">
              {s.images?.map((img, j) => (
                <span
                  key={`img-${j}`}
                  className="outline-tag"
                  style={{
                    background:
                      img.type === "mmd"
                        ? "var(--accent-soft)"
                        : "var(--bg-sub)",
                    color:
                      img.type === "mmd"
                        ? "var(--accent-strong)"
                        : "var(--text-muted)",
                  }}
                >
                  {img.type.toUpperCase()}
                </span>
              ))}
              <span className="outline-tag">~{s.estimated_words}자</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
