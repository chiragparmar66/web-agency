export type UserRole = "ADMIN" | "DEVELOPER" | "CUSTOMER";

export type ProjectStatus =
  | "LEAD"
  | "NEW"
  | "REQUIREMENTS_PENDING"
  | "PENDING_APPROVAL"
  | "BUILDING"
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

export type BuildStatus = "QUEUED" | "ANALYZING" | "GENERATING" | "COMPLETED" | "FAILED";

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
  package?: PricingPackage;
  title: string;
  business_name: string;
  status: ProjectStatus;
  preview_url?: string;
  production_url?: string;
  custom_domain?: string;
  assigned_developer_id?: string;
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
  sender_name?: string;
  sender_role?: string;
  message: string;
  is_internal_note: boolean;
  created_at: string;
}

export type FileCategory =
  | "LOGO"
  | "IMAGE"
  | "DOCUMENT"
  | "BRAND_ASSET"
  | "REVISION_ATTACHMENT"
  | "PREVIEW_SCREENSHOT";

export interface ProjectFileItem {
  id: string;
  project_id: string;
  revision_id?: string;
  file_category: FileCategory;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  uploaded_by_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface RevisionItem {
  id: string;
  project_id: string;
  revision_number: number;
  requested_by_user_id: string;
  description: string;
  status: RevisionStatus;
  admin_response?: string;
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  attachments: ProjectFileItem[];
}

export interface StaffUserItem {
  id: string;
  full_name: string;
  email: string;
  phone?: string;
  role: UserRole;
  is_active: boolean;
}

export interface InquiryItem {
  id: string;
  name: string;
  phone?: string;
  email?: string;
  subject?: string;
  business_name?: string;
  business_type?: string;
  city?: string;
  source: string;
  selected_package?: string;
  message?: string;
  status: string;
  read_at?: string | null;
  created_at: string;
}

export interface AdminProjectItem extends ProjectItem {
  customer?: {
    id: string;
    full_name: string;
    email?: string;
    phone: string;
    company_name?: string;
  };
  assigned_developer?: StaffUserItem;
  package_name?: string;
  advance_payment_status?: "PAID" | "PENDING";
  total_paid_inr?: number;
}

export type PaymentType = "ADVANCE" | "MILESTONE" | "FINAL" | "FULL";

export interface PaymentItem {
  id: string;
  project_id: string;
  customer_id: string;
  payment_type: PaymentType;
  amount_inr: number;
  status: PaymentStatus;
  razorpay_order_id?: string;
  razorpay_payment_id?: string;
  invoice_number?: string;
  paid_at?: string;
  created_at: string;
}

export interface OrderData {
  order_id: string;
  amount_inr: number;
  amount_paise: number;
  currency: string;
  key_id: string;
  payment_id: string;
  invoice_number: string;
  customer_name: string;
  customer_email?: string;
  customer_phone: string;
}

export interface InvoiceDetail {
  invoice_number: string;
  payment_id: string;
  project_number: string;
  project_title: string;
  customer_name: string;
  customer_email?: string;
  customer_phone: string;
  customer_company?: string;
  customer_gstin?: string;
  payment_type: PaymentType;
  amount_inr: number;
  currency: string;
  status: PaymentStatus;
  paid_at?: string;
  created_at: string;
}

export interface WebsiteBuildItem {
  id: string;
  project_id: string;
  revision_id?: string | null;
  version_number: number;
  status: BuildStatus;
  review_status?: "PENDING_REVIEW" | "APPROVED" | "REJECTED";
  review_notes?: string | null;
  reviewed_by_user_id?: string | null;
  reviewed_at?: string | null;
  client_approved?: boolean;
  client_approved_at?: string | null;
  client_feedback?: string | null;
  spec_data?: Record<string, any> | null;
  architecture_data?: Record<string, any> | null;
  design_system?: Record<string, any> | null;
  generated_code_path?: string | null;
  preview_url?: string | null;
  admin_notes?: string | null;
  is_active: boolean;
  approved_by_user_id?: string | null;
  approved_at?: string | null;
  created_at: string;
  updated_at: string;
}

export type WebsiteBuild = WebsiteBuildItem;

export type BuildReviewStatus = "PENDING_REVIEW" | "APPROVED" | "REJECTED";

export interface BuildReviewDetail {
  project_id: string;
  project_title: string;
  build_id: string;
  version_number: number;
  status: BuildStatus;
  review_status: BuildReviewStatus;
  review_notes?: string | null;
  client_approved?: boolean;
  client_approved_at?: string | null;
  client_feedback?: string | null;
  is_active: boolean;
  created_at: string;
  approved_at?: string | null;
  reviewed_at?: string | null;
  reviewed_by_name?: string | null;
  providers_used: Record<string, string>;
  entry_file: string;
  files_count: number;
  total_size_bytes: number;
  validation_score: number;
  validation_findings: Array<{
    file_path: string;
    severity: "ERROR" | "WARNING" | "INFO";
    rule: string;
    message: string;
  }>;
  spec_summary: Record<string, any>;
  architecture_summary?: Record<string, any> | null;
  generated_code_path?: string | null;
  admin_notes?: string | null;
}

export interface BuildFileItem {
  path: string;
  file_type: string;
  size_bytes: number;
  is_text: boolean;
}

export interface BuildFileContent {
  path: string;
  file_type: string;
  size_bytes: number;
  content?: string | null;
  is_text: boolean;
  is_truncated: boolean;
}

export interface BuildApprovalPayload {
  admin_notes?: string;
  revision_id?: string;
  force_override_payment?: boolean;
  waive_payment?: boolean;
}

export interface ProjectAiContext {
  project_id: string;
  title: string;
  status: string;
  client_name: string;
  client_email: string;
  company_name?: string | null;
  client_phone?: string | null;
  package?: {
    id: string;
    name: string;
    slug: string;
    price_inr: number;
    advance_percentage: number;
    delivery_days: number;
    revision_limit: number;
    features: string[];
  } | null;
  requirements?: Record<string, any> | null;
  files: Array<{
    id: string;
    category: string;
    original_filename: string;
    mime_type: string;
    file_size_bytes: number;
  }>;
  files_by_category?: Record<string, any[]>;
  active_revision?: {
    id: string;
    revision_number: number;
    description: string;
    status: string;
  } | null;
  advance_payment_verified: boolean;
  ready_for_build: boolean;
  context_summary: {
    project_title: string;
    package_name: string;
    has_logo: boolean;
    total_files: number;
    suggested_pages: string[];
    color_preferences: string;
    advance_payment_verified: boolean;
    total_paid_inr: number;
  };
}

export type DeploymentStatus =
  | "NOT_READY"
  | "READY"
  | "QUEUED"
  | "DEPLOYING"
  | "DEPLOYED"
  | "FAILED"
  | "ROLLED_BACK";

export interface Deployment {
  id: string;
  project_id: string;
  build_id: string;
  version_number: number;
  status: DeploymentStatus;
  provider: string;
  provider_deployment_id?: string | null;
  live_url?: string | null;
  error_message?: string | null;
  deployed_by_user_id?: string | null;
  deployed_at?: string | null;
  deployment_metadata?: Record<string, any> | null;
  smoke_test_status?: string | null;
  smoke_test_details?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface DeploymentEligibility {
  is_eligible: boolean;
  build_completed: boolean;
  admin_approved: boolean;
  client_approved: boolean;
  final_payment_cleared: boolean;
  artifact_available: boolean;
  package_price_inr: number;
  total_paid_inr: number;
  remaining_balance_inr: number;
  blockers: string[];
}

export interface ClientBuildPreview {
  project_id: string;
  project_title: string;
  build_id: string;
  version_number: number;
  status: BuildStatus;
  review_status: BuildReviewStatus;
  client_approved: boolean;
  client_approved_at?: string | null;
  preview_url: string;
  entry_file: string;
  files_count: number;
  created_at: string;
}
