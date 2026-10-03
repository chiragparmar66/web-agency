from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WebsiteAnalysisResult(BaseModel):
    """Normalized output from AI requirement analysis task."""
    website_type: str = Field(..., description="E.g., Corporate, Portfolio, E-commerce, Landing Page")
    target_audience: str = Field(..., description="Primary user personas and target market")
    suggested_pages: List[str] = Field(default_factory=list, description="Recommended list of page names")
    recommended_sections: List[str] = Field(default_factory=list, description="Recommended section structure")
    design_system: Dict[str, Any] = Field(
        default_factory=lambda: {
            "primary_color": "#0ea5e9",
            "secondary_color": "#6366f1",
            "background_theme": "dark",
            "font_family": "Inter, sans-serif",
        },
        description="Design system tokens: colors, typography, theme"
    )
    technical_constraints: List[str] = Field(default_factory=list, description="Technical constraints or rules")
    summary: str = Field(..., description="High-level project synthesis summary")


class WebsitePagePlan(BaseModel):
    """Specification for an individual page in the planned website."""
    path: str = Field(..., description="Target relative file path, e.g. 'index.html', 'about.html'")
    title: str = Field(..., description="Browser title and heading")
    purpose: str = Field(..., description="Goal and content narrative of this page")
    sections: List[str] = Field(default_factory=list, description="Sections planned for this page")


class WebsitePlanResult(BaseModel):
    """Architecture and page plan output from AI planning task."""
    project_name: str = Field(..., description="Branded website title")
    pages: List[WebsitePagePlan] = Field(..., description="List of planned pages")
    navigation: List[Dict[str, str]] = Field(default_factory=list, description="Global nav items [{'label': 'Home', 'url': 'index.html'}]")
    shared_components: List[str] = Field(default_factory=list, description="Components used across pages: header, footer, etc.")
    color_palette: Dict[str, str] = Field(default_factory=dict, description="Concrete color hex codes")
    typography: Dict[str, str] = Field(default_factory=dict, description="Typography definitions")
    asset_mapping: Dict[str, str] = Field(default_factory=dict, description="Mapped asset placeholders")


class GeneratedFile(BaseModel):
    """A generated code or asset file in the static website artifact."""
    path: str = Field(..., description="Relative path, sanitized, e.g. 'index.html', 'css/styles.css'")
    content: str = Field(..., description="Text content of the file")
    file_type: str = Field(default="html", description="Type: html, css, js, json, svg")


class GeneratedWebsite(BaseModel):
    """Complete multi-page static website output produced by AI generation task."""
    entry_file: str = Field(default="index.html", description="Primary landing page")
    files: List[GeneratedFile] = Field(..., description="List of all generated files")
    summary: str = Field(default="", description="Summary of generated website")


class CodeValidationFinding(BaseModel):
    """Validation issue or warning identified in generated code."""
    file_path: str
    severity: str = Field(default="WARNING", description="ERROR or WARNING")
    rule: str
    message: str


class CodeValidationResult(BaseModel):
    """Overall validation outcome for a generated website artifact."""
    is_valid: bool = True
    findings: List[CodeValidationFinding] = Field(default_factory=list)
    score: float = 100.0


class BuildManifest(BaseModel):
    """Metadata manifest saved with generated website build."""
    project_id: str
    build_id: str
    version_number: int
    entry_file: str = "index.html"
    files: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: str
    providers_used: Dict[str, str] = Field(default_factory=dict)
    spec_summary: Dict[str, Any] = Field(default_factory=dict)
