import { useCallback, useEffect, useState } from "react";
import { api } from "../../api/client";
import { useAppStore } from "../../stores/app-store";
import { BatchEditPanel } from "./BatchEditPanel";

interface ObsidianSettings {
  vault_path: string;
  frontmatter_tags: string[];
  auto_save: boolean;
}

interface GeneralSettings {
  tistory_blog_url: string;
  stage_timeout: number;
  image_generation_enabled: boolean;
  max_images_per_article: number;
  log_level: string;
}

export function SettingsPanel() {
  const addToast = useAppStore((s) => s.addToast);
  const [tab, setTab] = useState<"obsidian" | "general" | "batch">("obsidian");
  const [obsidian, setObsidian] = useState<ObsidianSettings | null>(null);
  const [general, setGeneral] = useState<GeneralSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.settings
      .getObsidian()
      .then((res) => {
        if (res.success && res.data)
          setObsidian(res.data as ObsidianSettings);
      })
      .catch(() => addToast({ type: "error", message: "Obsidian 설정 로드 실패" }));
    api.settings
      .getGeneral()
      .then((res) => {
        if (res.success && res.data)
          setGeneral(res.data as GeneralSettings);
      })
      .catch(() => addToast({ type: "error", message: "일반 설정 로드 실패" }));
  }, [addToast]);

  const saveObsidian = useCallback(async () => {
    if (!obsidian) return;
    setSaving(true);
    try {
      await api.settings.updateObsidian(obsidian);
      addToast({ type: "success", message: "Obsidian 설정 저장 완료" });
    } catch {
      addToast({ type: "error", message: "저장 실패" });
    } finally {
      setSaving(false);
    }
  }, [obsidian, addToast]);

  const saveGeneral = useCallback(async () => {
    if (!general) return;
    setSaving(true);
    try {
      await api.settings.updateGeneral(general);
      addToast({ type: "success", message: "일반 설정 저장 완료" });
    } catch {
      addToast({ type: "error", message: "저장 실패" });
    } finally {
      setSaving(false);
    }
  }, [general, addToast]);

  return (
    <div className="settings-panel">
      <div className="settings-tabs">
        <button
          className={`settings-tab ${tab === "obsidian" ? "active" : ""}`}
          onClick={() => setTab("obsidian")}
        >
          Obsidian
        </button>
        <button
          className={`settings-tab ${tab === "general" ? "active" : ""}`}
          onClick={() => setTab("general")}
        >
          일반
        </button>
        <button
          className={`settings-tab ${tab === "batch" ? "active" : ""}`}
          onClick={() => setTab("batch")}
        >
          일괄 편집
        </button>
      </div>

      {tab === "obsidian" && obsidian && (
        <div className="settings-form">
          <div className="settings-group">
            <label className="settings-label">
              Obsidian Vault 경로
            </label>
            <input
              className="settings-input"
              type="text"
              value={obsidian.vault_path}
              onChange={(e) =>
                setObsidian({ ...obsidian, vault_path: e.target.value })
              }
              placeholder="/Users/name/ObsidianVault"
            />
            <span className="settings-hint">
              Obsidian 볼트의 절대 경로를 입력하세요
            </span>
          </div>

          <div className="settings-group">
            <label className="settings-label">프론트매터 기본 태그</label>
            <input
              className="settings-input"
              type="text"
              value={obsidian.frontmatter_tags.join(", ")}
              onChange={(e) =>
                setObsidian({
                  ...obsidian,
                  frontmatter_tags: e.target.value
                    .split(",")
                    .map((t) => t.trim())
                    .filter(Boolean),
                })
              }
              placeholder="blog/published, category/ai"
            />
            <span className="settings-hint">쉼표로 구분하여 입력</span>
          </div>

          <div className="settings-group">
            <label className="settings-label">
              <input
                type="checkbox"
                checked={obsidian.auto_save}
                onChange={(e) =>
                  setObsidian({ ...obsidian, auto_save: e.target.checked })
                }
              />
              {" "}발행 시 자동 저장
            </label>
            <span className="settings-hint">
              Gate 2 통과 후 자동으로 Obsidian에 저장
            </span>
          </div>

          <button
            className="settings-save"
            onClick={saveObsidian}
            disabled={saving}
          >
            {saving ? "저장 중..." : "Obsidian 설정 저장"}
          </button>
        </div>
      )}

      {tab === "general" && general && (
        <div className="settings-form">
          <div className="settings-group">
            <label className="settings-label">Tistory 블로그 URL</label>
            <input
              className="settings-input"
              type="text"
              value={general.tistory_blog_url}
              onChange={(e) =>
                setGeneral({
                  ...general,
                  tistory_blog_url: e.target.value,
                })
              }
              placeholder="https://jaylenhan.tistory.com"
            />
          </div>

          <div className="settings-group">
            <label className="settings-label">
              스테이지 타임아웃 (초)
            </label>
            <input
              className="settings-input"
              type="number"
              value={general.stage_timeout}
              onChange={(e) =>
                setGeneral({
                  ...general,
                  stage_timeout: Number(e.target.value),
                })
              }
            />
          </div>

          <div className="settings-group">
            <label className="settings-label">
              <input
                type="checkbox"
                checked={general.image_generation_enabled}
                onChange={(e) =>
                  setGeneral({
                    ...general,
                    image_generation_enabled: e.target.checked,
                  })
                }
              />
              {" "}이미지 자동 생성
            </label>
          </div>

          <div className="settings-group">
            <label className="settings-label">글당 최대 이미지 수</label>
            <input
              className="settings-input"
              type="number"
              value={general.max_images_per_article}
              onChange={(e) =>
                setGeneral({
                  ...general,
                  max_images_per_article: Number(e.target.value),
                })
              }
              min={0}
              max={10}
            />
          </div>

          <div className="settings-group">
            <label className="settings-label">로그 레벨</label>
            <select
              className="settings-input"
              value={general.log_level}
              onChange={(e) =>
                setGeneral({ ...general, log_level: e.target.value })
              }
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>

          <button
            className="settings-save"
            onClick={saveGeneral}
            disabled={saving}
          >
            {saving ? "저장 중..." : "일반 설정 저장"}
          </button>
        </div>
      )}

      {tab === "batch" && <BatchEditPanel />}
    </div>
  );
}
