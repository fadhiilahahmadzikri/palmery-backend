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
        
        # Pre-process records for V2 schema
        formatted_records = []
        for r in records:
            date_str = r.harvest_date.strftime("%Y-%m-%d") if hasattr(r.harvest_date, 'strftime') else str(r.harvest_date)
            h_name = getattr(r, 'harvester_name', None)
            if not h_name and hasattr(r, 'harvester') and r.harvester:
                h_name = r.harvester.full_name
            if not h_name:
                h_name = str(getattr(r, 'harvester_id', '-'))

            loc_name = getattr(r, 'location_name', None)
            if not loc_name and hasattr(r, 'collection_point') and r.collection_point:
                loc_name = f"TPH {r.collection_point.point_number}"
            if not loc_name:
                loc_name = str(getattr(r, 'collection_point_id', '-'))

            gross = getattr(r, 'gross_tonnage_kg', 0.0)
            net = getattr(r, 'net_tonnage_kg', 0.0)
            loose_deduct = getattr(r, 'loose_fruit_deduction_kg', 0.0)
            fine_amount = getattr(r, 'fine_amount_rupiah', 0.0)
            unripe = getattr(r, 'unripe_bunch_count', 0)
            
            denda_str = f"Rp {fine_amount:,.0f}" if fine_amount > 0 else "-"

            formatted_records.append({
                "tanggal": date_str,
                "pemanen": h_name,
                "lokasi": loc_name,
                "janjang": getattr(r, 'valid_bunch_count', 0),
                "bjr": getattr(r, 'avg_bunch_weight_kg', 0),
                "bruto": f"{gross:,.1f}",
                "brondolan": f"{loose_deduct:,.1f}",
                "mentah_jjg": unripe,
                "denda_rp": denda_str,
                "netto": f"{net:,.1f}"
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
