import type { Article } from "../../types/article";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { Icons } from "../common/Icons";

interface EditorProps {
  article: Article;
}

const MODE_LABELS: Record<string, string> = {
  research: "Stage 2 · 자료수집",
  outline: "Stage 3 · 아웃라인 · Gate 1 대기",
  generate: "Stage 4 · 본문 생성",
  validate: "Stage 5 · Validator 통과",
  gate2: "Stage 5 → Gate 2 대기",
  published: "Stage 6 · 발행 완료",
};

interface OutlineSection {
  readonly section_number: number;
  readonly heading: string;
  readonly key_points?: readonly string[];
  readonly estimated_words?: number;
}

export function Editor({ article }: EditorProps) {
  const pipelineMode = useAppStore((s) => s.pipelineMode);
  const articleContent = useAppStore((s) => s.articleContent);
  const events = usePipelineStore((s) => s.events);

  const modeLabel = MODE_LABELS[pipelineMode];
  const isEarlyStage =
    pipelineMode === "research" || pipelineMode === "outline";
  const hasContent = Boolean(articleContent);

  const outlineEvent = events.find(
    (e) => e.event_type === "gate_pending" && e.stage === "gate_one",
  );
  const outline: readonly OutlineSection[] =
    (outlineEvent?.data as { outline?: OutlineSection[] } | undefined)
      ?.outline ?? [];

  const completedSections = new Set(
    events
      .filter(
        (e) =>
          e.event_type === "stage_complete" &&
          e.stage === "generator" &&
          (e.data as { section_number?: number } | undefined)
            ?.section_number != null,
      )
      .map(
        (e) =>
          (e.data as { section_number: number }).section_number,
      ),
  );

  const activeSectionNum = events
    .filter(
      (e) =>
        e.event_type === "stage_start" &&
        e.stage === "generator" &&
        (e.data as { section_number?: number } | undefined)?.section_number !=
          null,
    )
    .map(
      (e) =>
        (e.data as { section_number: number }).section_number,
    )
    .pop();

  return (
    <div className="editor">
      <div className="cover" />

      <div className="editor-meta">
        {modeLabel && (
          <>
            <span className="chip accent">{modeLabel}</span>
            <span>·</span>
          </>
        )}
        <span>
          {article.word_count > 0
            ? `예상 분량 ${article.word_count.toLocaleString()}자`
            : "분량 미정"}
        </span>
        <span>·</span>
        <span>이미지 {article.image_count}장</span>
        <span>·</span>
        <span>편당 비용 $0</span>
      </div>

      <h1 className="editor-title">
        {article.category && <span className="cat">{article.category}</span>}
        {article.title ?? article.topic}
      </h1>

      {article.title && article.title !== article.topic && (
        <div className="editor-subtitle">{article.topic}</div>
      )}

      {article.tags && article.tags.length > 0 && (
        <div className="tag-row">
          {article.tags.map((t, i) => (
            <span key={i} className={`tag ${i < 2 ? "primary" : ""}`}>
              #{t}
            </span>
          ))}
        </div>
      )}

      {(article.word_count > 0 || article.image_count > 0) && (
        <div className="meta-grid">
          <div className="meta-cell">
            <div className="k">참고자료</div>
            <div className="v">
              {article.reference_count ?? 0}
              <span className="unit"> / 8~15</span>
            </div>
          </div>
          <div className="meta-cell">
            <div className="k">대섹션</div>
            <div className="v">
              {article.section_count ?? outline.length ?? 0}
              <span className="unit"> / 7~9</span>
            </div>
          </div>
          <div className="meta-cell">
            <div className="k">키워드 밀도</div>
            <div className="v">
              —<span className="unit">%</span>
            </div>
          </div>
          <div className="meta-cell">
            <div className="k">예상 소요</div>
            <div className="v">
              —<span className="unit"> 분</span>
            </div>
          </div>
        </div>
      )}

      {hasContent ? (
        <MarkdownRenderer content={articleContent!} articleId={article.id} />
      ) : isEarlyStage ? (
        <EarlyStageSections outline={outline} />
      ) : (
        <GenerateStageSections
          outline={outline}
          completedSections={completedSections}
          activeSectionNum={activeSectionNum}
        />
      )}
    </div>
  );
}

function EarlyStageSections({
  outline,
}: {
  readonly outline: readonly OutlineSection[];
}) {
  const sections =
    outline.length > 0
      ? outline
      : Array.from({ length: 5 }, (_, i) => ({
          section_number: i + 1,
          heading: "",
        }));

  return (
    <>
      {sections.map((sec) => (
        <section key={sec.section_number} className="section">
          <h2 className="section-head">
            <span className="num">{sec.section_number}.</span>
            <span>{sec.heading || " "}</span>
            <span className="status queue">
              <span className="d" /> 대기
            </span>
          </h2>
          <div className="skel queued">
            <div className="line w90" />
            <div className="line w70" />
            <div className="line w50" />
          </div>
        </section>
      ))}
      <div className="slash-hint">
        <Icons.Sparkle s={14} /> Stage 2~3 완료 후 본문 생성이 시작됩니다.
        <div className="kbd-row">
          <span className="kbd">esc</span>
          <span style={{ fontSize: 11, color: "var(--text-faint)" }}>취소</span>
        </div>
      </div>
    </>
  );
}

function GenerateStageSections({
  outline,
  completedSections,
  activeSectionNum,
}: {
  readonly outline: readonly OutlineSection[];
  readonly completedSections: ReadonlySet<number>;
  readonly activeSectionNum: number | undefined;
}) {
  const sections =
    outline.length > 0
      ? outline
      : Array.from({ length: 6 }, (_, i) => ({
          section_number: i + 1,
          heading: "",
        }));

  return (
    <>
      {sections.map((sec) => {
        const isDone = completedSections.has(sec.section_number);
        const isActive = activeSectionNum === sec.section_number;

        let statusCls: string;
        let statusText: string;
        if (isDone) {
          statusCls = "";
          statusText = "생성 완료";
        } else if (isActive) {
          statusCls = "gen";
          statusText = "Generator 작성 중";
        } else if (
          completedSections.size > 0 &&
          sec.section_number >
            Math.max(...Array.from(completedSections))
        ) {
          statusCls = "queue";
          statusText = "대기";
        } else if (completedSections.size === 0 && !isActive) {
          statusCls = sec.section_number <= 3 ? "" : "gen";
          statusText =
            sec.section_number <= 3 ? "생성 완료" : "Generator 작성 중";
        } else {
          statusCls = "queue";
          statusText = "대기";
        }

        const skelCls = isDone ? "" : isActive ? "" : "queued";

        return (
          <section key={sec.section_number} className="section">
            <h2 className="section-head">
              <span className="num">{sec.section_number}.</span>
              <span>{sec.heading || " "}</span>
              <span className={`status ${statusCls}`}>
                <span className="d" /> {statusText}
              </span>
            </h2>
            <div className={`skel ${skelCls}`}>
              <div className="line w90" />
              <div className="line w70" />
              {(isDone || isActive) && <div className="line w50" />}
            </div>
          </section>
        );
      })}
    </>
  );
}
