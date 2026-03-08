// 招考信息类型定义
export interface RecruitmentInfo {
  id: number;
  source_id: string;
  title: string;
  exam_type: string;
  area: string;
  province: string;
  city: string;
  district: string;
  publish_date: string;
  registration_start: string;
  registration_end: string;
  exam_date: string;
  recruitment_count: number;
  status: string;
  source_url: string;
  content: string;
  ai_summary: string;
  attachments: string; // JSON string of attachment links
  tags: string; // JSON string
  source_site: string;
  created_at: string;
}

export interface RecruitmentInfoListResponse {
  items: RecruitmentInfo[];
  total: number;
  page: number;
  page_size: number;
}

export interface RecruitmentInfoFilters {
  exam_type?: string;
  province?: string;
  city?: string;
  status?: string;
  keyword?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface RecruitmentInfoFilterOptions {
  exam_types: string[];
  provinces: string[];
  cities: string[];
  statuses: string[];
}

export interface CrawlerConfig {
  id: number;
  name: string;
  target_url: string;
  interval_minutes: number;
  is_active: boolean;
  session_valid: boolean;
  last_crawl_at: string;
  last_crawl_status: string;
  last_error: string;
  total_crawled: number;
  ai_enabled: boolean;
  ai_model: string;
  ai_api_key: string;
  ai_base_url: string;
  ai_prompt: string;
  created_at: string;
}

export interface CrawlerStatus {
  configs: CrawlerConfig[];
  scheduler_running: boolean;
}
