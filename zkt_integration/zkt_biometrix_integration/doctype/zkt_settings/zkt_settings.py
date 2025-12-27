# Copyright (c) 2025, Muqeet Mughal and contributors
# For license information, please see license.txt
import json
import frappe
from frappe.model.document import Document
from zkt_integration.zkt_biometrix_integration.script import AttendanceSyncService

class ZKTSettings(Document):


	pass


@frappe.whitelist()
def get_zkt_settings():
	zkt_settings = frappe.get_doc("ZKT Settings")
	return zkt_settings

@frappe.whitelist()
def sync_attendance_log_to_erpnext():
	zkt_settings = frappe.get_doc("ZKT Settings")
	status = json.loads(zkt_settings.get("last_status"))
	for key in status:
		frappe.cache.set_value(f"{key}", status[key], expires_in_sec=3600)
	
	
	attendance_service = AttendanceSyncService(
		# last_status=zkt_settings.get("last_status") or {},
		devices=zkt_settings.get("devices") or [],
		shift_type_device_mapping=zkt_settings.get("shift_type_device_mapping") or [],
		pull_frequency=zkt_settings.get("pull_frequency"),
	)
	attendance_service.run_once()

	# Update last status in ZKT Settings
	new_status = {}
	for device in zkt_settings.get("devices") or []:
		pull_timestamp = frappe.cache.get_value(f"{device.device_id}_pull_timestamp")
		if pull_timestamp:
			new_status[f"{device.device_id}_pull_timestamp"] = pull_timestamp
			frappe.cache.delete_value(f"{device.device_id}_pull_timestamp")

	for mapping in json.loads(zkt_settings.get("shift_type_device_mapping")) or []:
		for shift in mapping["shift_type_name"] if isinstance(mapping["shift_type_name"], list) else [mapping["shift_type_name"]]:
			sync_timestamp = frappe.cache.get_value(f"{shift}_sync_timestamp")
			if sync_timestamp:
				new_status[f"{shift}_sync_timestamp"] = sync_timestamp
				frappe.cache.delete_value(f"{shift}_sync_timestamp")

	new_status["mission_accomplished_timestamp"] = frappe.cache.get_value('mission_accomplished_timestamp')
	frappe.cache.delete_value('mission_accomplished_timestamp')
	new_status["lift_off_timestamp"] = frappe.cache.get_value('lift_off_timestamp')
	frappe.cache.delete_value('lift_off_timestamp')


	print("Setting last status to:", new_status)
	frappe.db.set_value("ZKT Settings", zkt_settings.name, "last_status", json.dumps(new_status))


def clear_logs():
	frappe.db.delete("Attendance Device Log")
	frappe.db.commit()


