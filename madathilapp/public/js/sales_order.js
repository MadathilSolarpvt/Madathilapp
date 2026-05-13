frappe.ui.form.on('Sales Order', {

    refresh: function(frm) {
        calculate_commission(frm);
    },

    custom_kw: function(frm) {
        calculate_commission(frm);
    },

    additional_discount_amount: function(frm) {
        calculate_commission(frm);
    },

    validate: function(frm) {
        calculate_commission(frm);
    }

});

frappe.ui.form.on('Applicant Commission Detail', {

    percentage: function(frm, cdt, cdn) {

        let row = locals[cdt][cdn];

        let percentage =
            flt(row.percentage || 0);

        let amount =
            flt(row.amount || 0);

        let points =
            amount * percentage / 100;

        // Store ONLY in points
        frappe.model.set_value(
            cdt,
            cdn,
            'points',
            Math.round(points)
        );

        // Clear incentives field
        frappe.model.set_value(
            cdt,
            cdn,
            'incentives',
            0
        );
    }

});

function calculate_commission(frm) {

    let commission_data = {

        "2KW": {
            sales: 10075,
            closing: 5425,
            franchise: 3500
        },

        "3KW": {
            sales: 13325,
            closing: 7175,
            franchise: 5500
        },

        "4KW": {
            sales: 17550,
            closing: 9450,
            franchise: 6000
        },

        "5KW": {
            sales: 18525,
            closing: 9975,
            franchise: 6500
        },

        "6KW": {
            sales: 21125,
            closing: 11375,
            franchise: 7500
        },

        "8KW": {
            sales: 28275,
            closing: 15225,
            franchise: 9500
        },

        "10KW": {
            sales: 34775,
            closing: 18725,
            franchise: 11500
        }
    };

    let kw = frm.doc.custom_kw;

    if (!kw || !commission_data[kw]) {
        return;
    }

    let sales =
        commission_data[kw].sales;

    let closing =
        commission_data[kw].closing;

    let franchise =
        commission_data[kw].franchise;

    let total_commission =
        sales + closing;

    let discount =
        flt(frm.doc.base_discount_amount || 0);

    let remaining_commission =
        total_commission - discount;

    if (remaining_commission < 0) {
        remaining_commission = 0;
    }

    frm.set_value(
        'custom_sales_commission',
        sales
    );

    frm.set_value(
        'custom_closing_commission',
        closing
    );

    frm.set_value(
        'custom_franchise_commission',
        franchise
    );

    frm.set_value(
        'custom_total_commission_amount_calculated',
        remaining_commission + franchise
    );

    // CHILD TABLE

    if (frm.doc.custom_applicant_commission_detail) {

        frm.doc.custom_applicant_commission_detail.forEach(function(row) {

            row.amount =
                remaining_commission;

            let percentage =
                flt(row.percentage || 0);

            row.points =
                Math.round(
                    remaining_commission *
                    percentage / 100
                );

            // Clear incentives
            row.incentives = 0;

        });

        frm.refresh_field(
            'custom_applicant_commission_detail'
        );
    }
}