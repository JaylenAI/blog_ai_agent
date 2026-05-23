import { useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";

export function BatchEditPanel() {
  const articles = useAppStore((s) => s.articles);
  const addToast = useAppStore((s) => s.addToast);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [category, setCategory] = useState("");
  const [tags, setTags] = useState("");
  const [status, setStatus] = useState("");
  const [saving, setSaving] = useState(false);

  const toggleSelect = (id: number) => {
    const next = new Set(selected);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelected(next);
  };

  const toggleAll = () => {
    if (selected.size === articles.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(articles.map((a) => a.id)));
    }
  };

  const handleApply = async () => {
    if (selected.size === 0) return;
    setSaving(true);
    try {
      const data: {
        article_ids: number[];
        category?: string;
        tags?: string[];
        status?: string;
      } = {
        article_ids: [...selected],
      };
      if (category) data.category = category;
      if (tags)
        data.tags = tags
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean);
      if (status) data.status = status;

      const res = await api.settings.batchUpdate(data);
      if (res.success) {
        addToast({
          type: "success",
          message: `${res.data?.updated ?? 0}개 아티클 업데이트 완료`,
        });
        setSelected(new Set());
      }
    } catch {
      addToast({ type: "error", message: "일괄 업데이트 실패" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-form">
      <div className="batch-select-header">
        <label>
          <input
            type="checkbox"
            checked={
              selected.size === articles.length && articles.length > 0
            }
            onChange={toggleAll}
          />
          {" "}전체 선택 ({selected.size}/{articles.length})
        </label>
      </div>

      <div className="batch-list">
        {articles.map((a) => (
          <label key={a.id} className="batch-item">
            <input
              type="checkbox"
              checked={selected.has(a.id)}
              onChange={() => toggleSelect(a.id)}
            />
            <span className="batch-item-title">
              {a.title ?? a.topic}
            </span>
          </label>
        ))}
      </div>

      {selected.size > 0 && (
        <div className="batch-fields">
          <div className="settings-group">
            <label className="settings-label">카테고리 변경</label>
            <input
              className="settings-input"
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="새 카테고리 (비우면 변경 안 함)"
            />
          </div>
          <div className="settings-group">
            <label className="settings-label">태그 변경</label>
            <input
              className="settings-input"
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="태그1, 태그2 (비우면 변경 안 함)"
            />
          </div>
          <div className="settings-group">
            <label className="settings-label">상태 변경</label>
            <select
              className="settings-input"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">변경 안 함</option>
              <option value="draft">초안</option>
              <option value="review">검수 대기</option>
              <option value="published">발행 완료</option>
            </select>
          </div>
          <button
            className="settings-save"
            onClick={handleApply}
            disabled={saving}
          >
            {saving ? "적용 중..." : `${selected.size}개 아티클에 적용`}
          </button>
        </div>
      )}
    </div>
  );
}
