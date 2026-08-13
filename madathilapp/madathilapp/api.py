import frappe


@frappe.whitelist()
def get_quotation_manager():

    users = frappe.db.sql("""
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

    return users[0] if users else {}


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

        files = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Quotation",
                "attached_to_name": quotation["name"]
            },
            fields=[
                "name",
                "file_name",
                "file_url",
                "is_private"
            ]
        )

        quotation["attachments"] = files

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



@frappe.whitelist()
def get_my_sales_orders():

    user = frappe.session.user

    sales_orders = frappe.get_all(
        "Sales Order",
        filters={
            "custom_sales_user": user
        },
        fields=[
            "name",
            "customer",
            "transaction_date",
            "delivery_date",
            "status",
            "grand_total",
            "company",
            "custom_sales_user"
        ],
        order_by="modified desc"
    )

    for order in sales_orders:

        order["items"] = frappe.get_all(
            "Sales Order Item",
            filters={
                "parent": order["name"]
            },
            fields=[
                "item_code",
                "item_name",
                "description",
                "qty",
                "uom",
                "rate",
                "amount",
                "delivery_date"
            ],
            order_by="idx asc"
        )

        order["attachments"] = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Sales Order",
                "attached_to_name": order["name"]
            },
            fields=[
                "file_name",
                "file_url",
                "is_private"
            ]
        )

    return {
        "logged_in_user": user,
        "sales_orders": sales_orders
    }