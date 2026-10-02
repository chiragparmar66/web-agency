export const APP_CONFIG = {
  name: process.env.NEXT_PUBLIC_STUDIO_NAME || "Nexus Studio",
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  whatsappNumber: process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || "+919876543210",
  supportEmail: process.env.NEXT_PUBLIC_SUPPORT_EMAIL || "hello@nexusstudio.dev",
};

export const PROJECT_STATUS_LABELS: Record<string, { label: string; color: string }> = {
  LEAD: { label: "Lead Capture", color: "bg-gray-100 text-gray-800" },
  NEW: { label: "Project Created", color: "bg-blue-100 text-blue-800" },
  REQUIREMENTS_PENDING: { label: "Awaiting Requirements", color: "bg-amber-100 text-amber-800" },
  PENDING_APPROVAL: { label: "Pending Admin Approval", color: "bg-amber-100 text-amber-800" },
  BUILDING: { label: "AI Website Synthesis", color: "bg-violet-100 text-violet-800" },
  IN_PROGRESS: { label: "In Development", color: "bg-indigo-100 text-indigo-800" },
  DESIGN_REVIEW: { label: "Design Review", color: "bg-purple-100 text-purple-800" },
  DEVELOPMENT: { label: "Engineering & QA", color: "bg-cyan-100 text-cyan-800" },
  CLIENT_REVIEW: { label: "Preview Ready for Review", color: "bg-emerald-100 text-emerald-800" },
  REVISION_REQUESTED: { label: "Revisions in Progress", color: "bg-orange-100 text-orange-800" },
  APPROVED: { label: "Approved by Client", color: "bg-teal-100 text-teal-800" },
  PAYMENT_PENDING: { label: "Payment Settlement", color: "bg-yellow-100 text-yellow-800" },
  DEPLOYING: { label: "DNS & Production Deployment", color: "bg-blue-100 text-blue-800" },
  LIVE: { label: "Live in Production", color: "bg-green-100 text-green-800" },
  COMPLETED: { label: "Completed", color: "bg-emerald-100 text-emerald-800" },
};
