import frappe


def calculate_split_tax(doc, method):

    if not doc.items:
        return

    # =========================================
    # TOTAL VALUE
    # =========================================

    total = doc.net_total

    # =========================================
    # SPLIT PERCENTAGES
    # =========================================

    material_percent = 70
    labour_percent = 30

    # =========================================
    # GROSS VALUES
    # =========================================

    material_gross = total * (material_percent / 100)
    labour_gross = total * (labour_percent / 100)

    # =========================================
    # REMOVE INCLUDED GST
    # =========================================

    material_net = material_gross / 1.05
    labour_net = labour_gross / 1.18

    # =========================================
    # GST VALUES
    # =========================================

    material_tax = material_gross - material_net
    labour_tax = labour_gross - labour_net

    # =========================================
    # STORE CUSTOM VALUES
    # =========================================

    doc.custom_material_net = round(material_net, 2)
    doc.custom_labour_net = round(labour_net, 2)

    doc.custom_material_tax = round(material_tax, 2)
    doc.custom_labour_tax = round(labour_tax, 2)

    # =========================================
    # CLEAR TAX TABLE
    # =========================================

    doc.set("taxes", [])

    # =========================================
    # LABOUR CHARGE
    # =========================================

    doc.append("taxes", {
        "charge_type": "Actual",
        "account_head": "Labour charge - MMC",
        "tax_amount": round(labour_net, 2),
        "description": "Labour charge"
    })

    # =========================================
    # CGST 2.5%
    # =========================================

    doc.append("taxes", {
        "charge_type": "Actual",
        "account_head": "CGST OUTPUT @2.5% - MMC",
        "tax_amount": round(material_tax / 2, 2),
        "description": "CGST OUTPUT @2.5%"
    })

    # =========================================
    # SGST 2.5%
    # =========================================

    doc.append("taxes", {
        "charge_type": "Actual",
        "account_head": "SGST OUTPUT @2.5% - MMC",
        "tax_amount": round(material_tax / 2, 2),
        "description": "SGST OUTPUT @2.5%"
    })

    # =========================================
    # CGST 9%
    # =========================================

    doc.append("taxes", {
        "charge_type": "Actual",
        "account_head": "CGST OUTPUT @9% - MMC",
        "tax_amount": round(labour_tax / 2, 2),
        "description": "CGST OUTPUT @9%"
    })

    # =========================================
    # SGST 9%
    # =========================================

    doc.append("taxes", {
        "charge_type": "Actual",
        "account_head": "SGST OUTPUT @9% - MMC",
        "tax_amount": round(labour_tax / 2, 2),
        "description": "SGST OUTPUT @9%"
    })

    # =========================================
    # CALCULATE TOTALS
    # =========================================

    doc.calculate_taxes_and_totals()