"use client";

import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Code2,
  Compass,
  HeartHandshake,
  ShieldCheck,
  Target,
} from "lucide-react";
import { motion } from "motion/react";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import {
  fadeUpVariants,
  cardHoverProps,
  VIEWPORT_ONCE,
  staggerContainerVariants,
} from "@/lib/motion";

export default function AboutPage() {
  const values = [
    {
      title: "Human Craftsmanship Over Automation",
      description:
        "We believe a business website represents your company's reputation. We write custom code tailored to your exact business logic rather than relying on brittle website builders or generic AI generators.",
      icon: Code2,
    },
    {
      title: "Performance as a Core Feature",
      description:
        "Every millisecond of latency costs conversions. We architect our websites using Next.js and server-side rendering to ensure instant loading even on mobile data connections across India.",
      icon: Target,
    },
    {
      title: "Transparent, Milestone-Based Delivery",
      description:
        "No hidden charges, no vague timelines. You receive fixed scope, defined milestone deliverables, structured revisions on staging links, and verified payment invoices.",
      icon: Compass,
    },
    {
      title: "Long-Term Engineering Accountability",
      description:
        "We don't abandon you after launch. Our maintenance retainers and ongoing support ensure your digital infrastructure stays secure, up-to-date, and optimized.",
      icon: HeartHandshake,
    },
  ];

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <Navbar />

      <main className="flex-1">
        {/* Header */}
        <section className="border-b border-slate-200 bg-white py-16 sm:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              animate="visible"
              className="max-w-3xl"
            >
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">
                About Nexus Studio
              </span>
              <h1 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
                A dedicated web development studio for discerning businesses.
              </h1>
              <p className="mt-4 text-base sm:text-lg text-slate-600 leading-relaxed">
                Founded with a clear principle: Indian businesses deserve clean, custom-crafted digital presence engineered by experienced developers, not synthetic templates or marketing gimmicks.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Narrative Section */}
        <section className="py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <motion.div
                variants={fadeUpVariants}
                initial="hidden"
                whileInView="visible"
                viewport={VIEWPORT_ONCE}
              >
                <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 leading-snug">
                  Why we reject &quot;instant website builders&quot; and build custom digital architecture.
                </h2>
                <div className="mt-6 space-y-4 text-sm text-slate-600 leading-relaxed">
                  <p>
                    The modern internet is flooded with generic site builders and automated tools that generate bloated, cookie-cutter templates. These systems often fail in real business scenarios: they load slowly on Indian networks, break under custom requirements, and look indistinguishable from competitors.
                  </p>
                  <p>
                    At Nexus Studio, we take a software engineering approach. Every client website is planned, designed, and coded by real engineers using robust modern technologies: Next.js, TypeScript, FastAPI, and PostgreSQL.
                  </p>
                  <p>
                    The result is a fast, conversion-focused digital presence that works reliably across every mobile screen, desktop viewport, and search engine crawler.
                  </p>
                </div>

                <div className="mt-8 flex flex-col sm:flex-row gap-4">
                  <Link
                    href="/contact"
                    className="inline-flex items-center justify-center gap-2 rounded bg-slate-900 px-6 py-3 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
                  >
                    <span>Discuss Your Requirements</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </Link>
                  <Link
                    href="/services"
                    className="inline-flex items-center justify-center rounded border border-slate-300 bg-white px-6 py-3 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                  >
                    Explore Service Capabilities
                  </Link>
                </div>
              </motion.div>

              {/* Trust Box */}
              <motion.div
                variants={fadeUpVariants}
                initial="hidden"
                whileInView="visible"
                viewport={VIEWPORT_ONCE}
                className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm space-y-6"
              >
                <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                  <div className="flex h-10 w-10 items-center justify-center rounded bg-blue-50 text-blue-600">
                    <ShieldCheck className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-sm">
                      Studio Commitment & Operating Standards
                    </h3>
                    <p className="text-xs text-slate-500">
                      Standardized practices across all client engagements
                    </p>
                  </div>
                </div>

                <ul className="space-y-4 text-xs text-slate-600">
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-slate-900">Direct Developer Access:</strong>
                      <p className="text-slate-500 mt-0.5">You communicate directly with the engineer building your website, avoiding lost-in-translation account managers.</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-slate-900">Staging Review System:</strong>
                      <p className="text-slate-500 mt-0.5">Preview functional builds on private staging URLs and track revisions before code goes live.</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-slate-900">Indian Business Alignment:</strong>
                      <p className="text-slate-500 mt-0.5">INR payment verification via Razorpay, UPI support, and formal GST tax invoices for business accounting.</p>
                    </div>
                  </li>
                  <li className="flex items-start gap-2.5">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-slate-900">Source Code Ownership:</strong>
                      <p className="text-slate-500 mt-0.5">You own your content, domain, and deployment without platform vendor lock-in.</p>
                    </div>
                  </li>
                </ul>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Studio Values */}
        <section className="bg-white border-t border-slate-200 py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="max-w-2xl mb-12"
            >
              <span className="text-xs font-bold uppercase tracking-wider text-blue-600">
                Guiding Principles
              </span>
              <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">
                How we engineer software
              </h2>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {values.map((v) => {
                const IconComponent = v.icon;
                return (
                  <motion.div
                    key={v.title}
                    variants={fadeUpVariants}
                    initial="hidden"
                    whileInView="visible"
                    viewport={VIEWPORT_ONCE}
                    {...cardHoverProps}
                    className="rounded-lg border border-slate-200 bg-slate-50 p-6 flex flex-col justify-between hover:border-slate-300 transition-colors"
                  >
                    <div>
                      <div className="flex h-9 w-9 items-center justify-center rounded bg-slate-900 text-white mb-4">
                        <IconComponent className="h-4 w-4" />
                      </div>
                      <h3 className="text-base font-bold text-slate-900 mb-2">
                        {v.title}
                      </h3>
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {v.description}
                      </p>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
