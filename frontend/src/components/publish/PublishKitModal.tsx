import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import { Icons } from "../common/Icons";
import { LazyMarkdownRenderer as MarkdownRenderer } from "../editor/LazyMarkdownRenderer";
import type { PublishKit, ReferenceItem } from "../../types/publish";

type Tab = "markdown" | "html" | "meta" | "references" | "images";

interface Props {
  articleId: number;
  onClose: () => void;
}

export function PublishKitModal({ articleId, onClose }: Props) {
  const [kit, setKit] = useState<PublishKit | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("markdown");
  const addToast = useAppStore((s) => s.addToast);

  useEffect(() => {
    api.publishKit
      .get(articleId)
      .then((res) => {
        if (res.success && res.data) setKit(res.data);
      })
      .finally(() => setLoading(false));
  }, [articleId]);

  const copyText = useCallback(
    async (text: string, label: string) => {
      try {
        await navigator.clipboard.writeText(text);
        addToast({ type: "success", message: `${label} 복사 완료` });
      } catch {
        addToast({ type: "error", message: "클립보드 복사 실패" });
      }
    },
    [addToast],
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="pk-overlay" onClick={onClose}>
      <div
        className="pk-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pk-modal-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="pk-header">
          <div className="pk-header-left">
            <Icons.Send s={16} />
            <span className="pk-header-title" id="pk-modal-title">발행 준비</span>
            {kit && (
              <span className="pk-header-sub">
                {kit.title} · {kit.word_count.toLocaleString()}자
              </span>
            )}
          </div>
          <button className="pk-close" onClick={onClose} aria-label="닫기">
            <Icons.X s={16} />
          </button>
        </div>

        <div className="pk-tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`pk-tab ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              {t.icon}
              {t.label}
              {t.id === "references" && kit && kit.references.length > 0 && (
                <span className="pk-tab-badge">{kit.references.length}</span>
              )}
              {t.id === "images" && kit && kit.images.length > 0 && (
                <span className="pk-tab-badge">{kit.images.length}</span>
              )}
            </button>
          ))}
        </div>

        <div className="pk-body">
          {loading ? (
            <div className="pk-empty">불러오는 중...</div>
          ) : !kit ? (
            <div className="pk-empty">데이터를 불러올 수 없습니다.</div>
          ) : (
            <TabContent tab={tab} kit={kit} articleId={articleId} copyText={copyText} />
          )}
        </div>
      </div>
    </div>
  );
}

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "markdown", label: "Markdown", icon: <Icons.Doc s={14} /> },
  { id: "html", label: "HTML", icon: <Icons.Hash s={14} /> },
  { id: "meta", label: "메타 정보", icon: <Icons.Tag s={14} /> },
  { id: "references", label: "참고자료", icon: <Icons.ExternalLink s={14} /> },
  { id: "images", label: "이미지", icon: <Icons.Eye s={14} /> },
];

function TabContent({
  tab,
  kit,
  articleId,
  copyText,
}: {
  tab: Tab;
  kit: PublishKit;
  articleId: number;
  copyText: (text: string, label: string) => Promise<void>;
}) {
  switch (tab) {
    case "markdown":
      return <MarkdownTab kit={kit} articleId={articleId} copyText={copyText} />;
    case "html":
      return <HtmlTab kit={kit} articleId={articleId} copyText={copyText} />;
    case "meta":
      return <MetaTab kit={kit} copyText={copyText} />;
    case "references":
      return <ReferencesTabContent references={kit.references} copyText={copyText} />;
    case "images":
      return <ImagesTab kit={kit} />;
  }
}

function MarkdownTab({
  kit,
  articleId,
  copyText,
}: {
  kit: PublishKit;
  articleId: number;
  copyText: (text: string, label: string) => Promise<void>;
}) {
  const [view, setView] = useState<"rendered" | "source">("rendered");

  if (!kit.markdown) {
    return (
      <EmptyState
        icon={<Icons.Doc s={28} w={1} />}
        title="마크다운 콘텐츠 없음"
        description="파이프라인을 실행하여 콘텐츠를 생성해 주세요."
      />
    );
  }

  return (
    <div className="pk-content-tab">
      <div className="pk-toolbar">
        <div className="pk-toolbar-left">
          <button
            className={`pk-view-btn ${view === "rendered" ? "active" : ""}`}
            onClick={() => setView("rendered")}
          >
            렌더링
          </button>
          <button
            className={`pk-view-btn ${view === "source" ? "active" : ""}`}
            onClick={() => setView("source")}
          >
            원본
          </button>
        </div>
        <button
          className="pk-copy-btn"
          onClick={() => copyText(kit.markdown!, "Markdown")}
        >
          <Icons.Share s={13} /> 복사
        </button>
      </div>
      <div className="pk-scroll">
        {view === "rendered" ? (
          <div className="pk-markdown-render">
            <MarkdownRenderer content={kit.markdown} articleId={articleId} />
          </div>
        ) : (
          <pre className="pk-source">{kit.markdown}</pre>
        )}
      </div>
    </div>
  );
}

function HtmlTab({
  kit,
  articleId,
  copyText,
}: {
  kit: PublishKit;
  articleId: number;
  copyText: (text: string, label: string) => Promise<void>;
}) {
  const [view, setView] = useState<"preview" | "source">("source");
  const renderRef = useRef<HTMLDivElement>(null);
  const [generatedHtml, setGeneratedHtml] = useState<string | null>(null);
  const [backendHtml, setBackendHtml] = useState<string | null>(null);
  const [backendChecked, setBackendChecked] = useState(false);

  useEffect(() => {
    if (kit.html) {
      setBackendChecked(true);
      return;
    }
    api.articles
      .getHtml(articleId)
      .then((html) => {
        if (html) setBackendHtml(html);
      })
      .catch(() => { /* backend HTML unavailable — use fallback */ })
      .finally(() => setBackendChecked(true));
  }, [articleId, kit.html]);

  const htmlContent = kit.html ?? backendHtml ?? generatedHtml;
  const isGenerated = !kit.html && !backendHtml && !!generatedHtml;

  useEffect(() => {
    if (!kit.html && !backendHtml && backendChecked && kit.markdown && renderRef.current) {
      const el = renderRef.current;
      if (el.innerHTML.trim()) {
        setGeneratedHtml(el.innerHTML);
        return;
      }
      const observer = new MutationObserver(() => {
        if (el.innerHTML.trim()) {
          setGeneratedHtml(el.innerHTML);
          observer.disconnect();
        }
      });
      observer.observe(el, { childList: true, subtree: true });
      return () => observer.disconnect();
    }
  }, [kit.html, kit.markdown, backendHtml, backendChecked]);

  if (!kit.html && !kit.markdown && !backendHtml && backendChecked) {
    return (
      <EmptyState
        icon={<Icons.Hash s={28} w={1} />}
        title="HTML 콘텐츠 없음"
        description="파이프라인을 실행하여 콘텐츠를 생성해 주세요."
      />
    );
  }

  return (
    <div className="pk-content-tab">
      {!kit.html && !backendHtml && kit.markdown && (
        <div ref={renderRef} style={{ position: "absolute", left: "-9999px", top: 0 }}>
          <MarkdownRenderer content={kit.markdown} articleId={articleId} />
        </div>
      )}
      <div className="pk-toolbar">
        <div className="pk-toolbar-left">
          <button
            className={`pk-view-btn ${view === "source" ? "active" : ""}`}
            onClick={() => setView("source")}
          >
            코드
          </button>
          <button
            className={`pk-view-btn ${view === "preview" ? "active" : ""}`}
            onClick={() => setView("preview")}
          >
            미리보기
          </button>
          {isGenerated && (
            <span className="pk-generated-badge">마크다운에서 변환됨</span>
          )}
        </div>
        <button
          className="pk-copy-btn"
          disabled={!htmlContent}
          onClick={() => htmlContent && copyText(htmlContent, "HTML")}
        >
          <Icons.Share s={13} /> 복사
        </button>
      </div>
      <div className="pk-scroll">
        {!htmlContent ? (
          <div className="pk-empty">HTML 변환 중...</div>
        ) : view === "source" ? (
          <pre className="pk-source">{htmlContent}</pre>
        ) : (
          <iframe
            className="pk-html-preview"
            srcDoc={htmlContent}
            title="HTML Preview"
            sandbox=""
          />
        )}
      </div>
    </div>
  );
}

function MetaTab({
  kit,
  copyText,
}: {
  kit: PublishKit;
  copyText: (text: string, label: string) => Promise<void>;
}) {
  const tagsText = kit.tags.join(", ");

  return (
    <div className="pk-meta-tab">
      <MetaRow label="제목" value={kit.title} onCopy={() => copyText(kit.title, "제목")} />
      <MetaRow
        label="카테고리"
        value={kit.category || "미지정"}
        onCopy={() => copyText(kit.category, "카테고리")}
      />
      <MetaRow label="태그" value={tagsText} onCopy={() => copyText(tagsText, "태그")} />
      <MetaRow
        label="글자 수"
        value={`${kit.word_count.toLocaleString()}자`}
        onCopy={() => copyText(String(kit.word_count), "글자 수")}
      />
      <MetaRow
        label="상태"
        value={STATUS_LABELS[kit.status] ?? kit.status}
      />

      {kit.tags.length > 0 && (
        <div className="pk-meta-tags">
          <div className="pk-meta-tags-label">태그 목록</div>
          <div className="pk-meta-tags-list">
            {kit.tags.map((tag) => (
              <button
                key={tag}
                className="pk-tag-chip"
                onClick={() => copyText(tag, tag)}
                title="클릭하여 복사"
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="pk-meta-actions">
        <button
          className="pk-action-btn"
          onClick={() =>
            copyText(
              `제목: ${kit.title}\n카테고리: ${kit.category}\n태그: ${tagsText}`,
              "메타 정보 전체",
            )
          }
        >
          <Icons.Share s={13} /> 메타 정보 전체 복사
        </button>
      </div>
    </div>
  );
}

function MetaRow({
  label,
  value,
  onCopy,
}: {
  label: string;
  value: string;
  onCopy?: () => void;
}) {
  return (
    <div className="pk-meta-row">
      <span className="pk-meta-label">{label}</span>
      <span className="pk-meta-value">{value}</span>
      {onCopy && (
        <button className="pk-meta-copy" onClick={onCopy} title="복사">
          <Icons.Share s={12} />
        </button>
      )}
    </div>
  );
}

function ImagesTab({ kit }: { kit: PublishKit }) {
  const addToast = useAppStore((s) => s.addToast);
  const hasContent = kit.images.length > 0 || kit.diagrams.length > 0 || kit.thumbnail_url;

  if (!hasContent) {
    return (
      <EmptyState
        icon={<Icons.Eye s={28} w={1} />}
        title="이미지 없음"
        description="파이프라인 실행 시 이미지와 다이어그램이 자동 생성됩니다."
      />
    );
  }

  const handleDownload = async (url: string, name: string) => {
    try {
      const res = await fetch(url);
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch {
      addToast({ type: "error", message: "다운로드 실패" });
    }
  };

  return (
    <div className="pk-images-tab">
      {kit.thumbnail_url && (
        <>
          <div className="pk-images-section-title">썸네일</div>
          <div className="pk-thumbnail-wrap">
            <a href={kit.thumbnail_url} target="_blank" rel="noopener noreferrer">
              <img
                src={kit.thumbnail_url}
                alt="썸네일"
                className="pk-thumbnail-img"
                loading="lazy"
              />
            </a>
            <button
              className="pk-copy-btn"
              style={{ marginTop: 8 }}
              onClick={() => handleDownload(kit.thumbnail_url!, "thumbnail.png")}
            >
              <Icons.ExternalLink s={13} /> 다운로드
            </button>
          </div>
        </>
      )}

      {kit.images.length > 0 && (
        <>
          <div className="pk-images-section-title">
            이미지 ({kit.images.length})
          </div>
          <div className="pk-images-grid">
            {kit.images.map((img) => (
              <div key={img.name} className="pk-image-card">
                <a
                  href={img.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="pk-image-thumb"
                >
                  <img
                    src={img.url}
                    alt={img.name}
                    loading="lazy"
                  />
                </a>
                <div className="pk-image-info">
                  <span className="pk-image-name" title={img.name}>
                    {img.name}
                  </span>
                  <button
                    className="pk-image-dl"
                    title="다운로드"
                    onClick={() => handleDownload(img.url, img.name)}
                  >
                    <Icons.ExternalLink s={12} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {kit.diagrams.length > 0 && (
        <>
          <div className="pk-images-section-title">
            다이어그램 ({kit.diagrams.length})
          </div>
          <div className="pk-diagrams-list">
            {kit.diagrams.map((d) => (
              <DiagramCard key={d.name} diagram={d} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}

const SOURCE_LABELS: Record<string, string> = {
  official: "공식",
  github: "GitHub",
  blog_en: "영문 블로그",
  blog_kr: "한국어 블로그",
};

function ReferencesTabContent({
  references,
  copyText,
}: {
  references: ReferenceItem[];
  copyText: (text: string, label: string) => Promise<void>;
}) {
  if (references.length === 0) {
    return (
      <EmptyState
        icon={<Icons.ExternalLink s={28} w={1} />}
        title="참고자료 없음"
        description="파이프라인 실행 시 자동으로 수집됩니다."
      />
    );
  }

  const grouped = references.reduce<Record<string, ReferenceItem[]>>((acc, ref) => {
    const key = ref.source_type || "other";
    return { ...acc, [key]: [...(acc[key] ?? []), ref] };
  }, {});

  return (
    <div className="pk-references-tab">
      <div className="pk-ref-summary">
        총 {references.length}건의 참고자료
        <button
          className="pk-copy-btn"
          onClick={() => {
            const text = references
              .map((r) => `- [${r.title}](${r.url})\n  ${r.summary}`)
              .join("\n\n");
            copyText(text, "참고자료 전체");
          }}
        >
          <Icons.Share s={13} /> 전체 복사
        </button>
      </div>
      {Object.entries(grouped).map(([type, refs]) => (
        <div key={type} className="pk-ref-group">
          <div className="pk-ref-group-title">
            {SOURCE_LABELS[type] ?? type}
            <span className="pk-tab-badge">{refs.length}</span>
          </div>
          {refs.map((ref, i) => (
            <div key={`${ref.url}-${i}`} className="pk-ref-card">
              <div className="pk-ref-card-head">
                <a
                  href={ref.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="pk-ref-title"
                >
                  {ref.title}
                  <Icons.ExternalLink s={11} />
                </a>
                <span className="pk-ref-score">
                  {Math.round(ref.relevance_score * 100)}%
                </span>
              </div>
              <p className="pk-ref-summary-text">{ref.summary}</p>
              <span className="pk-ref-url">{ref.url}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

function DiagramCard({ diagram }: { diagram: { name: string; content: string } }) {
  const addToast = useAppStore((s) => s.addToast);

  return (
    <div className="pk-diagram-card">
      <div className="pk-diagram-header">
        <span>{diagram.name}</span>
        <button
          className="pk-meta-copy"
          onClick={async () => {
            await navigator.clipboard.writeText(diagram.content);
            addToast({ type: "success", message: `${diagram.name} 복사 완료` });
          }}
          title="Mermaid 코드 복사"
        >
          <Icons.Share s={12} />
        </button>
      </div>
      <pre className="pk-diagram-code">{diagram.content}</pre>
    </div>
  );
}

function EmptyState({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="pk-empty-state">
      {icon}
      <p className="pk-empty-title">{title}</p>
      <p className="pk-empty-desc">{description}</p>
    </div>
  );
}

const STATUS_LABELS: Record<string, string> = {
  draft: "초안",
  researching: "자료 수집 중",
  generating: "생성 중",
  validating: "검증 중",
  published: "발행 완료",
};
