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
def calculate_custom_package_total(items=None):

    # --------------------------------------------------
    # GET ITEMS
    # --------------------------------------------------

    if items is None:
        try:
            request_data = frappe.request.get_json(silent=True) or {}
            items = request_data.get("items")
        except Exception:
            items = None

    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            frappe.throw("Invalid items JSON.")

    if not isinstance(items, list) or not items:
        frappe.throw("Please select at least one item.")

    # --------------------------------------------------
    # GET PAPER WORK FEES
    # FROM SOLAR PACKAGE WHERE ITEM GROUP = SOLAR PACKAGE
    # --------------------------------------------------

    package_rows = frappe.get_all(
        "Solar Package",
        filters={
            "item_group": "Solar Package"
        },
        fields=[
            "name",
            "paper_work_fees",
            "item_group"
        ],
        order_by="modified desc",
        limit=1
    )

    if not package_rows:
        frappe.throw(
            "No Solar Package found with Item Group = Solar Package."
        )

    paper_work_fees = float(
        package_rows[0].paper_work_fees or 0
    )

    # --------------------------------------------------
    # CALCULATE ITEM TOTAL
    # --------------------------------------------------

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

        # Get Standard Selling price
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

    # --------------------------------------------------
    # PRICE VALIDATION
    # --------------------------------------------------

    if missing_prices:
        frappe.throw(
            "No Standard Selling price found for: "
            + ", ".join(missing_prices)
        )

    # --------------------------------------------------
    # GRAND TOTAL
    # --------------------------------------------------

    grand_total = items_total + paper_work_fees

    return {
        "items_total": items_total,
        "paper_work": paper_work_fees,
        "grand_total": grand_total
    }


@frappe.whitelist(allow_guest=True)
def create_customer(
    customer_name,
    customer_type,
    gstin=None,
    gst_category=None,
    country="India",
    mobile_no=None,
    email_id=None
):
    try:
        allowed_customer_types = [
            "Company",
            "Individual",
            "Partnership"
        ]

        # Validate Customer Type
        if customer_type not in allowed_customer_types:
            return {
                "success": False,
                "message": "Invalid Customer Type"
            }

        # GSTIN is not mandatory for Individual
        if customer_type != "Individual" and gst_category == "Registered Regular":
            if not gstin:
                return {
                    "success": False,
                    "message": "GSTIN is required for Registered Regular customers"
                }

        # Check duplicate customer
        existing_customer = frappe.db.exists(
            "Customer",
            {
                "customer_name": customer_name
            }
        )

        if existing_customer:
            return {
                "success": False,
                "message": "Customer already exists",
                "customer": existing_customer
            }

        # Create Customer
        customer = frappe.new_doc("Customer")

        # Default fields
        customer.customer_name = customer_name
        customer.customer_group = "Individual"
        customer.customer_type = customer_type
        customer.territory = "All Territories"

        # Country
        if country:
            customer.country = country

        # Optional GST fields
        if gstin:
            customer.tax_id = gstin

        if gst_category:
            customer.gst_category = gst_category

        # Contact fields
        if mobile_no:
            customer.mobile_no = mobile_no

        if email_id:
            customer.email_id = email_id

        # Insert Customer
        customer.insert(ignore_permissions=True)

        frappe.db.commit()

        return {
            "success": True,
            "message": "Customer created successfully",
            "data": {
                "customer": customer.name,
                "customer_name": customer.customer_name,
                "customer_group": customer.customer_group,
                "customer_type": customer.customer_type,
                "gstin": customer.tax_id,
                "gst_category": customer.gst_category
            }
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Mobile Customer Creation Error"
        )

        return {
            "success": False,
            "message": "Failed to create customer"
        } 


@frappe.whitelist(allow_guest=True)
def create_customer_address(
    customer_name,
    address_title,
    address_type,
    address_line1,
    address_line2=None,
    city=None,
    state=None,
    country="India",
    is_primary_address=0,
    is_shipping_address=0
):
    try:
        # Validate Customer
        if not customer_name:
            return {
                "success": False,
                "message": "Customer is required"
            }

        if not frappe.db.exists("Customer", customer_name):
            return {
                "success": False,
                "message": "Customer not found"
            }

        # Validate Address
        if not address_title:
            return {
                "success": False,
                "message": "Address Title is required"
            }

        if not address_line1:
            return {
                "success": False,
                "message": "Address Line 1 is required"
            }

        # Create Address
        address = frappe.new_doc("Address")

        address.address_title = address_title
        address.address_type = address_type
        address.address_line1 = address_line1
        address.address_line2 = address_line2
        address.city = city
        address.state = state
        address.country = country

        address.is_primary_address = int(is_primary_address or 0)
        address.is_shipping_address = int(is_shipping_address or 0)

        # Link Address to Customer
        address.append("links", {
            "link_doctype": "Customer",
            "link_name": customer_name
        })

        # Insert Address
        address.insert(ignore_permissions=True)

        frappe.db.commit()

        return {
            "success": True,
            "message": "Customer address created successfully",
            "data": {
                "address": address.name,
                "address_title": address.address_title,
                "address_type": address.address_type,
                "customer": customer_name
            }
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Mobile Customer Address Creation Error"
        )

        return {
            "success": False,
            "message": "Failed to create customer address"
        }   


@frappe.whitelist()
def get_my_leads():
    try:
        # ---------------------------------------------------------
        # CURRENT LOGGED-IN USER
        # ---------------------------------------------------------
        current_user = frappe.session.user

        if not current_user or current_user == "Guest":
            frappe.throw("Please login to access leads.")

        # ---------------------------------------------------------
        # GET LEADS
        # ONLY LEADS OWNED BY CURRENT USER
        # ---------------------------------------------------------
        leads = frappe.get_all(
            "Lead",
            filters={
                "lead_owner": current_user
            },
            fields=[
                "name",
                "lead_name",
                "source",
                "status",
                "email_id",
                "mobile_no",
                "whatsapp_no",
                "lead_owner",
                "area",
                
            ],
            order_by="modified desc"
        )

        # ---------------------------------------------------------
        # PROCESS EACH LEAD
        # ---------------------------------------------------------
        for lead in leads:

            # -----------------------------------------------------
            # LEAD TRACKING
            # -----------------------------------------------------
            lead["lead_tracking"] = frappe.get_all(
                "Lead Tracking",
                filters={
                    "parent": lead["name"],
                    "parenttype": "Lead",
                    "parentfield": "lead_tracking"
                },
                fields=[
                    "date_and_time",
                    "status",
                    "feedback",
                    "userlink"
                ],
                order_by="date_and_time desc"
            )

            # -----------------------------------------------------
            # ADDRESS
            # Find Address records linked to this Lead
            # -----------------------------------------------------
            addresses = frappe.get_all(
                "Address",
                filters={
                    "link_doctype": "Lead",
                    "link_name": lead["name"]
                },
                fields=[
                    "name",
                    "address_title",
                    "address_type",
                    "address_line1",
                    "address_line2",
                    "city",
                    "state",
                    "country",
                    "pincode",
                    "email_id",
                    "phone",
                    "is_primary_address",
                    "is_shipping_address"
                ],
                order_by="is_primary_address desc"
            )

            lead["addresses"] = addresses

        # ---------------------------------------------------------
        # RESPONSE
        # ---------------------------------------------------------
        return {
            "success": True,
            "message": "Leads fetched successfully",
            "user": current_user,
            "count": len(leads),
            "data": leads
        }

    except Exception as e:

        frappe.log_error(
            title="Get My Leads API Error",
            message=frappe.get_traceback()
        )

        return {
            "success": False,
            "message": str(e),
            "data": []
        }

@frappe.whitelist()
def get_my_customers():
    try:
        # ---------------------------------------------------------
        # CURRENT LOGGED-IN USER
        # ---------------------------------------------------------
        current_user = frappe.session.user

        if not current_user or current_user == "Guest":
            frappe.throw("Please login to access customers.")

        # ---------------------------------------------------------
        # GET ONLY CUSTOMERS OWNED BY CURRENT USER
        # ---------------------------------------------------------
        customers = frappe.get_all(
            "Customer",
            filters={
                "custom_customer_owner": current_user
            },
            fields=[

                "customer_name",
                "customer_type",
                "customer_group",
                "territory",
                "gstin",
                "custom_zone_name",
                "custom_customer_owner",
                "mobile_no",
                "email_id",
                "primary_address",
                "customer_primary_contact"
            ],
            order_by="modified desc"
        )

        # ---------------------------------------------------------
        # RESPONSE
        # ---------------------------------------------------------
        return {
            "success": True,
            "message": "Customers fetched successfully",
            "user": current_user,
            "count": len(customers),
            "data": customers
        }

    except Exception as e:

        frappe.log_error(
            title="Get My Customers API Error",
            message=frappe.get_traceback()
        )

        return {
            "success": False,
            "message": str(e),
            "data": []
        }  



@frappe.whitelist()
def add_lead_follow_up(
    lead_name,
    status,
    feedback,
    date_and_time=None
):
    try:
        current_user = frappe.session.user

        # ==========================
        # LOGIN CHECK
        # ==========================
        if not current_user or current_user == "Guest":
            return {
                "success": False,
                "message": "Please login to add follow-up."
            }

        # ==========================
        # GET LEAD
        # ==========================
        lead = frappe.get_doc("Lead", lead_name)

        # ==========================
        # ONLY LEAD OWNER CAN ADD
        # FOLLOW-UP
        # ==========================
        if lead.lead_owner != current_user:
            return {
                "success": False,
                "message": "You can only add follow-up to your own leads."
            }

        # ==========================
        # ADD FOLLOW-UP
        # ==========================
        row = lead.append(
            "lead_tracking",
            {
                "date_and_time": date_and_time or frappe.utils.now_datetime(),
                "status": status,
                "feedback": feedback,
                "userlink": current_user
            }
        )

        # ==========================
        # SAVE LEAD
        # ==========================
        lead.save(ignore_permissions=True)

        frappe.db.commit()

        return {
            "success": True,
            "message": "Follow-up added successfully",
            "data": {
                
                "date_and_time": row.date_and_time,
                "status": row.status,
                "feedback": row.feedback,
                "userlink": row.userlink
            }
        }

    except Exception as e:
        frappe.log_error(
            title="Add Lead Follow-up API Error",
            message=frappe.get_traceback()
        )

        return {
            "success": False,
            "message": str(e)
        } 





@frappe.whitelist()
def get_my_payment_entries():
    """
    Get Payment Entries belonging to the logged-in sales user,
    including Payment References.
    """

    user = frappe.session.user

    if not user or user == "Guest":
        frappe.throw("Login required")

    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={
            "custom_sales_user": user
        },
        fields=[
            "name",
            "payment_type",
            "posting_date",
            "party_type",
            "party",
            "party_name",
            "paid_amount",
            "received_amount",
            "paid_from",
            "paid_to",
            "mode_of_payment",
            "reference_no",
            "reference_date",
            "remarks",
            "status",
            "company",
            "creation",
            "modified"
        ],
        order_by="posting_date desc, creation desc"
    )

    result = []

    for payment in payment_entries:

        references = frappe.get_all(
            "Payment Entry Reference",
            filters={
                "parent": payment.name,
                "parenttype": "Payment Entry"
            },
            fields=[
                "reference_doctype",
                "reference_name",
                "total_amount",
                "outstanding_amount",
                "allocated_amount"
            ],
            order_by="idx asc"
        )

        payment["references"] = references

        result.append(payment)

    return result