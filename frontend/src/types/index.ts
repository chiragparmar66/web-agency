export type UserRole = "ADMIN" | "DEVELOPER" | "CUSTOMER";

export type ProjectStatus =
  | "LEAD"
  | "NEW"
  | "REQUIREMENTS_PENDING"
  | "IN_PROGRESS"
  | "DESIGN_REVIEW"
  | "DEVELOPMENT"
  | "CLIENT_REVIEW"
  | "REVISION_REQUESTED"
  | "APPROVED"
  | "PAYMENT_PENDING"
  | "DEPLOYING"
  | "LIVE"
  | "COMPLETED";

export type RevisionStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "REJECTED";

export type PaymentStatus = "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED";

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
}

export interface CustomerProfile {
  id: string;
  user_id?: string;
  full_name: string;
  email?: string;
  phone: string;
  company_name?: string;
  business_type?: string;
  city?: string;
  state?: string;
  country: string;
  gstin?: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  customer_profile?: CustomerProfile;
}

export interface ServiceItem {
  id: string;
  slug: string;
  title: string;
  short_description: string;
  full_description: string;
  deliverables: string[];
  icon_name: string;
  starting_price_inr: number;
  sort_order: number;
}

export interface PortfolioItem {
  id: string;
  title: string;
  slug: string;
  client_name: string;
  industry: string;
  description: string;
  technologies: string[];
  thumbnail_url: string;
  gallery_urls: string[];
  live_demo_url?: string;
  results_summary?: string;
  is_featured: boolean;
  sort_order: number;
}

export interface ProjectItem {
  id: string;
  project_number: string;
  customer_id: string;
  package_id?: string;
  title: string;
  business_name: string;
  status: ProjectStatus;
  preview_url?: string;
  production_url?: string;
  custom_domain?: string;
  revisions_used: number;
  created_at: string;
  updated_at: string;
}

export interface ActivityItem {
  id: string;
  action_type: string;
  old_status?: string;
  new_status?: string;
  note?: string;
  created_at: string;
}

export interface ProjectDetail extends ProjectItem {
  activities: ActivityItem[];
}

export interface DashboardSummary {
  total_projects: number;
  active_project?: ProjectItem;
  recent_projects: ProjectItem[];
  recent_activities: ActivityItem[];
}

export interface PricingPackage {
  id: string;
  slug: string;
  name: string;
  price_inr: number;
  description: string;
  features: string[];
  delivery_days: number;
  revisions_included: number;
  is_popular?: boolean;
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  database_connected: boolean;
  timestamp: string;
}

export interface RequirementItem {
  id: string;
  project_id: string;
  business_summary?: string;
  target_audience?: string;
  services_offered?: string;
  color_preferences?: string;
  reference_websites: string[];
  social_links: Record<string, string>;
  contact_email?: string;
  contact_phone?: string;
  physical_address?: string;
  special_requests?: string;
  is_submitted: boolean;
  submitted_at?: string;
  created_at: string;
  updated_at: string;
}

export interface MessageItem {
  id: string;
  project_id: string;
  sender_user_id: string;
  message: string;
  is_internal_note: boolean;
  created_at: string;
}
