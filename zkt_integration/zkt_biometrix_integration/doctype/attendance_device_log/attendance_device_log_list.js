// Copyright (c) 2025, Muqeet Mughal and contributors
// For license information, please see license.txt

frappe.listview_settings['Attendance Device Log'] = {
    onload(listview) {
        const btn = listview.page.add_inner_button(__('Clear Logs'), () => {
            frappe.call({
                method: "zkt_integration.zkt_biometrix_integration.script.clear_logs",
                freeze: true,
                callback: function (r) {
                    frappe.msgprint(__('Attendance log cleared successfully.'));
                    listview.refresh();
                }
            });
        });

        // Make button RED
        btn.removeClass('btn-default').addClass('btn-danger');
    }

};
