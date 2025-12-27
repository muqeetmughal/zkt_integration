import frappe
import json


def create_default_shift_type():
    shift_type_name = "Standard Office Shift"

    if frappe.db.exists("Shift Type", shift_type_name):
        print(f"Shift Type '{shift_type_name}' already exists.")
        return

    frappe.get_doc({
        "doctype": "Shift Type",
        "name": shift_type_name,
        "start_time": "12:00:00",
        "end_time": "21:00:00",
        "color": "Blue",
        "enable_auto_attendance": 0,
        "determine_check_in_and_check_out": "Alternating entries as IN and OUT during the same shift",
        "working_hours_calculation_based_on": "First Check-in and Last Check-out",
        "begin_check_in_before_shift_start_time": 60,
        "allow_check_out_after_shift_end_time": 60,
        "enable_late_entry_marking": 0,
        "late_entry_grace_period": 0,
        "enable_early_exit_marking": 0,
        "early_exit_grace_period": 0,
        "working_hours_threshold_for_half_day": 0.0,
        "working_hours_threshold_for_absent": 0.0,
        "process_attendance_after": frappe.utils.today(),
        "mark_auto_attendance_on_holidays": 0
    }).insert(ignore_permissions=True)

    print("✅ Shift Type created")


def setup_default_settings():
    settings_name = "ZKT Settings"

    if frappe.db.exists("ZKT Settings", settings_name):
        settings = frappe.get_doc("ZKT Settings", settings_name)
    else:
        settings = frappe.get_doc({"doctype": "ZKT Settings"})

    # ------------------------------
    # HANDLE JSON FIELD SAFELY
    # ------------------------------
    raw_mapping = settings.shift_type_device_mapping or "[]"

    try:
        mapping = json.loads(raw_mapping)
        if not isinstance(mapping, list):
            mapping = []
    except Exception:
        mapping = []

    # Ensure mapping exists
    exists = any(
        m.get("shift_type_name") == "Standard Office Shift"
        and "k40" in m.get("related_device_id", [])
        for m in mapping
    )

    if not exists:
        mapping.append({
            "shift_type_name": "Standard Office Shift",
            "related_device_id": ["k40"]
        })

    # Save back as JSON string
    settings.shift_type_device_mapping = json.dumps(mapping)

    # ------------------------------
    # DEVICE CONFIG
    # ------------------------------
    if not any(d.device_id == "k40" for d in settings.devices):
        settings.append("devices", {
            "device_id": "k40",
            "ip": "127.0.0.1",
            "punch_direction": "AUTO",
            "clear_from_device_on_fetch": 1,
            "latitude": 0,
            "longitude": 0,
            "pull_frequency": 60
        })

    settings.save(ignore_permissions=True)
    frappe.db.commit()

    print("✅ ZKT Settings configured successfully")


def after_install():
    create_default_shift_type()
    setup_default_settings()
