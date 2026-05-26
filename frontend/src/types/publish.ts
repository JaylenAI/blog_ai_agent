export interface PublishKitImage {
  name: string;
  url: string;
}

export interface PublishKitDiagram {
  name: string;
  content: string;
}

export interface ReferenceItem {
  url: string;
  title: string;
  summary: string;
  relevance_score: number;
  source_type: string;
}

export interface PublishKit {
  title: string;
  category: string;
  tags: string[];
  markdown: string | null;
  html: string | null;
  images: PublishKitImage[];
  diagrams: PublishKitDiagram[];
  references: ReferenceItem[];
  thumbnail_url: string | null;
  word_count: number;
  status: string;
}

export interface ObsidianSettings {
  vault_path: string;
  frontmatter_tags: string[];
  auto_save: boolean;
}

export interface GeneralSettings {
  tistory_blog_url: string;
  stage_timeout: number;
  image_generation_enabled: boolean;
  max_images_per_article: number;
  log_level: string;
}

export interface BatchUpdateRequest {
  article_ids: number[];
  category?: string;
  tags?: string[];
  status?: string;
}
