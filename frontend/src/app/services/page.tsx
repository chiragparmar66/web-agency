"use client";

import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  Code2,
  Cpu,
  Globe,
  Layers,
  ShieldCheck,
  Zap,
} from "lucide-react";
import { motion } from "motion/react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { fadeUpVariants, VIEWPORT_ONCE, cardHoverProps } from "@/lib/motion";

export default function ServicesPage() {
  const serviceList = [
    {
      id: "business-websites",
      title: "Bespoke Business Websites",
      category: "Corporate & Enterprise",
      icon: Globe,
      price: "From ₹4,999",
      delivery: "5–10 Business Days",
      summary:
        "Custom, multi-page corporate websites designed specifically for modern Indian enterprises, healthcare providers, law firms, and consulting firms.",
      deliverables: [
        "Up to 5–10 tailored responsive pages (Home, About, Services, Team, Contact)",
        "Semantic HTML5 & modern CSS with zero bloated visual builders",
        "Mobile-first responsive layout tested across iOS, Android, and Desktop",
        "Complete technical SEO setup (meta tags, OpenGraph, sitemap.xml)",
        "Direct inquiry capture & WhatsApp fast-track routing",
        "Domain linking, SSL certification & deployment assistance",
      ],
    },
    {
      id: "landing-pages",
      title: "High-Converting Landing Pages",
      category: "Performance Marketing",
      icon: Zap,
      price: "From ₹2,999",
      delivery: "3–5 Business Days",
      summary:
        "Laser-focused single-page websites engineered to convert ad traffic, social campaigns, and organic visitors into paying customers or qualified leads.",
      deliverables: [
        "Persuasive, conversion-driven section architecture",
        "Sub-1-second page load times optimized for Indian mobile data networks",
        "Direct lead capture forms with instant email/WhatsApp notification",
        "A/B testing-ready modular structure",
        "Analytics and meta-pixel event tracking setup",
      ],
    },
    {
      id: "portfolio-websites",
      title: "Studio & Portfolio Websites",
      category: "Creative & Professional",
      icon: Layers,
      price: "From ₹3,999",
      delivery: "5–7 Business Days",
      summary:
        "Distinctive digital showcases designed with high typographic standards for architects, interior designers, photographers, consultants, and creative studios.",
      deliverables: [
        "Curated visual gallery layouts with high-resolution image optimization",
        "Deep-dive project case study templates",
        "Editorial typography and restrained color harmony",
        "Direct commission inquiry form",
        "Lightweight, snappy transitions that don't compromise speed",
      ],
    },
    {
      id: "ecommerce-websites",
      title: "E-Commerce Platforms",
      category: "Online Retail",
      icon: Code2,
      price: "From ₹14,999",
      delivery: "14–21 Business Days",
      summary:
        "Independent online storefronts integrated with Indian payment infrastructure (Razorpay, UPI, Credit/Debit cards, NetBanking) with zero platform commission per transaction.",
      deliverables: [
        "Clean product catalog with category and price filtering",
        "Frictionless checkout experience optimized for mobile screens",
        "Razorpay / UPI payment gateway integration with backend verification",
        "Customer accounts, order tracking, and email receipts",
        "GST-compliant automated invoicing layout",
      ],
    },
    {
      id: "website-maintenance",
      title: "Performance & Maintenance Retainer",
      category: "Ongoing Engineering",
      icon: ShieldCheck,
      price: "From ₹1,999 / month",
      delivery: "Continuous Support",
      summary:
        "Dedicated monthly engineering care to keep your business website secure, fast-loading, up-to-date, and protected against downtime.",
      deliverables: [
        "Core Web Vitals monitoring & performance tuning",
        "Automated weekly backups stored securely off-site",
        "Security patching, dependency upgrades, and SSL renewal checks",
        "Priority developer hours for monthly content and layout updates",
        "Direct developer access via email and WhatsApp",
      ],
    },
    {
      id: "custom-web-apps",
      title: "Custom Web Applications",
      category: "Bespoke Software",
      icon: Cpu,
      price: "From ₹24,999",
      delivery: "Custom Milestone Scope",
      summary:
        "Tailored web software, client portals, and operational management systems engineered for complex business requirements using Next.js, FastAPI, and PostgreSQL.",
      deliverables: [
        "Relational database design and ACID transaction safety",
        "Role-Based Access Control (RBAC) with secure JWT authentication",
        "Clean, responsive administrative dashboards",
        "Third-party REST API integrations and webhook listeners",
        "Full staging environment and production container deployment",
      ],
    },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <Navbar />

      <main className="flex-1">
        {/* Page Header */}
        <section className="border-b border-slate-200 bg-white py-16 sm:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              animate="visible"
              className="max-w-3xl"
            >
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">
                Our Capabilities
              </span>
              <h1 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
                Professional Web Development Services
              </h1>
              <p className="mt-4 text-base sm:text-lg text-slate-600 leading-relaxed">
                We build real, bespoke web solutions for businesses that value craftsmanship, speed, and reliability. Every website is built from scratch by our engineers with clean, deterministic code.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Services List */}
        <section className="py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="space-y-12">
              {serviceList.map((service) => {
                const IconComponent = service.icon;
                return (
                  <motion.div
                    key={service.id}
                    id={service.id}
                    variants={fadeUpVariants}
                    initial="hidden"
                    whileInView="visible"
                    viewport={VIEWPORT_ONCE}
                    {...cardHoverProps}
                    className="scroll-mt-24 rounded-lg border border-slate-200 bg-white p-8 sm:p-10 shadow-sm transition-all hover:border-slate-300 hover:shadow-md"
                  >
                    <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-8">
                      {/* Left: Service Info */}
                      <div className="lg:max-w-xl">
                        <div className="flex items-center gap-3 mb-4">
                          <div className="flex h-10 w-10 items-center justify-center rounded bg-slate-100 text-slate-800">
                            <IconComponent className="h-5 w-5" />
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                              {service.category}
                            </span>
                            <h2 className="text-2xl font-bold text-slate-900">
                              {service.title}
                            </h2>
                          </div>
                        </div>

                        <p className="text-sm text-slate-600 leading-relaxed mb-6">
                          {service.summary}
                        </p>

                        <div className="flex flex-wrap items-center gap-6 text-xs text-slate-500 pt-2 border-t border-slate-100">
                          <div className="flex items-center gap-1.5 font-semibold text-slate-800">
                            <span>Starting at:</span>
                            <span className="text-blue-600 font-bold">{service.price}</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-slate-600">
                            <Clock className="h-3.5 w-3.5" />
                            <span>Estimated Delivery: {service.delivery}</span>
                          </div>
                        </div>
                      </div>

                      {/* Right: Deliverables List & CTA */}
                      <div className="lg:max-w-md w-full bg-slate-50 rounded-lg p-6 border border-slate-100 flex flex-col justify-between">
                        <div>
                          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
                            Key Deliverables Included
                          </h3>
                          <ul className="space-y-2.5 text-xs text-slate-600">
                            {service.deliverables.map((item, idx) => (
                              <li key={idx} className="flex items-start gap-2">
                                <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="mt-6 pt-4 border-t border-slate-200">
                          <Link
                            href={`/contact?service=${service.id}`}
                            className="w-full inline-flex items-center justify-center gap-2 rounded bg-slate-900 px-4 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
                          >
                            <span>Inquire for {service.title}</span>
                            <ArrowRight className="h-3.5 w-3.5" />
                          </Link>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Bottom Contact Section */}
        <section className="bg-white border-t border-slate-200 py-16 text-center">
          <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-slate-900">
              Need a tailored scope or custom architectural consultation?
            </h2>
            <p className="mt-3 text-sm text-slate-600 max-w-xl mx-auto">
              We frequently handle multi-system integrations, data migrations, and custom enterprise requirements. Contact our development team to discuss your specifications.
            </p>
            <div className="mt-6 flex justify-center">
              <Link
                href="/contact"
                className="inline-flex items-center gap-2 rounded bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition-colors"
              >
                <span>Request Custom Project Consultation</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
