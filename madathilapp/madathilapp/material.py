
import frappe
from frappe import _


# ============================================================
# 1. MATERIAL REQUEST -> MATERIAL TRACKING
# ============================================================

@frappe.whitelist()
def create_material_tracking_from_request(material_request):
    if not material_request:
        frappe.throw(_("Material Request is required."))

    # Fetch Material Request
    mr = frappe.get_doc("Material Request", material_request)
    mr.check_permission("read")

    # Find Sales Order from Material Request Items
    sales_orders = set()

    for row in mr.get("items", []):
        sales_order = row.get("sales_order")
        if sales_order:
            sales_orders.add(sales_order)

    # Fallback to custom Sales Order field
    if not sales_orders:
        custom_sales_order = mr.get("custom_sales_order")
        if custom_sales_order:
            sales_orders.add(custom_sales_order)

    if not sales_orders:
        frappe.throw(
            _("No Sales Order linked to Material Request {0}.").format(
                mr.name
            )
        )

    if len(sales_orders) > 1:
        frappe.throw(
            _("This Material Request is linked to multiple Sales Orders.")
        )

    sales_order_name = next(iter(sales_orders))

    # Fetch Sales Order
    so = frappe.get_doc("Sales Order", sales_order_name)
    so.check_permission("read")

    # Fetch formatted address from Sales Order
    address_details = so.get("address_display") or ""

    # Prevent duplicate Material Tracking
    existing = frappe.db.get_value(
        "Material Tracking",
        {"material_request": mr.name},
        "name",
    )

    if existing:
        frappe.throw(
            _("Material Tracking {0} already exists for this request.").format(
                existing
            )
        )

    # Create Material Tracking
    doc = frappe.new_doc("Material Tracking")
    doc.sales_order_number = so.name
    doc.material_request = mr.name
    doc.customer_name = so.customer_name or so.customer
    doc.address_details = address_details
    doc.kw = so.get("custom_kw") or 0

    doc.insert()

    return {"name": doc.name}


# ============================================================
# 2. MATERIAL TRACKING -> SITE MATERIAL TRACKING
# ============================================================

@frappe.whitelist()
def create_site_material_tracking(material_tracking):
    if not material_tracking:
        frappe.throw(_("Material Tracking is required."))

    # Fetch source Material Tracking
    source = frappe.get_doc("Material Tracking", material_tracking)
    source.check_permission("read")

    if not source.sales_order_number:
        frappe.throw(_("Sales Order is missing in Material Tracking."))

    # Fetch Sales Order
    so = frappe.get_doc("Sales Order", source.sales_order_number)
    so.check_permission("read")

    # Prevent duplicates using Sales Order
    existing = frappe.db.get_value(
        "Site Material Tracking",
        {"sales_order": source.sales_order_number},
        "name",
    )

    if existing:
        frappe.throw(
            _(
                "Site Material Tracking {0} already exists "
                "for Sales Order {1}."
            ).format(existing, source.sales_order_number)
        )

    # Create Site Material Tracking
    doc = frappe.new_doc("Site Material Tracking")
    doc.sales_order = source.sales_order_number
    doc.material_request = source.material_request
    doc.customer = so.customer
    doc.customer_name = source.customer_name
    doc.customer_address = source.address_details
    doc.kw = source.kw

    doc.insert()

    return {"name": doc.name}
