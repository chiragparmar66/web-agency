import json
from typing import Any, Dict


ANALYSIS_SYSTEM_PROMPT = """You are an elite Senior Web Architect at Nexus Studio.
Analyze client requirements, business domain, target audience, brand assets, and package specifications.
Formulate a precise technical and design specification for generating a complete static website.
You must output valid JSON complying strictly with the WebsiteAnalysisResult schema."""


PLANNING_SYSTEM_PROMPT = """You are a Principal Frontend Architect at Nexus Studio.
Given the client context and website analysis specification, design the exact site architecture,
page structure, navigation hierarchy, shared UI components, color palette, and typography.
Ensure a modern, responsive, accessible website plan.
You must output valid JSON complying strictly with the WebsitePlanResult schema."""


GENERATION_SYSTEM_PROMPT = """You are an expert Frontend Developer at Nexus Studio.
You produce clean, semantic, responsive, production-ready static website code (HTML5, modern CSS3, vanilla JavaScript).
RULES:
1. Always generate a self-contained multi-page static website.
2. The primary landing page MUST be named 'index.html'.
3. Every HTML file must include <!DOCTYPE html>, properly structured <head>, <meta charset="UTF-8">, viewport meta tag, and valid markup.
4. CSS should be clean, modular, and use CSS variables for colors and typography matching the design system.
5. JavaScript must be vanilla ES6+; do not attempt to import Node.js built-ins or server modules.
6. Absolutely DO NOT include or expose any API keys, credentials, or private tokens.
7. Return a valid JSON object matching the GeneratedWebsite schema containing all generated files.
"""


REPAIR_SYSTEM_PROMPT = """You are a Senior Frontend Code Reviewer and Debugging Specialist at Nexus Studio.
Review the previous website generation attempt and the validation error findings.
Fix every error, broken link, missing entry file, or security finding.
Return the complete corrected multi-page static website as valid JSON matching GeneratedWebsite schema."""


def build_analysis_prompt(project_context: Dict[str, Any]) -> str:
    return f"""Please analyze the following client project details and requirements:

{json.dumps(project_context, indent=2)}

Synthesize a comprehensive analysis including website_type, target_audience, suggested_pages,
recommended_sections, design_system, technical_constraints, and summary."""


def build_planning_prompt(project_context: Dict[str, Any], analysis_data: Dict[str, Any]) -> str:
    return f"""Based on the following project context and analysis specification:

--- PROJECT CONTEXT ---
{json.dumps(project_context, indent=2)}

--- ANALYSIS SPECIFICATION ---
{json.dumps(analysis_data, indent=2)}

Create a detailed multi-page website plan including pages, navigation, shared_components,
color_palette, typography, and asset_mapping."""


def build_generation_prompt(
    project_context: Dict[str, Any],
    analysis_data: Dict[str, Any],
    plan_data: Dict[str, Any],
) -> str:
    return f"""Generate the complete, production-ready static website based on the approved specifications:

--- PROJECT OVERVIEW ---
Title: {project_context.get('title', 'Website')}
Client: {project_context.get('client_name', 'Client')}

--- ANALYSIS SPEC ---
{json.dumps(analysis_data, indent=2)}

--- ARCHITECTURE & PAGE PLAN ---
{json.dumps(plan_data, indent=2)}

Generate all planned HTML pages (including 'index.html'), external CSS ('css/styles.css'),
and JavaScript ('js/main.js') files."""


def build_repair_prompt(
    validation_findings: list,
    previous_files: list,
) -> str:
    findings_str = json.dumps([f.model_dump() if hasattr(f, 'model_dump') else f for f in validation_findings], indent=2)
    files_summary = [{"path": f.path, "preview": f.content[:200] + "..."} for f in previous_files]

    return f"""The previous website generation produced validation errors that MUST be corrected:

--- VALIDATION ERRORS ---
{findings_str}

--- PREVIOUS FILES SUMMARY ---
{json.dumps(files_summary, indent=2)}

Regenerate all files so that all errors are resolved, 'index.html' exists, and the site is 100% valid."""
