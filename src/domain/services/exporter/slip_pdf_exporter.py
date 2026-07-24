import io
import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from .templates.header_config import ReportHeaderConfig

import io
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from .templates.header_config import ReportHeaderConfig

class SlipPdfExporter:
    def generate(
        self, 
        summary, 
        harvester_name: str, 
        employee_number: str, 
        period_name: str,
        division_name: str = "Divisi Panen",
        block_code: str = "-"
    ) -> io.BytesIO:
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('slip_template.html')
        
        header_data = ReportHeaderConfig.get_dynamic_header_data()
        
        loose_rp = float(getattr(summary, 'total_loose_fruit_premium_rupiah', 0))
        tier_rp = float(getattr(summary, 'total_tier_premium_rupiah', 0))
        total_penerimaan = loose_rp + tier_rp
        fine_rp = float(getattr(summary, 'total_fine_rupiah', 0))
        
        # Format the numbers
        data = {
            "nik": employee_number,
            "pemanen": harvester_name,
            "pemanen_name": harvester_name,
            "afdeling": division_name or getattr(summary, 'division_name', 'Divisi Panen'),
            "blok": block_code or getattr(summary, 'block_code', '-'),
            "periode": period_name,
            "total_janjang": f"{summary.total_valid_bunch_count:,.0f}",
            "denda_janjang": f"{summary.total_unripe_bunch_count:,.0f}",
            "total_netto": f"{float(summary.total_net_tonnage_kg):,.2f}",
            "brondolan_rp": f"Rp {loose_rp:,.0f}",
            "denda_rp": f"Rp {fine_rp:,.0f}",
            "fine_mode": getattr(summary, 'fine_mode_used', 'rupiah'),
            "total_penerimaan": f"Rp {total_penerimaan:,.0f}",
            "total_potongan": f"Rp {fine_rp:,.0f}",
            "net_pay": f"{float(summary.total_net_pay_rupiah):,.0f}",
            "tanggal_slip": datetime.now().strftime("%d %B %Y"),
            "tempat": "Kebun Utama",
            "approver_name": "Asisten Divisi",
            "approver_role": "Manager Operasional",
            "tiers": [
                {
                    "level": getattr(t, 'tier_level', 0),
                    "kg": f"{float(getattr(t, 'kg_in_tier', 0)):,.2f}",
                    "rate": f"{float(getattr(t, 'rate_per_kg', 0)):,.0f}",
                    "subtotal": f"Rp {float(getattr(t, 'subtotal_rupiah', 0)):,.0f}"
                }
                for t in summary.tier_details
            ] if hasattr(summary, 'tier_details') and summary.tier_details else [],
            "daily_records": [
                {
                    "date": r.harvest_date.strftime("%d-%m-%Y") if hasattr(r, 'harvest_date') and r.harvest_date else "-",
                    "valid": r.valid_bunch_count,
                    "unripe": r.unripe_bunch_count,
                    "net_kg": f"{float(r.net_tonnage_kg):,.2f}",
                    "loose_rp": f"Rp {float(r.loose_fruit_premium_rupiah):,.0f}",
                    "fine_rp": f"Rp {float(r.fine_amount_rupiah):,.0f}"
                }
                for r in summary.daily_records
            ] if hasattr(summary, 'daily_records') and summary.daily_records else []
        }
        
        html_out = template.render(header=header_data, data=data)
        
        output = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_out), dest=output)
        
        if pisa_status.err:
            raise Exception("Slip PDF generation failed")
            
        output.seek(0)
        return output
