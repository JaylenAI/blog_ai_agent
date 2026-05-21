import { Icons } from "../common/Icons";

interface FigureProps {
  readonly kind: "mmd" | "svg";
  readonly caption: string;
  readonly alt?: string;
}

export function Figure({ kind, caption, alt }: FigureProps) {
  return (
    <figure className="figure">
      <div className="figure-body">
        <div style={{ textAlign: "center", color: "var(--text-faint)" }}>
          <Icons.Layers s={24} />
          <div style={{ fontSize: 12, marginTop: 6 }}>
            {alt ?? (kind === "mmd" ? "Mermaid 다이어그램" : "SVG 이미지")}
          </div>
        </div>
      </div>
      <figcaption className="figure-cap">
        <span className="badge">{kind === "mmd" ? "MERMAID" : "SVG"}</span>
        <span>{caption}</span>
      </figcaption>
    </figure>
  );
}
