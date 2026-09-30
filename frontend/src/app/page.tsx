"use client";

import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
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
import {
  fadeUpVariants,
  staggerContainerVariants,
  cardHoverProps,
  buttonPressProps,
  VIEWPORT_ONCE,
} from "@/lib/motion";

export default function Home() {
  const capabilities = [
    {
      title: "Business Websites",
      description:
        "Fast, accessible digital presence for Indian enterprises, healthcare providers, law firms, and consulting agencies.",
      icon: Globe,
      href: "/services#business-websites",
    },
    {
      title: "High-Converting Landing Pages",
      description:
        "Focused single-page sites built for lead generation and product campaigns with under 1-second load times.",
      icon: Zap,
      href: "/services#landing-pages",
    },
    {
      title: "Portfolio & Studio Sites",
      description:
        "Distinctive digital showcases with refined typography for architects, designers, and creative professionals.",
      icon: Layers,
      href: "/services#portfolio-websites",
    },
    {
      title: "E-Commerce Platforms",
      description:
        "Custom online storefronts with Indian payment gateways (UPI, Cards, NetBanking) and zero commission per sale.",
      icon: Code2,
      href: "/services#ecommerce-websites",
    },
    {
      title: "Custom Web Applications",
      description:
        "Tailored web software, client portals, and internal workflows engineered with Next.js, FastAPI, and PostgreSQL.",
      icon: Cpu,
      href: "/services#custom-web-apps",
    },
    {
      title: "Maintenance & Performance",
      description:
        "Continuous Core Web Vitals monitoring, security updates, and priority developer support.",
      icon: ShieldCheck,
      href: "/services#website-maintenance",
    },
  ];

  const processSteps = [
    {
      step: "01",
      name: "Discovery & Requirements",
      description:
        "We understand your business model, target audience, brand identity, and technical requirements before writing a single line of code.",
    },
    {
      step: "02",
      name: "Visual & System Architecture",
      description:
        "We plan the wireframe structure, component hierarchy, typographic scale, and data model to ensure clear conversion paths.",
    },
    {
      step: "03",
      name: "Bespoke Engineering",
      description:
        "Handcrafted modern code using Next.js, TypeScript, and FastAPI. No bloated page builders, no slow plugins, no synthetic templates.",
    },
    {
      step: "04",
      name: "Staging Preview & Revisions",
      description:
        "You review the functional website on a private staging link and provide feedback through our structured revision workflow.",
    },
    {
      step: "05",
      name: "Deployment & Domain Linking",
      description:
        "We bind your custom domain, configure DNS records, verify SSL certificates, and hand over complete production documentation.",
    },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <Navbar />

      <main className="flex-1">
        {/* Hero Section with restrained stagger */}
        <section className="relative border-b border-slate-200 bg-white py-20 sm:py-28 overflow-hidden">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={staggerContainerVariants}
              initial="hidden"
              animate="visible"
              className="max-w-3xl"
            >
              <motion.div variants={fadeUpVariants}>
                <div className="inline-flex items-center gap-2 rounded border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-700 mb-6">
                  <span className="h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
                  <span>Professional Web Development Studio &bull; India</span>
                </div>
              </motion.div>

              <motion.h1
                variants={fadeUpVariants}
                className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.15]"
              >
                Custom web development engineered for real business growth.
              </motion.h1>

              <motion.p
                variants={fadeUpVariants}
                className="mt-6 text-lg text-slate-600 leading-relaxed max-w-2xl"
              >
                We design and build bespoke, high-performance websites and digital solutions for Indian businesses. Direct collaboration with experienced developers, transparent milestone delivery, and zero automated shortcuts.
              </motion.p>

              <motion.div
                variants={fadeUpVariants}
                className="mt-8 flex flex-wrap items-center gap-4"
              >
                <motion.div {...buttonPressProps}>
                  <Link
                    href="/contact"
                    className="inline-flex items-center justify-center gap-2 rounded bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition-colors shadow-sm"
                  >
                    <span>Start Your Project</span>
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </motion.div>
                <motion.div {...buttonPressProps}>
                  <Link
                    href="/services"
                    className="inline-flex items-center justify-center rounded border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    Explore Studio Services
                  </Link>
                </motion.div>
              </motion.div>

              {/* Trust Indicators */}
              <motion.div
                variants={fadeUpVariants}
                className="mt-12 pt-8 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-3 gap-6 text-xs text-slate-500"
              >
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Handcrafted Next.js & Python Code</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>GST Invoicing & Razorpay Verified</span>
                </div>
                <div className="flex items-center gap-2 col-span-2 sm:col-span-1">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Direct Developer Communication</span>
                </div>
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* Services Overview with scroll reveal */}
        <section className="py-20 bg-slate-50">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="flex flex-col md:flex-row md:items-end justify-between mb-12"
            >
              <div>
                <h2 className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-2">
                  What We Build
                </h2>
                <p className="text-3xl font-bold tracking-tight text-slate-900">
                  Comprehensive Web Development Services
                </p>
              </div>
              <Link
                href="/services"
                className="mt-4 md:mt-0 text-sm font-semibold text-slate-700 hover:text-blue-600 inline-flex items-center gap-1 transition-colors"
              >
                <span>View all service details</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </motion.div>

            <motion.div
              variants={staggerContainerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {capabilities.map((item) => {
                const IconComponent = item.icon;
                return (
                  <motion.div
                    key={item.title}
                    variants={fadeUpVariants}
                    {...cardHoverProps}
                    className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-6 transition-all hover:border-slate-300 hover:shadow-md"
                  >
                    <div>
                      <div className="flex h-10 w-10 items-center justify-center rounded bg-slate-100 text-slate-800 mb-4">
                        <IconComponent className="h-5 w-5" />
                      </div>
                      <h3 className="text-base font-bold text-slate-900 mb-2">
                        {item.title}
                      </h3>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {item.description}
                      </p>
                    </div>
                    <div className="mt-6 pt-4 border-t border-slate-100">
                      <Link
                        href={item.href}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
                      >
                        <span>Learn more</span>
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    </div>
                  </motion.div>
                );
              })}
            </motion.div>
          </div>
        </section>

        {/* Development Process with progressive cards */}
        <section className="py-20 bg-white border-y border-slate-200">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="max-w-2xl mb-16"
            >
              <h2 className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-2">
                Our Methodology
              </h2>
              <p className="text-3xl font-bold tracking-tight text-slate-900">
                A disciplined, predictable development lifecycle
              </p>
              <p className="mt-4 text-sm text-slate-600 leading-relaxed">
                We respect your timeline and investment. Every project follows a clear 5-stage progression with defined deliverables at each milestone.
              </p>
            </motion.div>

            <motion.div
              variants={staggerContainerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="grid grid-cols-1 md:grid-cols-5 gap-6"
            >
              {processSteps.map((step) => (
                <motion.div
                  key={step.step}
                  variants={fadeUpVariants}
                  {...cardHoverProps}
                  className="rounded-lg border border-slate-200 bg-slate-50 p-6 flex flex-col justify-between transition-all hover:bg-white hover:border-slate-300 hover:shadow-sm"
                >
                  <div>
                    <span className="font-mono text-2xl font-bold text-slate-400">
                      {step.step}
                    </span>
                    <h3 className="mt-3 text-sm font-bold text-slate-900">
                      {step.name}
                    </h3>
                    <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Selected Work Preview */}
        <section className="py-20 bg-slate-50">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="max-w-2xl mb-12"
            >
              <h2 className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-2">
                Portfolio Showcase
              </h2>
              <p className="text-3xl font-bold tracking-tight text-slate-900">
                Selected Work & Case Studies
              </p>
            </motion.div>

            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="rounded-lg border border-slate-200 bg-white p-12 text-center max-w-3xl mx-auto shadow-sm"
            >
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-600 mb-4">
                <Code2 className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Recent Client Engagements Under Non-Disclosure
              </h3>
              <p className="mt-2 text-xs text-slate-600 max-w-md mx-auto leading-relaxed">
                Many of our corporate web applications and custom systems operate under private agreements. We publish selected public case studies periodically.
              </p>
              <div className="mt-6 flex flex-wrap justify-center gap-4">
                <Link
                  href="/contact"
                  className="inline-flex items-center gap-2 rounded bg-slate-900 px-4 py-2 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
                >
                  <span>Request Client References</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <Link
                  href="/portfolio"
                  className="inline-flex items-center rounded border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  View Showcase Page
                </Link>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Technology Standards */}
        <section className="py-16 bg-white border-t border-slate-200">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="text-center max-w-2xl mx-auto mb-10"
            >
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                Modern Engineering Stack
              </h2>
              <p className="text-xl font-bold text-slate-900">
                Deterministic, maintainable technologies built for speed
              </p>
            </motion.div>

            <motion.div
              variants={staggerContainerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center"
            >
              {[
                { title: "Next.js 14+", sub: "App Router & Edge Speed" },
                { title: "TypeScript", sub: "Strict Type Safety" },
                { title: "FastAPI & Python", sub: "High-Throughput APIs" },
                { title: "PostgreSQL", sub: "ACID Relational Storage" },
              ].map((tech) => (
                <motion.div
                  key={tech.title}
                  variants={fadeUpVariants}
                  {...cardHoverProps}
                  className="rounded border border-slate-200 p-4 bg-slate-50 transition-all hover:bg-white hover:shadow-sm"
                >
                  <span className="font-bold text-slate-900 text-sm">{tech.title}</span>
                  <p className="text-[11px] text-slate-500 mt-1">{tech.sub}</p>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="bg-slate-900 text-white py-16">
          <motion.div
            variants={fadeUpVariants}
            initial="hidden"
            whileInView="visible"
            viewport={VIEWPORT_ONCE}
            className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center max-w-2xl"
          >
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
              Ready to build a distinctive web presence for your business?
            </h2>
            <p className="mt-4 text-sm text-slate-300 leading-relaxed">
              Schedule a direct consultation with our development team. We will review your goals, provide architectural recommendations, and prepare a milestone quote.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/contact"
                className="inline-flex items-center gap-2 rounded bg-blue-600 px-6 py-3 text-sm font-semibold text-white hover:bg-blue-500 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 shadow-sm"
              >
                <span>Initiate Project Consultation</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/services"
                className="inline-flex items-center rounded border border-slate-700 bg-slate-800 px-6 py-3 text-sm font-semibold text-slate-200 hover:bg-slate-700 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
              >
                Browse Service Packages
              </Link>
            </div>
          </motion.div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
