from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.showcase import Service
from app.models.pricing_package import PricingPackage


INITIAL_SERVICES = [
    {
        "slug": "business-websites",
        "title": "Bespoke Business Websites",
        "short_description": "Clean, conversion-driven websites designed for modern Indian enterprises, clinics, law firms, and consulting companies.",
        "full_description": "We engineer fast, accessible, responsive websites tailored to your exact brand positioning. No generic templates or bloated visual page builders—pure handcrafted modern code.",
        "deliverables": [
            "Custom UX/UI visual architecture",
            "Mobile-first responsive implementation",
            "SEO metadata, OpenGraph & schema markup",
            "Direct contact & inquiry capture integration",
            "Production deployment & DNS setup",
        ],
        "icon_name": "Globe",
        "starting_price_inr": 4999.0,
        "sort_order": 1,
    },
    {
        "slug": "landing-pages",
        "title": "High-Converting Landing Pages",
        "short_description": "Focused, distraction-free landing pages engineered to convert ad traffic into paying customers and leads.",
        "full_description": "Designed with strong visual hierarchy, persuasive copywriting layout, fast load times (<1s), and clear call-to-actions.",
        "deliverables": [
            "Conversion-focused single page structure",
            "Lead capture & WhatsApp integration",
            "Mobile performance optimization (<1s load)",
            "A/B test ready section layout",
        ],
        "icon_name": "Zap",
        "starting_price_inr": 2999.0,
        "sort_order": 2,
    },
    {
        "slug": "portfolio-websites",
        "title": "Studio & Portfolio Websites",
        "short_description": "Distinctive digital showcases for creative studios, architects, photographers, and independent professionals.",
        "full_description": "Showcase your work with refined typography, minimal aesthetics, and fast-loading media galleries that let your craft speak for itself.",
        "deliverables": [
            "Editorial typography and gallery layouts",
            "High-resolution optimized media delivery",
            "Interactive case study breakdowns",
            "Contact & commission inquiry channel",
        ],
        "icon_name": "Briefcase",
        "starting_price_inr": 3999.0,
        "sort_order": 3,
    },
    {
        "slug": "ecommerce-websites",
        "title": "E-Commerce Platforms",
        "short_description": "Custom online stores integrated with Indian payment gateways (UPI, Cards, NetBanking) and clear inventory workflows.",
        "full_description": "Sell your products directly with zero third-party platform percentage cut on every sale. Clean catalog, cart, and payment checkout experience.",
        "deliverables": [
            "Product catalog & category filtering",
            "Secure Razorpay / UPI checkout flow",
            "Order notification & tracking system",
            "Customer account & order history",
        ],
        "icon_name": "ShoppingBag",
        "starting_price_inr": 14999.0,
        "sort_order": 4,
    },
    {
        "slug": "website-maintenance",
        "title": "Performance & Maintenance Retainer",
        "short_description": "Continuous speed monitoring, security patches, regular backups, and content updates for your existing digital presence.",
        "full_description": "Keep your web applications secure and running at peak performance with dedicated monthly engineering support.",
        "deliverables": [
            "Core Web Vitals monitoring & optimizations",
            "Weekly automated off-site backups",
            "Security audit & dependency patching",
            "Priority developer change requests",
        ],
        "icon_name": "ShieldCheck",
        "starting_price_inr": 1999.0,
        "sort_order": 5,
    },
    {
        "slug": "custom-web-apps",
        "title": "Custom Web Applications",
        "short_description": "Tailored web applications, internal dashboards, and client portals built for complex business operations.",
        "full_description": "When off-the-shelf software doesn't fit your business processes, we build custom full-stack solutions using Next.js, FastAPI, and PostgreSQL.",
        "deliverables": [
            "Custom database architecture & APIs",
            "Role-based authentication & permissions",
            "Operational workflows & data reporting",
            "Cloud infrastructure deployment",
        ],
        "icon_name": "Cpu",
        "starting_price_inr": 24999.0,
        "sort_order": 6,
    },
]


INITIAL_PACKAGES = [
    {
        "slug": "starter-website",
        "name": "Starter Website",
        "price_inr": 1999.0,
        "description": "A clean, fast single-page website ideal for freelancers, individual professionals, and early-stage businesses.",
        "features": [
            "Single-page responsive website",
            "Mobile-first design",
            "Contact form integration",
            "SEO metadata setup",
            "WhatsApp quick-contact button",
            "Delivery in 3 working days",
        ],
        "delivery_days": 3,
        "revisions_included": 1,
        "is_popular": False,
        "is_active": True,
    },
    {
        "slug": "business-website",
        "name": "Business Website",
        "price_inr": 4999.0,
        "description": "A professional multi-page website for established businesses, clinics, law firms, and agencies.",
        "features": [
            "Up to 5 custom pages",
            "Mobile-first responsive design",
            "Contact & inquiry capture form",
            "Google Maps & social link integration",
            "SEO metadata + OpenGraph",
            "WhatsApp & call CTA buttons",
            "Delivery in 7 working days",
        ],
        "delivery_days": 7,
        "revisions_included": 2,
        "is_popular": True,
        "is_active": True,
    },
    {
        "slug": "professional-website",
        "name": "Professional Website",
        "price_inr": 9999.0,
        "description": "A premium website with advanced functionality for companies that need a sophisticated online presence.",
        "features": [
            "Up to 10 custom pages",
            "Premium UI/UX design",
            "Blog or news section",
            "Testimonials & portfolio section",
            "Advanced SEO & sitemap",
            "Analytics integration",
            "Delivery in 12 working days",
        ],
        "delivery_days": 12,
        "revisions_included": 3,
        "is_popular": False,
        "is_active": True,
    },
    {
        "slug": "custom-solution",
        "name": "Custom Solution",
        "price_inr": 19999.0,
        "description": "Fully bespoke web application or e-commerce platform engineered to your exact specifications.",
        "features": [
            "Unlimited custom pages",
            "Custom web application features",
            "E-commerce or booking system (if required)",
            "Razorpay / UPI payment integration",
            "Admin CMS dashboard",
            "Full deployment & DNS setup",
            "Delivery timeline agreed on scope",
        ],
        "delivery_days": 21,
        "revisions_included": 5,
        "is_popular": False,
        "is_active": True,
    },
]


async def seed_initial_data(session: AsyncSession) -> None:
    """Seed default studio services and pricing packages if tables are empty."""
    # Seed services
    svc_stmt = select(Service)
    svc_result = await session.execute(svc_stmt)
    if not svc_result.scalars().first():
        for s_data in INITIAL_SERVICES:
            session.add(Service(**s_data))
        await session.commit()

    # Seed pricing packages
    pkg_stmt = select(PricingPackage)
    pkg_result = await session.execute(pkg_stmt)
    if not pkg_result.scalars().first():
        for p_data in INITIAL_PACKAGES:
            session.add(PricingPackage(**p_data))
        await session.commit()

