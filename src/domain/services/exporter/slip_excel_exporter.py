import io
import xlsxwriter
from .templates.header_config import ReportHeaderConfig

class SlipExcelExporter:
    def generate(self, summary, harvester_name: str, employee_number: str, period_name: str) -> io.BytesIO:
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Slip Gaji")
        
        # Styles
        title_format = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
        })
        subtitle_format = workbook.add_format({
            'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#2ecc71', 'font_color': 'white', 'border': 1, 'align': 'left', 'valign': 'vcenter'
        })
        header_dark_format = workbook.add_format({
            'bold': True, 'bg_color': '#34495e', 'font_color': 'white', 'border': 1, 'align': 'left', 'valign': 'vcenter'
        })
        cell_format = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter'})
        num_format = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter'})
        currency_format = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter', 'num_format': '"Rp "#,##0'})
        total_format = workbook.add_format({
            'bold': True, 'bg_color': '#e8f5e9', 'border': 1, 'align': 'left', 'valign': 'vcenter'
        })
        total_currency_format = workbook.add_format({
            'bold': True, 'bg_color': '#e8f5e9', 'border': 1, 'align': 'right', 'valign': 'vcenter', 'num_format': '"Rp "#,##0'
        })
        
        header_data = ReportHeaderConfig.get_dynamic_header_data()
        
        # Header
        worksheet.merge_range("A1:F1", header_data["company_name"], title_format)
        worksheet.merge_range("A2:F2", "SLIP GAJI PEMANEN", subtitle_format)
        
        worksheet.merge_range(3, 0, 3, 2, f"Pemanen: {employee_number} - {harvester_name}", workbook.add_format({'bold': True}))
        worksheet.merge_range(3, 3, 3, 5, f"Periode: {period_name}", workbook.add_format({'bold': True, 'align': 'right'}))
        
        # Section 1: Rangkuman Prestasi Panen
        worksheet.merge_range("A5:F5", "Rangkuman Prestasi Panen", header_format)
        
        worksheet.merge_range(5, 0, 5, 3, "Total Janjang Masuk", cell_format)
        worksheet.merge_range(5, 4, 5, 5, f"{summary.total_valid_bunch_count} jjg", num_format)
        
        worksheet.merge_range(6, 0, 6, 3, "Total Janjang Denda (Mentah, dll)", cell_format)
        worksheet.merge_range(6, 4, 6, 5, f"{summary.total_unripe_bunch_count} jjg", num_format)
        
        worksheet.merge_range(7, 0, 7, 3, "Total Tonase Bersih (Netto)", cell_format)
        worksheet.merge_range(7, 4, 7, 5, f"{float(summary.total_net_tonnage_kg):,.2f} kg", num_format)
        
        current_row = 9
        
        # Section 2: Rincian Prestasi Harian
        if hasattr(summary, 'daily_records') and summary.daily_records:
            header_orange = workbook.add_format({
                'bold': True, 'bg_color': '#f39c12', 'font_color': 'white', 'border': 1, 'align': 'center', 'valign': 'vcenter'
            })
            worksheet.merge_range(current_row, 0, current_row, 5, "Rincian Prestasi Harian", header_orange)
            current_row += 1
            
            headers = ["Tanggal", "Jjg Valid", "Jjg Denda", "Netto (kg)", "Premi Brondol (Rp)", "Potongan (Rp)"]
            for col_num, header in enumerate(headers):
                worksheet.write(current_row, col_num, header, header_orange)
            current_row += 1
            
            for r in summary.daily_records:
                worksheet.write(current_row, 0, r.harvest_date.strftime("%d-%m-%Y") if hasattr(r, 'harvest_date') else "-", cell_format)
                worksheet.write(current_row, 1, r.valid_bunch_count, num_format)
                worksheet.write(current_row, 2, r.unripe_bunch_count, num_format)
                worksheet.write(current_row, 3, float(r.net_tonnage_kg), num_format)
                worksheet.write(current_row, 4, float(r.loose_fruit_premium_rupiah), currency_format)
                
                fine_format = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter', 'font_color': 'red', 'num_format': '"Rp "#,##0'})
                worksheet.write(current_row, 5, float(r.fine_amount_rupiah), fine_format)
                current_row += 1
                
            current_row += 1
        
        # Section 3: Rincian Pendapatan & Potongan
        worksheet.merge_range(current_row, 0, current_row, 3, "Rincian Pendapatan & Potongan", header_dark_format)
        worksheet.merge_range(current_row, 4, current_row, 5, "Jumlah (Rp)", header_dark_format)
        current_row += 1
        
        worksheet.merge_range(current_row, 0, current_row, 3, "Premi Brondolan (Loose Fruit)", cell_format)
        worksheet.merge_range(current_row, 4, current_row, 5, float(summary.total_loose_fruit_premium_rupiah), currency_format)
        current_row += 1
        if hasattr(summary, 'tier_details') and summary.tier_details:
            for t in summary.tier_details:
                desc = f"Premi Progresif Tier {getattr(t, 'tier_level', 0)} ({float(getattr(t, 'kg_in_tier', 0)):,.2f} kg x Rp {float(getattr(t, 'rate_per_kg', 0)):,.0f})"
                worksheet.merge_range(current_row, 0, current_row, 3, desc, cell_format)
                worksheet.merge_range(current_row, 4, current_row, 5, float(getattr(t, 'subtotal_rupiah', 0)), currency_format)
                current_row += 1
                
        worksheet.merge_range(current_row, 0, current_row, 3, f"Potongan Denda (Mode: {summary.fine_mode_used})", cell_format)
        fine_currency_format = workbook.add_format({'border': 1, 'align': 'right', 'valign': 'vcenter', 'font_color': 'red', 'num_format': '"Rp "#,##0'})
        worksheet.merge_range(current_row, 4, current_row, 5, -float(summary.total_fine_rupiah), fine_currency_format)
        current_row += 1
        
        worksheet.merge_range(current_row, 0, current_row, 3, "TOTAL PENDAPATAN BERSIH (NET PAY)", total_format)
        worksheet.merge_range(current_row, 4, current_row, 5, float(summary.total_net_pay_rupiah), total_currency_format)
        
        # Set column widths
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:D', 12)
        worksheet.set_column('E:F', 18)
        
        workbook.close()
        output.seek(0)
        return output
