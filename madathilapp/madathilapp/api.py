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


@frappe.whitelist()
def get_my_quotations():

    user = frappe.session.user

    quotations = frappe.get_all(
        "Quotation",
        filters={
            "custom_sales_person": user
        },
        fields=[
            "name",
            "customer_name",
            "transaction_date",
            "valid_till",
            "status",
            "grand_total",
            "company"
        ],
        order_by="modified desc"
    )

    for quotation in quotations:

        file = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Quotation",
                "attached_to_name": quotation["name"]
            },
            fields=[
                "file_name",
                "file_url",
                "is_private"
            ],
            limit=1
        )

        quotation["attachment"] = file[0] if file else {}

    return quotations


@frappe.whitelist()
def get_quotation_attachment(quotation):

    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Quotation",
            "attached_to_name": quotation
        },
        fields=[
            "name",
            "file_name",
            "file_url",
            "is_private"
        ]
    )

    return files