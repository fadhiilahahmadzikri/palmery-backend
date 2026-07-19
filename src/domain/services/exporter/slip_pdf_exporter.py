import io
import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from .templates.header_config import ReportHeaderConfig

class SlipPdfExporter:
    def generate(self, summary, harvester_name: str, employee_number: str, period_name: str) -> io.BytesIO:
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('slip_template.html')
        
        header_data = ReportHeaderConfig.get_dynamic_header_data()
        
        # Format the numbers
        data = {
            "pemanen": f"{employee_number} - {harvester_name}",
            "periode": period_name,
            "total_janjang": summary.total_valid_bunch_count,
            "denda_janjang": summary.total_unripe_bunch_count,
            "total_netto": f"{float(summary.total_net_tonnage_kg):,.2f}",
            "brondolan_rp": f"{float(summary.total_loose_fruit_premium_rupiah):,.0f}",
            "denda_rp": f"{float(summary.total_fine_rupiah):,.0f}",
            "fine_mode": summary.fine_mode_used,
            "net_pay": f"{float(summary.total_net_pay_rupiah):,.0f}",
            "tiers": [
                {
                    "level": getattr(t, 'tier_level', 0),
                    "kg": f"{float(getattr(t, 'kg_in_tier', 0)):,.2f}",
                    "rate": f"{float(getattr(t, 'rate_per_kg', 0)):,.0f}",
                    "subtotal": f"{float(getattr(t, 'subtotal_rupiah', 0)):,.0f}"
                }
                for t in summary.tier_details
            ] if hasattr(summary, 'tier_details') else [],
            "daily_records": [
                {
                    "date": r.harvest_date.strftime("%d-%m-%Y") if hasattr(r, 'harvest_date') else "-",
                    "valid": r.valid_bunch_count,
                    "unripe": r.unripe_bunch_count,
                    "net_kg": f"{float(r.net_tonnage_kg):,.2f}",
                    "loose_rp": f"{float(r.loose_fruit_premium_rupiah):,.0f}",
                    "fine_rp": f"{float(r.fine_amount_rupiah):,.0f}"
                }
                for r in summary.daily_records
            ] if hasattr(summary, 'daily_records') else []
        }
        
        html_out = template.render(header=header_data, data=data)
        
        output = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_out), dest=output)
        
        if pisa_status.err:
            raise Exception("Slip PDF generation failed")
            
        output.seek(0)
        return output
