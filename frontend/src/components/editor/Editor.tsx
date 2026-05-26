import { useCallback, useEffect, useRef, useState } from "react";
import type { Article } from "../../types/article";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import { usePipelineStore } from "../../stores/pipeline-store";
import { LazyMarkdownRenderer as MarkdownRenderer } from "./LazyMarkdownRenderer";
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
  const editorMode = useAppStore((s) => s.editorMode);
  const editDraft = useAppStore((s) => s.editDraft);
  const setEditorMode = useAppStore((s) => s.setEditorMode);
  const setEditDraft = useAppStore((s) => s.setEditDraft);
  const setArticleContent = useAppStore((s) => s.setArticleContent);
  const addToast = useAppStore((s) => s.addToast);
  const events = usePipelineStore((s) => s.events);
  const sectionProgress = usePipelineStore((s) => s.sectionProgress);
  const [saving, setSaving] = useState(false);

  const modeLabel = MODE_LABELS[pipelineMode];
  const isEarlyStage =
    pipelineMode === "research" || pipelineMode === "outline";
  const hasContent = Boolean(articleContent);
  const isEditing = editorMode === "edit";

  const outlineEvent = events.find(
    (e) => e.event_type === "gate_pending" && e.stage === "gate_one",
  );
  const outline: readonly OutlineSection[] =
    (outlineEvent?.data as { outline?: OutlineSection[] } | undefined)
      ?.outline ?? [];

  const completedSections = new Set<number>();
  if (sectionProgress) {
    for (let i = 1; i <= sectionProgress.completedSections; i++) {
      completedSections.add(i);
    }
  }

  const activeSectionNum = sectionProgress?.status === "writing"
    ? sectionProgress.currentSection
    : undefined;

  const handleEdit = useCallback(() => {
    setEditDraft(articleContent ?? "");
    setEditorMode("edit");
  }, [articleContent, setEditDraft, setEditorMode]);

  const handleCancel = useCallback(() => {
    setEditorMode("view");
  }, [setEditorMode]);

  const handleSave = useCallback(async () => {
    if (editDraft == null) return;
    setSaving(true);
    try {
      const res = await api.articles.updateContent(article.id, editDraft);
      if (res.success) {
        setArticleContent(editDraft);
        setEditorMode("view");
        addToast({ type: "success", message: "저장 완료" });
      }
    } catch {
      addToast({ type: "error", message: "저장 실패" });
    } finally {
      setSaving(false);
    }
  }, [editDraft, article.id, setArticleContent, setEditorMode, addToast]);

  useEffect(() => {
    if (!isEditing) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "s" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        void handleSave();
      }
      if (e.key === "Escape") handleCancel();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isEditing, handleSave, handleCancel]);

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

        {hasContent && !isEditing && (
          <button className="editor-edit-btn" onClick={handleEdit} aria-label="편집">
            <Icons.Doc s={12} /> 편집
          </button>
        )}
        {isEditing && (
          <div className="editor-edit-actions">
            <button className="editor-cancel-btn" onClick={handleCancel} aria-label="편집 취소">
              취소
            </button>
            <button
              className="editor-save-btn"
              onClick={handleSave}
              disabled={saving}
              aria-label="저장"
            >
              <Icons.Check s={12} w={2} />
              {saving ? "저장 중..." : "저장"}
            </button>
            <span className="editor-shortcut">⌘S</span>
          </div>
        )}
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
              {article.reference_count || 0}
              <span className="unit"> / 8~15</span>
            </div>
          </div>
          <div className="meta-cell">
            <div className="k">대섹션</div>
            <div className="v">
              {article.section_count || outline.length || 0}
              <span className="unit"> / 7~9</span>
            </div>
          </div>
        </div>
      )}

      {isEditing && editDraft != null ? (
        <MarkdownEditor
          value={editDraft}
          onChange={setEditDraft}
          articleId={article.id}
        />
      ) : hasContent ? (
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

function MarkdownEditor({
  value,
  onChange,
  articleId,
}: {
  value: string;
  onChange: (value: string) => void;
  articleId: number;
}) {
  const [splitView, setSplitView] = useState(true);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  return (
    <div className="md-editor">
      <div className="md-editor-toolbar">
        <button
          className={`pk-view-btn ${splitView ? "active" : ""}`}
          onClick={() => setSplitView(true)}
        >
          분할 보기
        </button>
        <button
          className={`pk-view-btn ${!splitView ? "active" : ""}`}
          onClick={() => setSplitView(false)}
        >
          편집만
        </button>
        <span className="md-editor-chars">
          {value.replace(/\s/g, "").length.toLocaleString()}자
        </span>
      </div>
      <div className={`md-editor-panes ${splitView ? "split" : "single"}`}>
        <div className="md-editor-input">
          <textarea
            ref={textareaRef}
            className="md-editor-textarea"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            spellCheck={false}
          />
        </div>
        {splitView && (
          <div className="md-editor-preview">
            <MarkdownRenderer content={value} articleId={articleId} />
          </div>
        )}
      </div>
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
