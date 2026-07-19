import io
import os
from typing import List, Any
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from .interfaces import BaseExporter
from .templates.header_config import ReportHeaderConfig

class PdfExporter(BaseExporter):
    def generate(self, records: List[Any]) -> io.BytesIO:
        # Load template
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('pdf_template.html')
        
        header_data = ReportHeaderConfig.get_dynamic_header_data()
        
        # Pre-process records for V2 schema
        formatted_records = []
        for r in records:
            date_str = r.harvest_date.strftime("%Y-%m-%d") if hasattr(r.harvest_date, 'strftime') else str(r.harvest_date)
            h_name = getattr(r, 'harvester_name', str(r.harvester_id))
            
            gross = getattr(r, 'gross_tonnage_kg', 0)
            net = getattr(r, 'net_tonnage_kg', 0)
            loose_deduct = getattr(r, 'loose_fruit_deduction_kg', 0)
            fine_mode = getattr(r, 'fine_mode_snapshot', 'rupiah')
            fine_amount = getattr(r, 'fine_amount_rupiah', 0)
            weight_deduct = getattr(r, 'weight_deduction_kg', 0)
            unripe = getattr(r, 'unripe_bunch_count', 0)
            
            if unripe == 0:
                denda_str = "-"
            elif fine_mode == 'rupiah':
                denda_str = f"Rp {fine_amount:,.0f} ({unripe} jjg)"
            else:
                denda_str = f"{weight_deduct} kg ({unripe} jjg)"

            formatted_records.append({
                "tanggal": date_str,
                "pemanen": h_name,
                "lokasi": "TPH " + str(getattr(r, 'collection_point_id', '-'))[:4],
                "janjang": getattr(r, 'valid_bunch_count', 0),
                "bjr": getattr(r, 'avg_bunch_weight_kg', 0),
                "bruto": gross,
                "brondolan": loose_deduct,
                "mentah": denda_str,
                "netto": net
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
