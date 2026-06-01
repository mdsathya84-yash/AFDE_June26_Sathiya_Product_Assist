import json
import logging
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ReportGenerator:
    def __init__(self):
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)

    def generate_pdf(self, analysis_state: dict) -> bytes:
        try:
            from weasyprint import HTML
        except ImportError:
            raise RuntimeError("weasyprint is required for PDF generation")

        html = self._render_html(analysis_state)
        return HTML(string=html).write_pdf()

    def generate_json(self, analysis_state: dict) -> dict:
        report = analysis_state.get("report_sections", {})
        return {
            "generated_at": date.today().isoformat(),
            "executive_summary": analysis_state.get("executive_summary", ""),
            "customer_insights": report.get("customer_insights", {}),
            "sales_analysis": report.get("sales_analysis", {}),
            "swot": report.get("swot", {}),
            "feature_priorities": report.get("feature_priorities", {}),
            "opportunities": report.get("opportunities", {}),
            "strategy": report.get("strategy", {}),
        }

    def _render_html(self, analysis_state: dict) -> str:
        sections = analysis_state.get("report_sections", {})
        strategy = sections.get("strategy", {})
        action_plan = strategy.get("action_plan", {})
        template = self.env.get_template("report.html")
        return template.render(
            generated_date=date.today().strftime("%B %d, %Y"),
            executive_summary=analysis_state.get("executive_summary", ""),
            customer_insights=sections.get("customer_insights", {}),
            sales_analysis=sections.get("sales_analysis", {}),
            swot=sections.get("swot", {}),
            feature_priorities=sections.get("feature_priorities", {}),
            opportunities=sections.get("opportunities", {}),
            strategy=strategy,
            action_plan_90=action_plan.get("90_days", []),
            action_plan_6m=action_plan.get("6_months", []),
            action_plan_12m=action_plan.get("12_months", []),
            product_roadmap=strategy.get("product_roadmap", []),
        )
