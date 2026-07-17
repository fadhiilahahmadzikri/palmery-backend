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
        headers = ["Tanggal", "Pemanen", "Janjang", "BJR (kg)", "Tonase (kg)", "Denda (Rp)", "Total Premi (Rp)"]
        for col_num, header in enumerate(headers):
            worksheet.write(4, col_num, header, header_format)
            
        # Data
        for row_num, r in enumerate(records, start=5):
            worksheet.write(row_num, 0, r.harvest_date.strftime("%Y-%m-%d") if hasattr(r.harvest_date, 'strftime') else str(r.harvest_date), cell_format)
            worksheet.write(row_num, 1, r.harvester_name, cell_format)
            worksheet.write(row_num, 2, r.input_total_bunches, num_format)
            worksheet.write(row_num, 3, r.input_avg_bunch_weight, num_format)
            worksheet.write(row_num, 4, r.calc_total_tonnage, num_format)
            worksheet.write(row_num, 5, r.input_unripe_penalty, currency_format)
            worksheet.write(row_num, 6, r.total_final_premium, currency_format)
            
        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:E', 12)
        worksheet.set_column('F:G', 20)
        
        workbook.close()
        output.seek(0)
        return output
