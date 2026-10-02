"use client";

import Link from "next/link";
import { ArrowRight, ExternalLink, FolderGit2, ShieldCheck } from "lucide-react";
import { motion } from "motion/react";
import { PortfolioItem } from "@/types";
import {
  fadeUpVariants,
  cardHoverProps,
  VIEWPORT_ONCE,
  staggerContainerVariants,
} from "@/lib/motion";

interface PortfolioContentProps {
  projects: PortfolioItem[];
}

export default function PortfolioContent({ projects }: PortfolioContentProps) {
  return (
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
              Selected Work
            </span>
            <h1 className="mt-3 text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900">
              Studio Portfolio & Case Studies
            </h1>
            <p className="mt-4 text-base sm:text-lg text-slate-600 leading-relaxed">
              Review verified digital solutions built by Nexus Studio. Every build reflects clean engineering, strong visual identity, and measurable conversion goals.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Content Section */}
      <section className="py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {projects.length > 0 ? (
            <motion.div
              variants={staggerContainerVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
            >
              {projects.map((project) => (
                <motion.div
                  key={project.id}
                  variants={fadeUpVariants}
                  {...cardHoverProps}
                  className="flex flex-col justify-between rounded-lg border border-slate-200 bg-white p-6 shadow-sm hover:border-slate-300 hover:shadow-md transition-all"
                >
                  <div>
                    <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
                      <span className="font-semibold uppercase tracking-wider text-blue-600">
                        {project.industry}
                      </span>
                      <span>{project.client_name}</span>
                    </div>

                    <h2 className="text-xl font-bold text-slate-900 mb-3">
                      {project.title}
                    </h2>

                    <p className="text-xs text-slate-600 leading-relaxed mb-4">
                      {project.description}
                    </p>

                    <div className="flex flex-wrap gap-1.5 mb-6">
                      {project.technologies.map((tech, idx) => (
                        <span
                          key={idx}
                          className="rounded bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-700"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
                    {project.live_demo_url ? (
                      <a
                        href={project.live_demo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors"
                      >
                        <span>Visit Live Website</span>
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    ) : (
                      <span className="text-xs text-slate-400">Deployed Production</span>
                    )}
                  </div>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            /* Clean Authentic Empty State - No Fake Reviews or Invented Clients */
            <motion.div
              variants={fadeUpVariants}
              initial="hidden"
              whileInView="visible"
              viewport={VIEWPORT_ONCE}
              className="rounded-lg border border-slate-200 bg-white p-12 sm:p-16 text-center max-w-2xl mx-auto shadow-sm"
            >
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-700 mb-5">
                <FolderGit2 className="h-7 w-7" />
              </div>

              <h2 className="text-xl font-bold text-slate-900">
                Case Studies & Deployments
              </h2>

              <p className="mt-3 text-sm text-slate-600 leading-relaxed">
                We maintain strict client non-disclosure agreements for custom enterprise systems and corporate portals. Public case studies are updated following client launch verification.
              </p>

              <div className="mt-6 rounded border border-slate-100 bg-slate-50 p-4 text-xs text-slate-600 text-left space-y-2">
                <div className="flex items-center gap-2 font-medium text-slate-800">
                  <ShieldCheck className="h-4 w-4 text-blue-600 shrink-0" />
                  <span>Client Privacy & NDA Commitment</span>
                </div>
                <p className="text-[12px] text-slate-500 leading-relaxed">
                  We never disclose proprietary source code, internal schemas, or client customer metrics without explicit written consent.
                </p>
              </div>

              <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
                <Link
                  href="/contact"
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded bg-slate-900 px-6 py-2.5 text-xs font-semibold text-white hover:bg-slate-800 transition-colors"
                >
                  <span>Request Private References</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </Link>
                <Link
                  href="/services"
                  className="w-full sm:w-auto inline-flex items-center justify-center rounded border border-slate-300 bg-white px-6 py-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  Explore Service Packages
                </Link>
              </div>
            </motion.div>
          )}
        </div>
      </section>
    </main>
  );
}
