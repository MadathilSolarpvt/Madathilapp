# Copyright (c) 2026, sourav and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class SolarCalculation(Document):

    def validate(self):
        self.total_amount = (self.panel_rate or 0) * (self.panel_number or 0)