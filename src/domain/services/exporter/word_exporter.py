import io
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from typing import List, Any
from .interfaces import BaseExporter
from .templates.header_config import ReportHeaderConfig

class WordExporter(BaseExporter):
    def generate(self, records: List[Any]) -> io.BytesIO:
        document = Document()
        
        # Set landscape
        section = document.sections[-1]
        new_width, new_height = section.page_height, section.page_width
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = new_width
        section.page_height = new_height
        
        header_data = ReportHeaderConfig.get_dynamic_header_data()
        
        # Header
        h1 = document.add_heading(header_data["company_name"], 0)
        h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        p = document.add_paragraph()
        p.add_run(header_data["report_title"]).bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        p_date = document.add_paragraph(f"Tanggal Cetak: {header_data['print_date']}")
        p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Table
        table = document.add_table(rows=1, cols=7)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        headers = ["Tanggal", "Pemanen", "Janjang", "BJR (kg)", "Tonase (kg)", "Denda (Rp)", "Total Premi (Rp)"]
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
            hdr_cells[i].paragraphs[0].runs[0].bold = True
            
        for r in records:
            row_cells = table.add_row().cells
            row_cells[0].text = r.harvest_date.strftime("%Y-%m-%d") if hasattr(r.harvest_date, 'strftime') else str(r.harvest_date)
            row_cells[1].text = r.harvester_name
            row_cells[2].text = str(r.input_total_bunches)
            row_cells[3].text = str(r.input_avg_bunch_weight)
            row_cells[4].text = str(r.calc_total_tonnage)
            row_cells[5].text = f"Rp {r.input_unripe_penalty:,.0f}".replace(',', '.')
            row_cells[6].text = f"Rp {r.total_final_premium:,.0f}".replace(',', '.')
            
        output = io.BytesIO()
        document.save(output)
        output.seek(0)
        return output
