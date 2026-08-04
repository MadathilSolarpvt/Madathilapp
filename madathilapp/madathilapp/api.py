import frappe

@frappe.whitelist()
def get_quotation_manager():
    user = frappe.db.sql("""
        SELECT
            hr.parent,
            u.full_name
        FROM `tabHas Role` hr
        INNER JOIN `tabUser` u
            ON u.name = hr.parent
        WHERE hr.role = 'Quotation Manager'
          AND u.enabled = 1
        LIMIT 1
    """, as_dict=True)

    return user[0] if user else {}