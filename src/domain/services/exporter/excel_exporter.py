import io
import xlsxwriter
from typing import List, Any, Optional
from .interfaces import BaseExporter
from .templates.header_config import ReportHeaderConfig

class ExcelExporter(BaseExporter):
    def generate(self, records: List[Any], period_label: Optional[str] = None) -> io.BytesIO:
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Laporan Premi")
        
        # Styles
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
        })
        subtitle_format = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#CAFF3F', 'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter'})
        num_format = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter'})
        currency_format = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter', 'num_format': '"Rp "#,##0'})
        
        header_data = ReportHeaderConfig.get_dynamic_header_data()
        
        # Header (Centered across 10 columns A:J)
        worksheet.merge_range("A1:J1", header_data["company_name"], title_format)
        worksheet.merge_range("A2:J2", header_data["report_title"], subtitle_format)
        
        if period_label:
            worksheet.merge_range("A3:J3", f"Periode: {period_label}", workbook.add_format({'align': 'center', 'italic': True}))
            worksheet.merge_range("A4:J4", f"Tanggal Cetak: {header_data['print_date']}", workbook.add_format({'align': 'center'}))
            header_row = 5
        else:
            worksheet.merge_range("A3:J3", f"Tanggal Cetak: {header_data['print_date']}", workbook.add_format({'align': 'center'}))
            header_row = 4
        
        # Table Headers (Atomic Data Principles)
        headers = [
            "Tanggal", 
            "Pemanen", 
            "Lokasi", 
            "Janjang Valid (jjg)", 
            "BJR (kg)", 
            "Bruto (kg)", 
            "Ptgn Brondolan (kg)", 
            "Mentah (jjg)", 
            "Denda Mentah (Rp)", 
            "Netto (kg)"
        ]
        for col_num, header in enumerate(headers):
            worksheet.write(header_row, col_num, header, header_format)
            
        # Data (Canonical Data Model - Pure Numbers)
        start_data_row = header_row + 1
        for row_num, r in enumerate(records, start=start_data_row):
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

            # Raw Canonical Values
            valid_bunches = getattr(r, 'valid_bunch_count', 0)
            bjr = getattr(r, 'avg_bunch_weight_kg', 0)
            gross = getattr(r, 'gross_tonnage_kg', 0.0)
            loose_deduct = getattr(r, 'loose_fruit_deduction_kg', 0.0)
            unripe = getattr(r, 'unripe_bunch_count', 0)
            fine_amount = getattr(r, 'fine_amount_rupiah', 0.0)
            net = getattr(r, 'net_tonnage_kg', 0.0)

            # Pure Cell Writes
            worksheet.write(row_num, 0, date_str, cell_format)
            worksheet.write(row_num, 1, h_name, cell_format)
            worksheet.write(row_num, 2, loc_name, cell_format)
            worksheet.write_number(row_num, 3, valid_bunches, num_format)
            worksheet.write_number(row_num, 4, float(bjr), num_format)
            worksheet.write_number(row_num, 5, float(gross), num_format)
            worksheet.write_number(row_num, 6, float(loose_deduct), num_format)
            worksheet.write_number(row_num, 7, unripe, num_format)
            worksheet.write_number(row_num, 8, float(fine_amount), currency_format)
            worksheet.write_number(row_num, 9, float(net), num_format)
            
        # Set column widths
        worksheet.set_column('A:A', 14)
        worksheet.set_column('B:B', 24)
        worksheet.set_column('C:C', 14)
        worksheet.set_column('D:J', 18)
        
        workbook.close()
        output.seek(0)
        return output

