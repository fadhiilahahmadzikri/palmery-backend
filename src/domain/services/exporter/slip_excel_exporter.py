import io
import xlsxwriter
from datetime import datetime
from .templates.header_config import ReportHeaderConfig

class SlipExcelExporter:
    def generate(
        self, 
        summary, 
        harvester_name: str, 
        employee_number: str, 
        period_name: str,
        division_name: str = "Divisi Panen",
        block_code: str = "-"
    ) -> io.BytesIO:
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Slip Gaji")
        
        # Gridlines enabled
        worksheet.hide_gridlines(False)
        
        # Color Palette
        PRIMARY_GREEN = '#1c3d2e'
        LIGHT_GREEN = '#f0fdf4'
        BORDER_COLOR = '#d8dcd9'
        LIGHT_BORDER = '#eceeec'
        MUTED_TEXT = '#6b7280'
        TEXT_COLOR = '#16211a'
        RED_COLOR = '#8a1f1f'

        # Formats
        fmt_company = workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': TEXT_COLOR, 'valign': 'vcenter'
        })
        fmt_meta_company = workbook.add_format({
            'font_size': 8, 'font_color': MUTED_TEXT, 'valign': 'vcenter'
        })
        fmt_doc_period = workbook.add_format({
            'bold': True, 'font_size': 11, 'font_color': TEXT_COLOR, 'align': 'right', 'valign': 'vcenter'
        })
        fmt_doc_tag = workbook.add_format({
            'font_size': 8, 'font_color': MUTED_TEXT, 'align': 'right', 'valign': 'vcenter'
        })
        fmt_title = workbook.add_format({
            'bold': True, 'font_size': 15, 'font_color': TEXT_COLOR, 'valign': 'vcenter'
        })
        fmt_eyebrow = workbook.add_format({
            'font_size': 8, 'font_color': MUTED_TEXT, 'valign': 'vcenter'
        })

        fmt_section = workbook.add_format({
            'bold': True, 'font_size': 9, 'font_color': PRIMARY_GREEN, 'bottom': 2, 'bottom_color': PRIMARY_GREEN, 'valign': 'vcenter'
        })

        fmt_meta_label = workbook.add_format({
            'font_size': 7, 'font_color': MUTED_TEXT, 'valign': 'vcenter', 'top': 1, 'top_color': BORDER_COLOR
        })
        fmt_meta_val = workbook.add_format({
            'bold': True, 'font_size': 9.5, 'font_color': TEXT_COLOR, 'valign': 'vcenter', 'bottom': 1, 'bottom_color': BORDER_COLOR
        })

        fmt_th = workbook.add_format({
            'font_size': 8, 'font_color': MUTED_TEXT, 'bg_color': '#f8faf8', 'bottom': 1, 'bottom_color': BORDER_COLOR, 'valign': 'vcenter'
        })
        fmt_th_right = workbook.add_format({
            'font_size': 8, 'font_color': MUTED_TEXT, 'bg_color': '#f8faf8', 'bottom': 1, 'bottom_color': BORDER_COLOR, 'align': 'right', 'valign': 'vcenter'
        })

        fmt_td = workbook.add_format({'font_size': 9, 'bottom': 1, 'bottom_color': LIGHT_BORDER, 'valign': 'vcenter'})
        fmt_td_right = workbook.add_format({'font_size': 9, 'bottom': 1, 'bottom_color': LIGHT_BORDER, 'align': 'right', 'valign': 'vcenter'})
        fmt_td_num = workbook.add_format({'font_size': 9, 'bottom': 1, 'bottom_color': LIGHT_BORDER, 'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0.00'})
        fmt_td_currency = workbook.add_format({'font_size': 9, 'bottom': 1, 'bottom_color': LIGHT_BORDER, 'align': 'right', 'valign': 'vcenter', 'num_format': '"Rp "#,##0'})
        fmt_td_fine = workbook.add_format({'font_size': 9, 'font_color': RED_COLOR, 'bottom': 1, 'bottom_color': LIGHT_BORDER, 'align': 'right', 'valign': 'vcenter', 'num_format': '"Rp "#,##0'})

        fmt_col_total_label = workbook.add_format({'bold': True, 'font_size': 9, 'font_color': TEXT_COLOR, 'top': 2, 'top_color': PRIMARY_GREEN, 'valign': 'vcenter'})
        fmt_col_total_val = workbook.add_format({'bold': True, 'font_size': 9, 'font_color': TEXT_COLOR, 'top': 2, 'top_color': PRIMARY_GREEN, 'align': 'right', 'valign': 'vcenter', 'num_format': '"Rp "#,##0'})

        fmt_thp_box_label = workbook.add_format({'font_size': 8, 'font_color': MUTED_TEXT, 'valign': 'vcenter'})
        fmt_thp_box_val = workbook.add_format({
            'bold': True, 'font_size': 14, 'font_color': TEXT_COLOR, 'bg_color': LIGHT_GREEN, 'border': 2, 'border_color': PRIMARY_GREEN, 'align': 'center', 'valign': 'vcenter', 'num_format': '"Rp "#,##0'
        })

        fmt_sig_center = workbook.add_format({'font_size': 8.5, 'align': 'center', 'valign': 'vcenter'})
        fmt_sig_name = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter', 'top': 1, 'top_color': TEXT_COLOR})

        header_data = ReportHeaderConfig.get_dynamic_header_data()
        
        # 1. Letterhead
        worksheet.merge_range("A1:D1", header_data["company_name"], fmt_company)
        worksheet.merge_range("A2:D2", f"{header_data['address']} · Telp: {header_data['contact']} · {header_data['email']}", fmt_meta_company)
        worksheet.merge_range("E1:F1", "SLIP GAJI", fmt_doc_tag)
        worksheet.merge_range("E2:F2", period_name, fmt_doc_period)
        
        # 2. Document Title
        worksheet.merge_range("A4:F4", "DOKUMEN PENGGAJIAN · DIVISI PANEN", fmt_eyebrow)
        worksheet.merge_range("A5:F5", "Slip Gaji Pemanen", fmt_title)
        
        # 3. Employee Metadata Grid (Rows 7-8)
        worksheet.write("A7", "NIK / ID KARYAWAN", fmt_meta_label)
        worksheet.write("A8", employee_number, fmt_meta_val)
        
        worksheet.merge_range("B7:C7", "NAMA PEMANEN", fmt_meta_label)
        worksheet.merge_range("B8:C8", harvester_name, fmt_meta_val)
        
        worksheet.merge_range("D7:E7", "DIVISI / AFDELING", fmt_meta_label)
        worksheet.merge_range("D8:E8", division_name, fmt_meta_val)
        
        worksheet.write("F7", "BLOK KEBUN", fmt_meta_label)
        worksheet.write("F8", block_code, fmt_meta_val)
        
        # 4. Rangkuman Prestasi Panen (Row 10)
        worksheet.merge_range("A10:F10", "RANGKUMAN PRESTASI PANEN", fmt_section)
        
        worksheet.merge_range("A11:E11", "Total Janjang Masuk", fmt_td)
        worksheet.write("F11", f"{summary.total_valid_bunch_count} jjg", fmt_td_right)
        
        worksheet.merge_range("A12:E12", "Total Janjang Denda (Mentah, dll)", fmt_td)
        worksheet.write("F12", f"{summary.total_unripe_bunch_count} jjg", fmt_td_right)
        
        worksheet.merge_range("A13:E13", "Total Tonase Bersih (Netto)", fmt_td)
        worksheet.write("F13", f"{float(summary.total_net_tonnage_kg):,.2f} kg", fmt_td_right)
        
        current_row = 15
        
        # 5. Rincian Prestasi Harian
        if hasattr(summary, 'daily_records') and summary.daily_records:
            worksheet.merge_range(current_row, 0, current_row, 5, "RINCIAN PRESTASI HARIAN", fmt_section)
            current_row += 1
            
            headers = ["Tanggal", "Jjg Valid", "Jjg Denda", "Netto (kg)", "Premi Brondol (Rp)", "Potongan (Rp)"]
            for c_idx, h_text in enumerate(headers):
                align_fmt = fmt_th if c_idx == 0 else fmt_th_right
                worksheet.write(current_row, c_idx, h_text, align_fmt)
            current_row += 1
            
            for r in summary.daily_records:
                dt_str = r.harvest_date.strftime("%d-%m-%Y") if hasattr(r, 'harvest_date') and r.harvest_date else "-"
                worksheet.write(current_row, 0, dt_str, fmt_td)
                worksheet.write(current_row, 1, r.valid_bunch_count, fmt_td_right)
                worksheet.write(current_row, 2, r.unripe_bunch_count, fmt_td_right)
                worksheet.write(current_row, 3, float(r.net_tonnage_kg), fmt_td_num)
                worksheet.write(current_row, 4, float(r.loose_fruit_premium_rupiah), fmt_td_currency)
                worksheet.write(current_row, 5, float(r.fine_amount_rupiah), fmt_td_fine)
                current_row += 1
            current_row += 1

        # 6. Penerimaan & Potongan (2-Column Layout)
        worksheet.merge_range(current_row, 0, current_row, 5, "PENERIMAAN & POTONGAN", fmt_section)
        current_row += 1
        
        # Headers
        worksheet.merge_range(current_row, 0, current_row, 1, "PENERIMAAN", fmt_th)
        worksheet.write(current_row, 2, "JUMLAH (RP)", fmt_th_right)
        worksheet.merge_range(current_row, 3, current_row, 4, "POTONGAN", fmt_th)
        worksheet.write(current_row, 5, "JUMLAH (RP)", fmt_th_right)
        current_row += 1

        # Row 1: Loose Fruit Premium & Fine
        loose_rp = float(getattr(summary, 'total_loose_fruit_premium_rupiah', 0))
        fine_rp = float(getattr(summary, 'total_fine_rupiah', 0))
        fine_mode = getattr(summary, 'fine_mode_used', 'rupiah')

        worksheet.merge_range(current_row, 0, current_row, 1, "Premi Brondolan (Loose Fruit)", fmt_td)
        worksheet.write(current_row, 2, loose_rp, fmt_td_currency)
        worksheet.merge_range(current_row, 3, current_row, 4, f"Denda Panen (Mode: {fine_mode})", fmt_td)
        worksheet.write(current_row, 5, fine_rp, fmt_td_fine)
        current_row += 1

        # Tiers
        tier_details = getattr(summary, 'tier_details', []) or []
        tier_subtotal = sum(float(getattr(t, 'subtotal_rupiah', 0)) for t in tier_details)
        total_penerimaan = loose_rp + tier_subtotal

        for t in tier_details:
            t_level = getattr(t, 'tier_level', 0)
            t_kg = float(getattr(t, 'kg_in_tier', 0))
            t_rate = float(getattr(t, 'rate_per_kg', 0))
            t_sub = float(getattr(t, 'subtotal_rupiah', 0))
            desc = f"  Tier {t_level} ({t_kg:,.2f} kg x Rp {t_rate:,.0f})"
            
            worksheet.merge_range(current_row, 0, current_row, 1, desc, fmt_td)
            worksheet.write(current_row, 2, t_sub, fmt_td_currency)
            worksheet.merge_range(current_row, 3, current_row, 4, "", fmt_td)
            worksheet.write(current_row, 5, "", fmt_td_right)
            current_row += 1

        # Column Totals
        worksheet.merge_range(current_row, 0, current_row, 1, "Total Penerimaan", fmt_col_total_label)
        worksheet.write(current_row, 2, total_penerimaan, fmt_col_total_val)
        worksheet.merge_range(current_row, 3, current_row, 4, "Total Potongan", fmt_col_total_label)
        worksheet.write(current_row, 5, fine_rp, fmt_col_total_val)
        current_row += 2

        # 7. Take Home Pay
        worksheet.merge_range(current_row, 0, current_row, 2, "TOTAL DITERIMA (TAKE HOME PAY)", fmt_thp_box_label)
        worksheet.merge_range(current_row, 3, current_row, 5, f"{datetime.now().strftime('%d %B %Y')}", fmt_td_right)
        current_row += 1
        
        net_pay = float(getattr(summary, 'total_net_pay_rupiah', 0))
        worksheet.merge_range(current_row, 0, current_row + 1, 2, net_pay, fmt_thp_box_val)
        current_row += 3

        # 8. Signatures
        worksheet.merge_range(current_row, 0, current_row, 2, "Disetujui Oleh,", fmt_sig_center)
        worksheet.merge_range(current_row, 3, current_row, 5, "Diterima Oleh,", fmt_sig_center)
        current_row += 3
        
        worksheet.merge_range(current_row, 0, current_row, 2, "Asisten Divisi / Manager", fmt_sig_name)
        worksheet.merge_range(current_row, 3, current_row, 5, harvester_name, fmt_sig_name)

        # Set Column Widths
        worksheet.set_column('A:A', 16)
        worksheet.set_column('B:B', 16)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 18)
        
        workbook.close()
        output.seek(0)
        return output
