import { useEffect, useCallback } from "react";
import { api } from "../api/client";
import { useAppStore } from "../stores/app-store";
import type { Article } from "../types/article";

export function useArticles() {
  const { setArticles, setArticlesLoading } = useAppStore();

  const fetchArticles = useCallback(async () => {
    setArticlesLoading(true);
    try {
      const res = await api.articles.list();
      if (res.success && res.data) {
        setArticles(res.data.items as Article[]);
      }
    } finally {
      setArticlesLoading(false);
    }
  }, [setArticles, setArticlesLoading]);

  useEffect(() => {
    void fetchArticles();
  }, [fetchArticles]);

  return { refetch: fetchArticles };
}
