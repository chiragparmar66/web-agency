import Link from "next/link";
import { Mail, MessageCircle, Phone } from "lucide-react";
import { APP_CONFIG, getWhatsAppUrl } from "@/lib/constants";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-slate-950 text-slate-400 text-sm">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Column 1: Studio Identity */}
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded bg-white text-slate-900 font-bold text-sm">
                NX
              </div>
              <span className="text-base font-bold tracking-tight text-white">
                NEXUS STUDIO
              </span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Professional web development studio for Indian businesses. We design and engineer bespoke, high-performance websites with dedicated developer support.
            </p>
            <div className="pt-2 text-xs text-slate-400">
              <span className="inline-block px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
                GST Compliant Invoicing
              </span>
            </div>
          </div>

          {/* Column 2: Navigation */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Studio
            </h3>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/" className="hover:text-white transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link href="/services" className="hover:text-white transition-colors">
                  Services
                </Link>
              </li>
              <li>
                <Link href="/portfolio" className="hover:text-white transition-colors">
                  Selected Work
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-white transition-colors">
                  About Studio
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-white transition-colors">
                  Project Inquiry
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Services */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Capabilities
            </h3>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/services#business-websites" className="hover:text-white transition-colors">
                  Business Websites
                </Link>
              </li>
              <li>
                <Link href="/services#landing-pages" className="hover:text-white transition-colors">
                  High-Converting Landing Pages
                </Link>
              </li>
              <li>
                <Link href="/services#portfolio-websites" className="hover:text-white transition-colors">
                  Portfolio & Creative Websites
                </Link>
              </li>
              <li>
                <Link href="/services#ecommerce-websites" className="hover:text-white transition-colors">
                  E-Commerce Development
                </Link>
              </li>
              <li>
                <Link href="/services#website-maintenance" className="hover:text-white transition-colors">
                  Performance & Maintenance
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Contact & Office */}
          <div className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-200">
              Direct Contact
            </h3>
            <div className="space-y-2.5 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-slate-500 shrink-0" />
                <a
                  href={`mailto:${APP_CONFIG.supportEmail}`}
                  className="hover:text-white transition-colors"
                >
                  {APP_CONFIG.supportEmail}
                </a>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-slate-500 shrink-0" />
                <a
                  href={`tel:${APP_CONFIG.phoneNumber}`}
                  className="hover:text-white transition-colors"
                >
                  +91 {APP_CONFIG.phoneNumber}
                </a>
              </div>
              <div className="flex items-center gap-2">
                <MessageCircle className="h-4 w-4 text-emerald-400 shrink-0" />
                <a
                  href={getWhatsAppUrl("Hi Nexus Studio, I'd like to discuss a website project.")}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-emerald-400 transition-colors"
                >
                  +91 {APP_CONFIG.whatsappNumber} (WhatsApp)
                </a>
              </div>
            </div>

            <div className="pt-2">
              <Link
                href="/login"
                className="inline-flex items-center text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Existing Client? Access Portal &rarr;
              </Link>
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="border-t border-slate-900 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>
            &copy; {new Date().getFullYear()} Nexus Studio. All rights reserved. Handcrafted engineering.
          </p>
          <div className="flex items-center gap-6">
            <span>Deterministic Modern Code</span>
            <span>Razorpay Payment Verified</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
