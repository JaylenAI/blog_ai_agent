import { create } from "zustand";
import type { Article } from "../types/article";
import type { PipelineMode } from "../types/pipeline";

interface GateModalState {
  gate: "gate_one" | "gate_two";
  runId: number;
}

type Theme = "light" | "dark";
type Density = "compact" | "default" | "spacious";

export interface Toast {
  id: string;
  type: "error" | "success" | "info";
  message: string;
}

export type SidebarPanel = null | "pipelines" | "style-guide" | "tistory" | "subagents" | "skills" | "eval" | "mcp" | "dashboard" | "settings";
export type EditorMode = "view" | "edit";

interface AppState {
  sidebarOpen: boolean;
  rightPanelOpen: boolean;
  rightPanelTab: "pipeline" | "references" | "validation" | "history";
  activeArticle: Article | null;
  pipelineMode: PipelineMode;
  articles: Article[];
  articleContent: string | null;
  gateModal: GateModalState | null;
  articlesLoading: boolean;
  theme: Theme;
  density: Density;
  accentHue: number;
  toasts: Toast[];
  sidebarPanel: SidebarPanel;
  publishKitOpen: boolean;
  editorMode: EditorMode;
  editDraft: string | null;

  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  setRightPanelTab: (tab: AppState["rightPanelTab"]) => void;
  setActiveArticle: (article: Article | null) => void;
  setPipelineMode: (mode: PipelineMode) => void;
  setArticles: (articles: Article[]) => void;
  addArticle: (article: Article) => void;
  setArticleContent: (content: string | null) => void;
  openGateModal: (gate: GateModalState["gate"], runId: number) => void;
  closeGateModal: () => void;
  setArticlesLoading: (loading: boolean) => void;
  setTheme: (theme: Theme) => void;
  setDensity: (density: Density) => void;
  setAccentHue: (hue: number) => void;
  addToast: (toast: Omit<Toast, "id">) => void;
  removeToast: (id: string) => void;
  setSidebarPanel: (panel: SidebarPanel) => void;
  setPublishKitOpen: (open: boolean) => void;
  setEditorMode: (mode: EditorMode) => void;
  setEditDraft: (draft: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  rightPanelOpen: true,
  rightPanelTab: "pipeline",
  activeArticle: null,
  pipelineMode: "idle",
  articles: [],
  articleContent: null,
  gateModal: null,
  articlesLoading: false,
  theme: (typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light") as Theme,
  density: "default" as Density,
  accentHue: 255,
  toasts: [],
  sidebarPanel: null,
  publishKitOpen: false,
  editorMode: "view" as EditorMode,
  editDraft: null as string | null,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab }),
  setActiveArticle: (article) =>
    set({ activeArticle: article, articleContent: null, editorMode: "view" as EditorMode, editDraft: null }),
  setPipelineMode: (mode) => set({ pipelineMode: mode }),
  setArticles: (articles) => set({ articles }),
  addArticle: (article) =>
    set((s) => ({ articles: [article, ...s.articles] })),
  setArticleContent: (content) => set({ articleContent: content }),
  openGateModal: (gate, runId) => set({ gateModal: { gate, runId } }),
  closeGateModal: () => set({ gateModal: null }),
  setArticlesLoading: (loading) => set({ articlesLoading: loading }),
  setTheme: (theme) => set({ theme }),
  setDensity: (density) => set({ density }),
  setAccentHue: (hue) => set({ accentHue: hue }),
  addToast: (toast) =>
    set((s) => ({
      toasts: [...s.toasts, { ...toast, id: crypto.randomUUID() }],
    })),
  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  setSidebarPanel: (panel) =>
    set((s) => ({ sidebarPanel: s.sidebarPanel === panel ? null : panel })),
  setPublishKitOpen: (open) => set({ publishKitOpen: open }),
  setEditorMode: (mode) => set({ editorMode: mode, editDraft: mode === "view" ? null : undefined }),
  setEditDraft: (draft) => set({ editDraft: draft }),
}));
