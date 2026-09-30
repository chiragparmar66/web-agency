import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Nexus Studio | Professional Web Design & Development",
  description:
    "We build custom, conversion-focused websites and web applications for modern businesses. Handcrafted engineering, transparent pricing, and dedicated developer support.",
  openGraph: {
    title: "Nexus Studio | Professional Web Design & Development",
    description:
      "Bespoke websites and web applications engineered for modern businesses.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col font-sans bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}
