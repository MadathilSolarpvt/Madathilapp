import frappe
import json


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





@frappe.whitelist()
def get_franchise_applications():

    records = frappe.get_all(
        "Franchise Application Form",
        filters={
            "docstatus": ["in", [0, 1]]
        },
        fields=["name"],
        order_by="name asc",
        limit_page_length=0,
        ignore_permissions=True
    )

    return [row.name for row in records]
   
@frappe.whitelist(allow_guest=True)
def get_solar_product_bundles():

    bundles = frappe.get_all(
        "Product Bundle",
        filters={
            "custom_group_name": "Solar Package"
        },
        fields=[
            "name",
            "new_item_code",
            "description",
            "custom_product_total_price",
            "custom_group_name"
        ],
        order_by="name asc",
        limit_page_length=0,
        ignore_permissions=True
    )

    result = []

    for bundle in bundles:

        # Get complete Product Bundle document
        doc = frappe.get_doc(
            "Product Bundle",
            bundle.name
        )

        items = []

        for row in doc.items:

            items.append({
                "item": row.item_code,
                "description": row.description,
                "qty": row.qty,
                "uom": row.uom
            })

        result.append({
            "name": bundle.name,
            "new_item_code": bundle.new_item_code,
            "description": bundle.description,
            "custom_product_total_price": bundle.custom_product_total_price,
            "custom_group_name": bundle.custom_group_name,
            "items": items
        })

    return result


@frappe.whitelist(allow_guest=True)
def get_solar_package_items():
    """
    Fetch Solar Package Items along with their Item Price.
    """

    items = frappe.get_all(
        "Item",
        filters={
            "item_group": "Solar Package",
            "disabled": 0
        },
        fields=[
            "item_code",
            "item_name",
            "description",
            "gst_hsn_code",
            "stock_uom"
        ]
    )

    result = []

    for item in items:

        prices = frappe.get_all(
            "Item Price",
            filters={
                "item_code": item.item_code,
                "custom_item_group": "Solar Package"
            },
            fields=[
                "price_list",
                "price_list_rate",
                "currency"
            ],
            order_by="creation desc"
        )

        result.append({
            "item_code": item.item_code,
            "item_name": item.item_name,
            "description": item.description,
            "gst_hsn_code": item.gst_hsn_code,
            "stock_uom": item.stock_uom,
            "prices": prices
        })

    return result






@frappe.whitelist(allow_guest=True)
def calculate_custom_package_total(items=None, solar_package=None):

    # ---------------------------------------------------------
    # GET DATA FROM JSON REQUEST
    # ---------------------------------------------------------

    if items is None or solar_package is None:
        try:
            request_data = frappe.request.get_json(silent=True) or {}

            if items is None:
                items = request_data.get("items")

            if solar_package is None:
                solar_package = request_data.get("solar_package")

        except Exception:
            pass

    # ---------------------------------------------------------
    # PARSE ITEMS
    # ---------------------------------------------------------

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            frappe.throw("Invalid items JSON.")

    if not isinstance(items, list) or not items:
        frappe.throw("Please select at least one item.")

    # ---------------------------------------------------------
    # SOLAR PACKAGE
    # ---------------------------------------------------------

    if not solar_package:
        frappe.throw("Please select a Solar Package.")

    # ---------------------------------------------------------
    # GET PAPER WORK FEES
    # ---------------------------------------------------------

    paper_work_fees = frappe.db.get_value(
        "Solar Package",
        solar_package,
        "paper_work_fees"
    )

    if paper_work_fees is None:
        frappe.throw(
            f"Paper Work Fees not found for Solar Package: {solar_package}"
        )

    paper_work_fees = float(paper_work_fees or 0)

    # ---------------------------------------------------------
    # CALCULATE ITEMS TOTAL
    # ---------------------------------------------------------

    items_total = 0.0
    missing_prices = []

    for row in items:

        if not isinstance(row, dict):
            continue

        item_code = str(
            row.get("item_code") or ""
        ).strip()

        try:
            qty = float(row.get("qty") or 0)
        except (TypeError, ValueError):
            qty = 0

        if not item_code or qty <= 0:
            continue

        # Get latest Standard Selling price
        price_rows = frappe.get_all(
            "Item Price",
            filters={
                "item_code": item_code,
                "price_list": "Standard Selling",
                "selling": 1
            },
            fields=["price_list_rate"],
            order_by="creation desc",
            limit=1
        )

        if not price_rows:
            missing_prices.append(item_code)
            continue

        price_list_rate = float(
            price_rows[0].price_list_rate or 0
        )

        # PRICE × QUANTITY
        items_total += price_list_rate * qty

    # ---------------------------------------------------------
    # MISSING PRICE
    # ---------------------------------------------------------

    if missing_prices:
        frappe.throw(
            "No Standard Selling price found for: "
            + ", ".join(missing_prices)
        )

    # ---------------------------------------------------------
    # FINAL TOTAL
    # ---------------------------------------------------------

    grand_total = items_total + paper_work_fees

    return {
        "items_total": items_total,
        "paper_work": paper_work_fees,
        "grand_total": grand_total
    }


