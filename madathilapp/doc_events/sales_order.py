import frappe

def calculate_commission(doc, method):

    doc.set("custom_commission_details", [])
    doc.total_commission = 0

    for row in doc.sales_team:

        sales_person = row.sales_person

        # Fetch role from Sales Person
        role = frappe.db.get_value(
            "Sales Person",
            sales_person,
            "custom_commision_role"
        )

        commission_amount = 0

        if role:

            # Fetch FIXED commission amount
            commission_amount = frappe.db.get_value(
                "Commission Role Master",
                role,
                "commission_amount"
            ) or 0

        doc.append("custom_commission_details", {
            "custom_sales_person": sales_person,
            "custom_role": role,
            "custom_commission": commission_amount
        })

        doc.total_commission += commission_amount