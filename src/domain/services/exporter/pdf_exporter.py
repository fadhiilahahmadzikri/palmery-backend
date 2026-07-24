import io
import os
from typing import List, Any, Optional
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from .interfaces import BaseExporter
from .templates.header_config import ReportHeaderConfig

class PdfExporter(BaseExporter):
    def generate(self, records: List[Any], period_label: Optional[str] = None) -> io.BytesIO:
        # Load template
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('pdf_template.html')
        
        header_data = ReportHeaderConfig.get_dynamic_header_data()
        if period_label:
            header_data["period_label"] = period_label
        
        def fmt_id(val: float, decimals: int = 1) -> str:
            if val is None:
                return "0"
            s = f"{val:,.{decimals}f}"
            return s.replace(",", "X").replace(".", ",").replace("X", ".")

        # Pre-process records for V2 schema
        formatted_records = []
        for r in records:
            date_str = r.harvest_date.strftime("%d-%m-%Y") if hasattr(r.harvest_date, 'strftime') else str(r.harvest_date)
            
            h_name = getattr(r, 'harvester_name', None)
            if not h_name and hasattr(r, 'harvester') and r.harvester and hasattr(r.harvester, 'full_name'):
                h_name = r.harvester.full_name
            if not h_name or len(str(h_name)) > 30:
                h_name = "Pemanen"

            loc_name = getattr(r, 'location_name', None)
            if not loc_name and hasattr(r, 'collection_point') and r.collection_point and hasattr(r.collection_point, 'point_number'):
                loc_name = f"TPH {r.collection_point.point_number}"
            if not loc_name and hasattr(r, 'block') and r.block and hasattr(r.block, 'code'):
                loc_name = f"Blok {r.block.code}"
            if not loc_name or len(str(loc_name)) > 20:
                loc_name = "-"

            gross = getattr(r, 'gross_tonnage_kg', 0.0)
            net = getattr(r, 'net_tonnage_kg', 0.0)
            loose_deduct = getattr(r, 'loose_fruit_deduction_kg', 0.0)
            fine_amount = getattr(r, 'fine_amount_rupiah', 0.0)
            unripe = getattr(r, 'unripe_bunch_count', 0)
            bjr_val = getattr(r, 'avg_bunch_weight_kg', 0.0)
            
            denda_str = f"Rp {fmt_id(fine_amount, 0)}" if fine_amount > 0 else "-"

            formatted_records.append({
                "tanggal": date_str,
                "pemanen": h_name,
                "lokasi": loc_name,
                "janjang": fmt_id(getattr(r, 'valid_bunch_count', 0), 0),
                "bjr": fmt_id(bjr_val, 1),
                "bruto": fmt_id(gross, 1),
                "brondolan": fmt_id(loose_deduct, 1),
                "mentah_jjg": fmt_id(unripe, 0),
                "denda_rp": denda_str,
                "netto": fmt_id(net, 1)
            })
            
        # Render HTML
        html_out = template.render(header=header_data, records=formatted_records)
        
        # Generate PDF
        output = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_out), dest=output)
        
        if pisa_status.err:
            raise Exception("PDF generation failed")
            
        output.seek(0)
        return output
