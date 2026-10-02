import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import { api } from "@/lib/api";
import { PortfolioItem } from "@/types";
import PortfolioContent from "./PortfolioContent";

async function getPortfolioProjects(): Promise<PortfolioItem[]> {
  try {
    const res = await api.get<PortfolioItem[]>("/portfolio");
    if (res.success && Array.isArray(res.data)) {
      return res.data;
    }
    return [];
  } catch (err) {
    return [];
  }
}

export default async function PortfolioPage() {
  const projects = await getPortfolioProjects();

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <Navbar />
      <PortfolioContent projects={projects} />
      <Footer />
    </div>
  );
}
