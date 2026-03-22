export interface Position {
  id: number;
  title?: string;
  department?: string;
  location?: string;
  selection_location?: string;
  city?: string;
  education?: string;
  major?: string;
  degree?: string;
  political_status?: string;
  work_experience?: string;
  other_requirements?: string;
  recruitment_count: number;
  exam_type?: string;
  exam_category?: string;
  year?: number;
  position_code?: string;
  status?: string;
  apply_count?: number;
  successful_applicants?: number;
  competition_ratio?: number;
  estimated_competition_ratio?: number;
  difficulty_level?: string;
  min_interview_score?: number;
  max_interview_score?: number;
  max_xingce_score?: number;
  max_shenlun_score?: number;
  professional_skills?: string;
  // 国考扩展字段
  province?: string;
  hiring_unit?: string;
  institution_level?: string;
  position_attribute?: string;
  position_distribution?: string;
  interview_ratio?: string;
  settlement_location?: string;
  grassroots_project?: string;
  // 事业编扩展字段
  supervising_dept?: string;
  funding_source?: string;
  exam_ratio?: string;
  recruitment_target?: string;
  position_level?: string;
  remark?: string;
  exam_weight_ratio?: string;
  description?: string;
  eligibility_status?: 'hard_pass' | 'manual_review_needed' | 'hard_fail';
  match_source?: string;
  match_reasons?: string[];
  sort_reasons?: string[];
  recommendation_tier?: '冲刺' | '稳妥' | '保底';
  recommendation_reasons?: string[];
  post_nature?: string;
  similarity_score?: number;
  risk_tags?: string[];
  risk_reasons?: string[];
  risk_score?: number;
  manual_review_flags?: string[];
  normalized_funding_source?: string;
  normalized_recruitment_target?: string;
}

export interface PositionDetailExtension {
  history_items: Position[];
  related_items: Position[];
}

export interface PositionFilterOptions {
  cities: string[];
  educations: string[];
  exam_categories: string[];
  locations: string[];
  years?: number[];
  exam_types?: string[];
  city_locations?: Record<string, string[]>;
  // 国考筛选项
  provinces?: string[];
  province_cities?: Record<string, string[]>;
  institution_levels?: string[];
  // 事业编筛选项
  funding_sources?: string[];
  recruitment_targets?: string[];
}

export interface MatchSummary {
  total_positions: number;
  matched?: number;
  education_excluded?: number;
  major_excluded?: number;
  political_excluded?: number;
  work_experience_excluded?: number;
  gender_excluded?: number;
  hard_pass?: number;
  manual_review_needed?: number;
  hard_fail?: number;
  sprint_count?: number;
  stable_count?: number;
  safe_count?: number;
  sort_basis?: string[];
}

export interface MatchRequest {
  year: number;
  exam_type: string;
  education: string;
  major: string;
  political_status?: string;
  work_years?: number;
  gender?: string;
  city?: string;
  exam_category?: string;
  location?: string;
  province?: string;
  institution_level?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: string;
}

export interface MatchResult {
  items: Position[];
  total: number;
  page: number;
  page_size: number;
  match_summary?: MatchSummary;
  summary?: MatchSummary;
}

export interface ShiyeSelectionFilterOptions {
  years: number[];
  cities: string[];
  locations: string[];
  funding_sources: string[];
  recruitment_targets: string[];
  post_natures: string[];
  risk_tags: string[];
  city_locations?: Record<string, string[]>;
}
