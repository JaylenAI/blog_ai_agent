export interface BlogFormat {
  id: string;
  name: string;
  name_en: string;
  description: string;
  icon: string;
  section_count_min: number;
  section_count_max: number;
  char_count_standard: [number, number];
}

export interface FormatSuggestion {
  format_id: string;
  name: string;
  icon: string;
  confidence: number;
  reason: string;
}
