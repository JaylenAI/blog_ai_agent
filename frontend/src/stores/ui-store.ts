import { create } from "zustand";
import type { SidebarPanel, EditorMode } from "./app-store";

type Theme = "light" | "dark";
type Density = "compact" | "default" | "spacious";

interface UIState {
  sidebarOpen: boolean;
  rightPanelOpen: boolean;
  rightPanelTab: "pipeline" | "references" | "validation" | "history";
  theme: Theme;
  density: Density;
  accentHue: number;
  sidebarPanel: SidebarPanel;
  publishKitOpen: boolean;
  editorMode: EditorMode;
  editDraft: string | null;

  toggleSidebar: () => void;
  toggleRightPanel: () => void;
  setRightPanelTab: (tab: UIState["rightPanelTab"]) => void;
  setTheme: (theme: Theme) => void;
  setDensity: (density: Density) => void;
  setAccentHue: (hue: number) => void;
  setSidebarPanel: (panel: SidebarPanel) => void;
  setPublishKitOpen: (open: boolean) => void;
  setEditorMode: (mode: EditorMode) => void;
  setEditDraft: (draft: string | null) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  rightPanelOpen: true,
  rightPanelTab: "pipeline",
  theme: (typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light") as Theme,
  density: "default" as Density,
  accentHue: 255,
  sidebarPanel: null,
  publishKitOpen: false,
  editorMode: "view" as EditorMode,
  editDraft: null as string | null,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab }),
  setTheme: (theme) => set({ theme }),
  setDensity: (density) => set({ density }),
  setAccentHue: (hue) => set({ accentHue: hue }),
  setSidebarPanel: (panel) =>
    set((s) => ({ sidebarPanel: s.sidebarPanel === panel ? null : panel })),
  setPublishKitOpen: (open) => set({ publishKitOpen: open }),
  setEditorMode: (mode) => set({ editorMode: mode, editDraft: mode === "view" ? null : undefined }),
  setEditDraft: (draft) => set({ editDraft: draft }),
}));
