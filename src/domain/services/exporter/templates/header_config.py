from datetime import datetime

class ReportHeaderConfig:
    COMPANY_NAME = "PT. BUMI PERTIWI AGRO"
    REPORT_TITLE = "LAPORAN REKAPITULASI PREMI PANEN"
    
    @classmethod
    def get_dynamic_header_data(cls):
        return {
            "company_name": cls.COMPANY_NAME,
            "report_title": cls.REPORT_TITLE,
            "print_date": datetime.now().strftime("%d %B %Y %H:%M"),
            "generator": "System Generated"
        }
