import frappe


@frappe.whitelist()
def get_quotation_manager():
    users = frappe.db.sql(
        """
        SELECT
            hr.parent,
            u.full_name
        FROM `tabHas Role` hr
        INNER JOIN `tabUser` u
            ON u.name = hr.parent
        WHERE hr.role = 'Quotation Manager'
          AND u.enabled = 1
        LIMIT 1
        """,
        as_dict=True,
    )

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
            "company",
        ],
        order_by="modified desc",
    )

    for quotation in quotations:
        files = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Quotation",
                "attached_to_name": quotation["name"],
            },
            fields=[
                "name",
                "file_name",
                "file_url",
                "is_private",
            ],
        )

        quotation["attachments"] = files

    return quotations


@frappe.whitelist()
def get_quotation_attachment(quotation):
    files = frappe.get_all(
        "File",
        filters={
            "attached_to_doctype": "Quotation",
            "attached_to_name": quotation,
        },
        fields=[
            "name",
            "file_name",
            "file_url",
            "is_private",
        ],
    )

    return files


@frappe.whitelist()
def get_my_sales_orders():
    user = frappe.session.user

    sales_orders = frappe.get_all(
        "Sales Order",

        # ============================================================
        # ALL USER RELATIONSHIPS ARE OR CONDITIONS
        # ============================================================
        filters={},

        or_filters=[
            # Main Sales User
            {"custom_sales_user": user},

            # Sales User -> Closing Executive
            {"custom_sales_user__closing_executive": user},

            # Sales User -> Franchise
            {"custom_sales_user__franchise": user},

            # Management hierarchy
            {"custom_am__sales_user": user},
            {"custom_rm__sales_user": user},
            {"custom_zm__sales_user": user},
            {"custom_agm__sales_user": user},
            {"custom_gm__sales_user": user},
            {"custom_vp__sales_user": user},

            # Sales Order Executive
            {"custom_executive_name": user},

            # Sales Order Closing Executive
            {"custom_closing_executive": user},
        ],

        fields=[
            "name",
            "customer",
            "transaction_date",
            "delivery_date",
            "status",
            "grand_total",
            "company",

            # Sales User
            "custom_sales_user",

            # Sales Order fields
            "custom_executive_name",
            "custom_closing_executive",

            # Franchise
            "custom_franchise_name",
        ],

        order_by="modified desc",
    )

    for order in sales_orders:

        # ============================================================
        # SALES ORDER ITEMS
        # ============================================================
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
                "delivery_date",
            ],
            order_by="idx asc",
        )

        # ============================================================
        # APPLICANT COMMISSION DETAILS
        # ============================================================
        order["commission_details"] = frappe.get_all(
            "Applicant Commission Detail",
            filters={
                "parent": order["name"]
            },
            fields=[
                "points",
                "user",
            ],
            order_by="idx asc",
        )

        # ============================================================
        # ATTACHMENTS
        # ============================================================
        order["attachments"] = frappe.get_all(
            "File",
            filters={
                "attached_to_doctype": "Sales Order",
                "attached_to_name": order["name"],
            },
            fields=[
                "file_name",
                "file_url",
                "is_private",
            ],
        )

    return {
        "logged_in_user": user,
        "sales_orders": sales_orders,
    }



@frappe.whitelist()
def get_my_employee():
    user = frappe.session.user

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        [
            "name",
            "employee_name",
            "user_id",
            "company",
        ],
        as_dict=True,
    )

    if not employee:
        frappe.throw(
            f"No Employee is linked to the logged-in user: {user}"
        )

    return employee


@frappe.whitelist()
def get_my_payment_verifications():
    user = frappe.session.user

    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["name", "employee_name"],
        as_dict=True,
    )

    if not employee:
        frappe.throw(
            f"No Employee is linked to the logged-in user: {user}"
        )

    payments = frappe.get_all(
        "Sales Payment Verification",
        filters={
            "sales_manager": employee["name"]
        },
        fields=[
            "name",
            "customer",
            "customer_name",
            "amount",
            "total_project_cost",
            "kw",
            "place",
            "utr_number",
            "transaction_image",
            "cheque_number",
            "cheque_image",
            "sales_manager",
            "manager_name",
            "workflow_state",
        ],
        order_by="modified desc",
        ignore_permissions=True,
    )

    return payments