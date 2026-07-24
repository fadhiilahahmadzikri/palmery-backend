import base64
import os
from datetime import datetime

class ReportHeaderConfig:
    COMPANY_NAME = "PT. Palmery"
    REPORT_TITLE = "LAPORAN REKAPITULASI PREMI PANEN"
    ADDRESS = "Jl. Kebun Sawit Utama No. 88, Riau"
    CONTACT = "0812-3456-7890"
    EMAIL = "info@palmery.co.id"
    
    @classmethod
    def get_logo_base64(cls):
        logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
        return None

    @classmethod
    def get_dynamic_header_data(cls):
        return {
            "company_name": cls.COMPANY_NAME,
            "report_title": cls.REPORT_TITLE,
            "address": cls.ADDRESS,
            "contact": cls.CONTACT,
            "email": cls.EMAIL,
            "logo_path": cls.get_logo_base64(),
            "print_date": datetime.now().strftime("%d %B %Y %H:%M"),
            "generator": "System Generated"
        }
