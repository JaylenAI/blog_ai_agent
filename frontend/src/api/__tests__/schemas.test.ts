import { describe, it, expect } from "vitest";
import {
  ArticleSchema,
  ArticleListSchema,
  PipelineRunSchema,
  ValidationItemSchema,
  ValidationSummarySchema,
  ValidationResultSchema,
  BlogFormatSchema,
  FormatSuggestionSchema,
  PublishKitSchema,
  ObsidianSettingsSchema,
  GeneralSettingsSchema,
} from "../schemas";

describe("ArticleSchema", () => {
  const valid = {
    id: 1,
    slug: "test",
    title: "제목",
    topic: "주제",
    category: "AI",
    format_id: "concept",
    status: "draft",
    content_path: null,
    word_count: 5000,
    image_count: 3,
    created_at: "2026-01-01",
    updated_at: "2026-01-01",
  };

  it("accepts valid article", () => {
    expect(ArticleSchema.parse(valid)).toEqual(valid);
  });

  it("accepts nullable title", () => {
    const result = ArticleSchema.parse({ ...valid, title: null });
    expect(result.title).toBeNull();
  });

  it("accepts optional tags", () => {
    const result = ArticleSchema.parse({ ...valid, tags: ["AI", "RAG"] });
    expect(result.tags).toEqual(["AI", "RAG"]);
  });

  it("rejects invalid status", () => {
    expect(() =>
      ArticleSchema.parse({ ...valid, status: "invalid_status" }),
    ).toThrow();
  });

  it("rejects missing required fields", () => {
    expect(() => ArticleSchema.parse({ id: 1 })).toThrow();
  });
});

describe("ArticleListSchema", () => {
  it("accepts valid article list", () => {
    const data = {
      items: [
        {
          id: 1,
          slug: "a",
          title: null,
          topic: "t",
          category: null,
          format_id: "concept",
          status: "draft",
          content_path: null,
          word_count: 0,
          image_count: 0,
          created_at: "",
          updated_at: "",
        },
      ],
      total: 1,
      page: 1,
      limit: 20,
    };
    expect(ArticleListSchema.parse(data).items).toHaveLength(1);
  });
});

describe("PipelineRunSchema", () => {
  it("accepts valid run", () => {
    const run = {
      id: 1,
      article_id: 2,
      current_stage: "researcher",
      status: "running",
      started_at: "2026-01-01T00:00:00",
      completed_at: null,
    };
    expect(PipelineRunSchema.parse(run).id).toBe(1);
  });

  it("accepts nullable completed_at", () => {
    const run = {
      id: 1,
      article_id: 2,
      current_stage: "researcher",
      status: "running",
      started_at: "2026-01-01",
      completed_at: "2026-01-01T01:00:00",
    };
    expect(PipelineRunSchema.parse(run).completed_at).toBe(
      "2026-01-01T01:00:00",
    );
  });

  it("accepts optional error_message", () => {
    const run = {
      id: 1,
      article_id: 2,
      current_stage: "researcher",
      status: "failed",
      error_message: "timeout",
      started_at: "2026-01-01",
      completed_at: null,
    };
    expect(PipelineRunSchema.parse(run).error_message).toBe("timeout");
  });
});

describe("ValidationSchemas", () => {
  it("accepts valid validation item", () => {
    const item = {
      category: "style",
      item: "제목 길이",
      passed: true,
      score: 0.95,
      message: "통과",
    };
    expect(ValidationItemSchema.parse(item).passed).toBe(true);
  });

  it("rejects invalid category", () => {
    expect(() =>
      ValidationItemSchema.parse({
        category: "invalid",
        item: "x",
        passed: true,
        score: 1,
        message: "",
      }),
    ).toThrow();
  });

  it("accepts valid validation summary", () => {
    const summary = {
      total: 22,
      passed: 20,
      failed: 2,
      score: 0.91,
      by_category: {
        style: { total: 14, passed: 13 },
        seo: { total: 4, passed: 4 },
      },
    };
    expect(ValidationSummarySchema.parse(summary).total).toBe(22);
  });

  it("accepts valid validation result", () => {
    const result = {
      validations: [
        {
          category: "seo",
          item: "메타 디스크립션",
          passed: true,
          score: 1,
          message: "OK",
        },
      ],
      summary: {
        total: 1,
        passed: 1,
        failed: 0,
        score: 1,
        by_category: { seo: { total: 1, passed: 1 } },
      },
    };
    expect(ValidationResultSchema.parse(result).validations).toHaveLength(1);
  });
});

describe("BlogFormatSchema", () => {
  it("accepts valid format", () => {
    const format = {
      id: "concept",
      name: "개념형",
      name_en: "Concept",
      description: "개념 해설",
      icon: "📚",
      section_count_min: 7,
      section_count_max: 9,
      char_count_standard: [6000, 8000] as [number, number],
    };
    expect(BlogFormatSchema.parse(format).id).toBe("concept");
  });

  it("rejects invalid char_count_standard (not tuple)", () => {
    expect(() =>
      BlogFormatSchema.parse({
        id: "x",
        name: "x",
        name_en: "x",
        description: "",
        icon: "",
        section_count_min: 1,
        section_count_max: 2,
        char_count_standard: [1000],
      }),
    ).toThrow();
  });
});

describe("FormatSuggestionSchema", () => {
  it("accepts valid suggestion", () => {
    const s = {
      format_id: "tutorial",
      name: "튜토리얼형",
      icon: "🛠️",
      confidence: 0.85,
      reason: "실습 중심",
    };
    expect(FormatSuggestionSchema.parse(s).confidence).toBe(0.85);
  });
});

describe("PublishKitSchema", () => {
  it("accepts valid publish kit", () => {
    const kit = {
      title: "제목",
      category: "AI",
      tags: ["tag1"],
      markdown: "# content",
      html: "<h1>content</h1>",
      images: [{ name: "thumb.png", url: "/img/thumb.png" }],
      diagrams: [{ name: "flow.mmd", content: "graph TD" }],
      word_count: 5000,
      status: "ready",
    };
    expect(PublishKitSchema.parse(kit).word_count).toBe(5000);
  });

  it("accepts null markdown and html", () => {
    const kit = {
      title: "",
      category: "",
      tags: [],
      markdown: null,
      html: null,
      images: [],
      diagrams: [],
      word_count: 0,
      status: "draft",
    };
    expect(PublishKitSchema.parse(kit).markdown).toBeNull();
  });
});

describe("ObsidianSettingsSchema", () => {
  it("accepts valid settings", () => {
    const s = {
      vault_path: "/vault",
      frontmatter_tags: ["project/blog"],
      auto_save: true,
    };
    expect(ObsidianSettingsSchema.parse(s).auto_save).toBe(true);
  });
});

describe("GeneralSettingsSchema", () => {
  it("accepts valid settings", () => {
    const s = {
      tistory_blog_url: "https://jaylenhan.tistory.com",
      stage_timeout: 600,
      image_generation_enabled: true,
      max_images_per_article: 10,
      log_level: "INFO",
    };
    expect(GeneralSettingsSchema.parse(s).stage_timeout).toBe(600);
  });
});
