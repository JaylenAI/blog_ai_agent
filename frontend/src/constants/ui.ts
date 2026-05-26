export const TOAST = {
  AUTO_DISMISS_MS: 5000,
  POSITION_BOTTOM: 20,
  POSITION_RIGHT: 20,
  Z_INDEX: 9999,
  MAX_WIDTH: 400,
  GAP: 10,
  FONT_SIZE: 13,
} as const;

export const DEBOUNCE = {
  FORMAT_SUGGEST_MS: 500,
} as const;

export const PIPELINE = {
  MAX_EVENTS: 500,
  SSE_RETRY_DELAYS: [1500, 3000, 6000] as const,
} as const;

export const CONTENT_PREVIEW = {
  MAX_CHARS: 500,
  MAX_HEIGHT_PX: 384,
} as const;

export const INPUT_LIMITS = {
  AVATAR_INITIALS_MAX: 4,
  MAX_IMAGES_PER_ARTICLE: 10,
  MAX_TAGS: 10,
} as const;
