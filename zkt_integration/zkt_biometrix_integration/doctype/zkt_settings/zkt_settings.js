// Copyright (c) 2025, Muqeet Mughal and contributors
// For license information, please see license.txt

frappe.ui.form.on('ZKT Settings', {
    refresh: function(frm) {
        // Add custom button to trigger sync
        frm.add_custom_button(__('Sync Attendance Logs'), function() {
            frappe.call({
                method: "zkt_integration.zkt_biometrix_integration.doctype.zkt_settings.zkt_settings.sync_attendance_log_to_erpnext",
                args: {},
                freeze: true,
                freeze_message: __("Syncing attendance logs..."),
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(__('Attendance logs synced successfully!'));
                        frm.reload_doc();
                    }
                }
            });
        }, __('Actions'));
    }
});
