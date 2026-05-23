import { useUIStore } from "./ui-store";
import { useArticleStore } from "./article-store";
import { useToastStore } from "./toast-store";
import type { Toast } from "./toast-store";

export { useUIStore, useArticleStore, useToastStore };
export type { Toast };

export type SidebarPanel = null | "pipelines" | "style-guide" | "tistory" | "subagents" | "skills" | "eval" | "mcp" | "dashboard" | "settings";
export type EditorMode = "view" | "edit";

type MergedState = ReturnType<typeof useUIStore.getState> &
  ReturnType<typeof useArticleStore.getState> &
  ReturnType<typeof useToastStore.getState>;

export function useAppStore(): MergedState;
export function useAppStore<T>(selector: (s: MergedState) => T): T;
export function useAppStore<T>(selector?: (s: MergedState) => T): MergedState | T {
  const ui = useUIStore();
  const article = useArticleStore();
  const toast = useToastStore();

  const merged = { ...ui, ...article, ...toast } as MergedState;
  return selector ? selector(merged) : merged;
}
