import { create } from "zustand";
import type { Article } from "../types/article";
import type { PipelineMode } from "../types/pipeline";

interface GateModalState {
  gate: "gate_one" | "gate_two";
  runId: number;
}

interface AppState {
  sidebarOpen: boolean;
  rightPanelOpen: boolean;
  rightPanelTab: "pipeline" | "references" | "validation";
  activeArticle: Article | null;
  pipelineMode: PipelineMode;
  articles: Article[];
  articleContent: string | null;
  gateModal: GateModalState | null;
  articlesLoading: boolean;

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

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab }),
  setActiveArticle: (article) =>
    set({ activeArticle: article, articleContent: null }),
  setPipelineMode: (mode) => set({ pipelineMode: mode }),
  setArticles: (articles) => set({ articles }),
  addArticle: (article) =>
    set((s) => ({ articles: [article, ...s.articles] })),
  setArticleContent: (content) => set({ articleContent: content }),
  openGateModal: (gate, runId) => set({ gateModal: { gate, runId } }),
  closeGateModal: () => set({ gateModal: null }),
  setArticlesLoading: (loading) => set({ articlesLoading: loading }),
}));
