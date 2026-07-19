import io
import xlsxwriter
from typing import List, Any
from .interfaces import BaseExporter
from .templates.header_config import ReportHeaderConfig

class ExcelExporter(BaseExporter):
    def generate(self, records: List[Any]) -> io.BytesIO:
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
        
        # Header
        worksheet.merge_range("A1:G1", header_data["company_name"], title_format)
        worksheet.merge_range("A2:G2", header_data["report_title"], subtitle_format)
        worksheet.merge_range("A3:G3", f"Tanggal Cetak: {header_data['print_date']}", workbook.add_format({'align': 'center'}))
        
        # Table Headers
        headers = ["Tanggal", "Pemanen", "Lokasi", "Janjang Valid", "BJR (kg)", "Bruto (kg)", "Potongan Brondolan (kg)", "Mentah (Denda)", "Netto (kg)"]
        for col_num, header in enumerate(headers):
            worksheet.write(4, col_num, header, header_format)
            
        # Data
        for row_num, r in enumerate(records, start=5):
            date_str = r.harvest_date.strftime("%Y-%m-%d") if hasattr(r.harvest_date, 'strftime') else str(r.harvest_date)
            # Assuming harvester name is available (might need to fetch or join, but we'll try to get it if it's there)
            h_name = getattr(r, 'harvester_name', str(r.harvester_id))
            
            # For V2 schema fields:
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

            worksheet.write(row_num, 0, date_str, cell_format)
            worksheet.write(row_num, 1, h_name, cell_format)
            worksheet.write(row_num, 2, "TPH " + str(getattr(r, 'collection_point_id', '-')), cell_format)
            worksheet.write(row_num, 3, getattr(r, 'valid_bunch_count', 0), num_format)
            worksheet.write(row_num, 4, getattr(r, 'avg_bunch_weight_kg', 0), num_format)
            worksheet.write(row_num, 5, gross, num_format)
            worksheet.write(row_num, 6, loose_deduct, num_format)
            worksheet.write(row_num, 7, denda_str, cell_format)
            worksheet.write(row_num, 8, net, num_format)
            
        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:E', 12)
        worksheet.set_column('F:G', 20)
        
        workbook.close()
        output.seek(0)
        return output
