
import frappe
from frappe import _


# ============================================================
# 1. MATERIAL REQUEST -> MATERIAL TRACKING
# ============================================================

@frappe.whitelist()
def create_material_tracking_from_request(material_request):
    if not material_request:
        frappe.throw(_("Material Request is required."))

    mr = frappe.get_doc("Material Request", material_request)
    mr.check_permission("read")

    # Find Sales Order from Material Request Items
    sales_orders = set()

    for row in mr.get("items", []):
        sales_order = row.get("sales_order")
        if sales_order:
            sales_orders.add(sales_order)

    # Optional fallback if your site uses a custom parent field
    if not sales_orders:
        custom_sales_order = mr.get("custom_sales_order")
        if custom_sales_order:
            sales_orders.add(custom_sales_order)

    if not sales_orders:
        frappe.throw(
            _(
                "No Sales Order linked to Material Request {0}. "
                "Please check the Sales Order field in the Items table."
            ).format(mr.name)
        )

    if len(sales_orders) > 1:
        frappe.throw(
            _(
                "This Material Request is linked to multiple Sales Orders. "
                "Please create separate Material Tracking records."
            )
        )

    sales_order_name = next(iter(sales_orders))

    so = frappe.get_doc("Sales Order", sales_order_name)
    so.check_permission("read")

    # Get Sales Order shipping address
    customer_address = ""

    if so.get("shipping_address_name"):
        address = frappe.db.get_value(
            "Address",
            so.shipping_address_name,
            [
                "address_line1",
                "address_line2",
                "city",
                "state",
                "pincode",
                "country",
            ],
            as_dict=True,
        )

        if address:
            customer_address = "\n".join(
                str(value)
                for value in [
                    address.address_line1,
                    address.address_line2,
                    address.city,
                    address.state,
                    address.pincode,
                    address.country,
                ]
                if value
            )

    if not customer_address:
        customer_address = so.get("shipping_address") or ""

    # Prevent duplicate Material Tracking
    existing = frappe.db.get_value(
        "Material Tracking",
        {"material_request": mr.name},
        "name",
    )

    if existing:
        frappe.throw(
            _("Material Tracking {0} already exists for this request.")
            .format(existing)
        )

    # Create Material Tracking
    doc = frappe.new_doc("Material Tracking")
    doc.sales_order_number = so.name
    doc.material_request = mr.name
    doc.customer_name = so.customer_name or so.customer
    doc.customer_address = customer_address
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

    # Fetch Sales Order to obtain the Customer link
    so = frappe.get_doc("Sales Order", source.sales_order_number)
    so.check_permission("read")

    # Prevent duplicate Site Material Tracking
    # Requires a Link field named material_tracking
    # in Site Material Tracking.
    existing = frappe.db.get_value(
        "Site Material Tracking",
        {"material_tracking": source.name},
        "name",
    )

    if existing:
        frappe.throw(
            _("Site Material Tracking {0} already exists for this record.")
            .format(existing)
        )

    # Create Site Material Tracking
    doc = frappe.new_doc("Site Material Tracking")

    doc.material_tracking = source.name
    doc.sales_order = source.sales_order_number
    doc.material_request = source.material_request
    doc.customer = so.customer
    doc.customer_name = source.customer_name
    doc.customer_address = source.customer_address
    doc.kw = source.kw

    doc.insert()

    return {"name": doc.name}
