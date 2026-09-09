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
            "custom_sales_user",
            "custom_executive_name",
            "custom_closing_executive",
            "custom_franchise_name",
            "custom_franchise_commission",  # ADDED
        ],
        order_by="modified desc",
    )

    for order in sales_orders:

        # ============================================================
        # FRANCHISE COMMISSION
        # ============================================================

        if order.get("custom_franchise_name"):
            order["custom_franchise_commission"] = (
                order.get("custom_franchise_commission") or 0
            )

        # ============================================================
        # SALES ORDER ITEMS
        # ============================================================

        order["items"] = frappe.get_all(
            "Sales Order Item",
            filters={
                "parent": order["name"],
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

        sales_order_doc = frappe.get_doc(
            "Sales Order",
            order["name"],
        )

        commission_rows = (
            sales_order_doc.get("custom_applicant_commission_detail") or []
        )

        order["commission_details"] = [
            {
                "points": row.points or 0,
                "user": row.user or "",
            }
            for row in commission_rows
        ]

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

@frappe.whitelist()
def get_leave_application_access():
    user = frappe.session.user

    # ============================================================
    # HR USERS
    # ============================================================

    hr_roles = {
        "HR Manager",
        "HR User",
    }

    user_roles = set(frappe.get_roles(user))

    is_hr = bool(user_roles.intersection(hr_roles))

    # ============================================================
    # HR -> ALL EMPLOYEES
    # ============================================================

    if is_hr:
        employees = frappe.get_all(
            "Employee",
            filters={
                "status": "Active",
            },
            fields=[
                "name",
                "employee_name",
                "user_id",
                "company",
            ],
            order_by="employee_name asc",
            ignore_permissions=True,
        )

        leave_applications = frappe.get_all(
            "Leave Application",
            fields=[
                "name",
                "employee",
                "employee_name",
                "leave_type",
                "company",
                "from_date",
                "to_date",
                "description",
                # "leave_approver",
                # "leave_approver_name",
                "posting_date",
                "status",
                "half_day",
                "total_leave_days",
            ],
            order_by="creation desc",
            ignore_permissions=True,
        )

        return {
            "is_hr": True,
            "logged_in_user": user,
            "employees": employees,
            "leave_applications": leave_applications,
        }

    # ============================================================
    # NORMAL EMPLOYEE
    # ============================================================

    employee = frappe.db.get_value(
        "Employee",
        {
            "user_id": user,
            "status": "Active",
        },
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
            f"No active Employee is linked to the logged-in user: {user}"
        )

    leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            "employee": employee["name"],
        },
        fields=[
            "name",
            "employee",
            "employee_name",
            "leave_type",
            "company",
            "from_date",
            "to_date",
            "description",
            # "leave_approver",
            # "leave_approver_name",
            "posting_date",
            "status",
            "half_day",
            "total_leave_days",
        ],
        order_by="creation desc",
        ignore_permissions=True,
    )

    return {
        "is_hr": False,
        "logged_in_user": user,
        "employee": employee,
        "employees": [employee],
        "leave_applications": leave_applications,
    }    