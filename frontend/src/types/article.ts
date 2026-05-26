export interface Article {
  id: number;
  slug: string;
  title: string | null;
  topic: string;
  category: string | null;
  format_id: string;
  status: ArticleStatus;
  content_path: string | null;
  word_count: number;
  image_count: number;
  tags: string[];
  reference_count: number;
  section_count: number;
  thumbnail_path: string;
  created_at: string;
  updated_at: string;
}

export type ArticleStatus =
  | "draft"
  | "researching"
  | "outlining"
  | "generating"
  | "validating"
  | "review"
  | "gate_one"
  | "published"
  | "failed";

export interface ArticleCreate {
  topic: string;
  title?: string;
  format_id?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
