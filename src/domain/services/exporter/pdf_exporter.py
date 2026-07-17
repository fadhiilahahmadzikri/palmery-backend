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
        
        # Render HTML
        html_out = template.render(header=header_data, records=records)
        
        # Generate PDF
        output = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_out), dest=output)
        
        if pisa_status.err:
            raise Exception("PDF generation failed")
            
        output.seek(0)
        return output
