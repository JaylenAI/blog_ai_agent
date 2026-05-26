import { z } from "zod";

export const ArticleStatusSchema = z.enum([
  "draft",
  "researching",
  "outlining",
  "generating",
  "validating",
  "review",
  "gate_one",
  "published",
  "failed",
]);

export const ArticleSchema = z.object({
  id: z.number(),
  slug: z.string(),
  title: z.string().nullable(),
  topic: z.string(),
  category: z.string().nullable(),
  format_id: z.string(),
  status: ArticleStatusSchema,
  content_path: z.string().nullable(),
  word_count: z.number(),
  image_count: z.number(),
  tags: z.array(z.string()),
  reference_count: z.number(),
  section_count: z.number(),
  thumbnail_path: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const ArticleListSchema = z.object({
  items: z.array(ArticleSchema),
  total: z.number(),
  page: z.number(),
  limit: z.number(),
});

export const PipelineRunSchema = z.object({
  id: z.number(),
  article_id: z.number(),
  current_stage: z.string(),
  status: z.string(),
  error_message: z.string().optional(),
  started_at: z.string(),
  completed_at: z.string().nullable(),
});

export const ValidationItemSchema = z.object({
  category: z.enum(["style", "seo", "aeo", "geo"]),
  item: z.string(),
  passed: z.boolean(),
  score: z.number(),
  message: z.string(),
});

export const ValidationSummarySchema = z.object({
  total: z.number(),
  passed: z.number(),
  failed: z.number(),
  score: z.number(),
  by_category: z.record(
    z.string(),
    z.object({ total: z.number(), passed: z.number() }),
  ),
});

export const ValidationResultSchema = z.object({
  validations: z.array(ValidationItemSchema),
  summary: ValidationSummarySchema,
});

export const BlogFormatSchema = z.object({
  id: z.string(),
  name: z.string(),
  name_en: z.string(),
  description: z.string(),
  icon: z.string(),
  section_count_min: z.number(),
  section_count_max: z.number(),
  char_count_standard: z.tuple([z.number(), z.number()]),
});

export const FormatSuggestionSchema = z.object({
  format_id: z.string(),
  name: z.string(),
  icon: z.string(),
  confidence: z.number(),
  reason: z.string(),
});

export const ReferenceItemSchema = z.object({
  url: z.string(),
  title: z.string(),
  summary: z.string(),
  relevance_score: z.number(),
  source_type: z.string(),
});

export const PublishKitSchema = z.object({
  title: z.string(),
  category: z.string(),
  tags: z.array(z.string()),
  markdown: z.string().nullable(),
  html: z.string().nullable(),
  images: z.array(z.object({ name: z.string(), url: z.string() })),
  diagrams: z.array(z.object({ name: z.string(), content: z.string() })),
  references: z.array(ReferenceItemSchema),
  thumbnail_url: z.string().nullable(),
  word_count: z.number(),
  status: z.string(),
});

export const ObsidianSettingsSchema = z.object({
  vault_path: z.string(),
  frontmatter_tags: z.array(z.string()),
  auto_save: z.boolean(),
});

export const GeneralSettingsSchema = z.object({
  tistory_blog_url: z.string(),
  stage_timeout: z.number(),
  image_generation_enabled: z.boolean(),
  max_images_per_article: z.number(),
  log_level: z.string(),
});
