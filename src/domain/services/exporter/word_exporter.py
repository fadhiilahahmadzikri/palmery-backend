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
        table = document.add_table(rows=1, cols=9)
        table.style = 'Table Grid'
        
        hdr_cells = table.rows[0].cells
        headers = ["Tanggal", "Pemanen", "Lokasi", "Janjang", "BJR", "Bruto", "Brondolan", "Mentah", "Netto"]
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
            hdr_cells[i].paragraphs[0].runs[0].bold = True
            
        for r in records:
            row_cells = table.add_row().cells
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

            row_cells[0].text = date_str
            row_cells[1].text = h_name
            row_cells[2].text = "TPH " + str(getattr(r, 'collection_point_id', '-'))[:4]
            row_cells[3].text = str(getattr(r, 'valid_bunch_count', 0))
            row_cells[4].text = str(getattr(r, 'avg_bunch_weight_kg', 0))
            row_cells[5].text = str(gross)
            row_cells[6].text = str(loose_deduct)
            row_cells[7].text = denda_str
            row_cells[8].text = str(net)
            
        output = io.BytesIO()
        document.save(output)
        output.seek(0)
        return output
