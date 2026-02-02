import json
import datetime
import frappe
from zk import ZK


class AttendanceSyncService:

    def __init__(self, devices):
        self.devices = devices or []
        self.device_punch_in = [0, 4]
        self.device_punch_out = [1, 5]

    # ------------------------------------------------------------------
    # ENTRY POINT
    # ------------------------------------------------------------------
    def run(self):
        

        for device in self.devices:
            last_run = device.last_run

            if last_run:
                self._log("Calculating delta since last run for device:" + device.device_id)
                delta = (datetime.datetime.now() - last_run).total_seconds() / 60
                self._log("Delta (minutes):"+ str(delta) + " Pull Frequency:" + str(device.pull_frequency) + " Device ID:" + device.device_id)


                if delta < device.pull_frequency :
                    self._log("Skipping run; pull frequency not met.")
                    return
            self._log("Device last run: " + device.device_id + " " + str(last_run))
            self._log("Processing device: " + device.device_id)

            self._process_device(device)

            device.last_run = datetime.datetime.now()
            device.save(ignore_permissions=True)
            self._log("Before retry unsynced records process *Done") 

        self.retry_unsynced_records()

    # ------------------------------------------------------------------
    # DEVICE PIPELINE
    # ------------------------------------------------------------------
    def _process_device(self, device):
        logs = self._fetch_from_device(device)
        self._log("Fetched logs: " + str(len(logs)))

        if not logs:
            self._log(f"No logs found from device {device.device_id}")
            return

        total_logs = len(logs)
        synced_count = 0  # Counting Synced Logs From Device to Zkt Raw Attendence

        for log in logs:
            # Always store raw (idempotent)
            if self._store_raw_log(device, log):
             synced_count += 1  # Counting Synced Logs From Device to Zkt Raw Attendence

            # Skip if already synced
            if self._is_already_synced(device, log):
                
                continue

            # Try ERP sync
            success, response = self._push_to_erp(device, log)
            
            if success:
                self._mark_synced(device, log)

        self._log(f"Synced {synced_count}/{total_logs} logs")

        # ✅ Only clear device if ALL logs are synced
        if synced_count == total_logs and device.clear_from_device_on_fetch:
            self._log("All logs synced — clearing device: " + device.device_id)
            # self._clear_device(device)
        else:
            self._log("Not clearing device — pending unsynced logs remain")
            # ------------------------------------------------------------------
            # FETCH FROM DEVICE
            # ------------------------------------------------------------------
    def _fetch_from_device(self, device):
        zk = ZK(device.ip, port=4370, password=device.get_password("device_password"))
        conn = None

        try:
            conn = zk.connect()
            conn.disable_device()
            logs = conn.get_attendance()
            return [l.__dict__ for l in logs]

        except Exception as e:
            self._log(f"[DEVICE ERROR] {device.device_id} → {str(e)}")
            return []

        finally:
            if conn:
                conn.enable_device()
                conn.disconnect()

    # ------------------------------------------------------------------
    # RAW STORAGE (ANTI-DUPLICATE)
    # ------------------------------------------------------------------
    def _store_raw_log(self, device, log):
        if frappe.db.exists(
            "ZKT Raw Attendance",
            {
                "device_id": device.device_id,
                "user_id": log["user_id"],
                "timestamp": log["timestamp"],
            },
        ):
            return False
        
        #converting datetime log object to string for jason dumps
        def serialize(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        frappe.get_doc({
            "doctype": "ZKT Raw Attendance",
            "device_id": device.device_id,
            "user_id": log["user_id"],
            "timestamp": log["timestamp"],
            "punch": log["punch"],
            "raw_json": json.dumps(log, default=serialize),
            "synced": 0,
        }).insert(ignore_permissions=True)

        return True

    # ------------------------------------------------------------------
    # ERP SYNC  From Device logs After Storing in Raw Zkt Attendence
    # ------------------------------------------------------------------
    def _push_to_erp(self, device, log):
        from hrms.hr.doctype.employee_checkin.employee_checkin import (
            add_log_based_on_employee_field,
        )

        try:
            response = add_log_based_on_employee_field(
                employee_field_value=log["user_id"],
                timestamp=str(log["timestamp"]),
                device_id=device.device_id,
                log_type=self._resolve_direction(device, log["punch"]),
                latitude=device.latitude,
                longitude=device.longitude,
            )
            self._log("Pushing to ERPNext:" + str(response))
            print(response)
            
            return (True, response)

        except Exception as e:
            # print(e)
            self._log(f"[ERP ERROR] {str(e)}")
            return (False, str(e))

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def _resolve_direction(self, device, punch):
        if device.punch_direction != "AUTO":
            return device.punch_direction
        if punch in self.device_punch_in:
            return "IN"
        if punch in self.device_punch_out:
            return "OUT"
        return None

    def _clear_device(self, device):
        self._log("Clear Device Function Currently *Commented")

    #     self._log("Clearing device:" + device.device_id)  # change , to +
    #     try:
    #         zk = ZK(device.ip, port=4370, password=device.get_password("device_password"))
    #         conn = zk.connect()
    #         conn.clear_attendance()
    #         conn.disconnect()
    #     except Exception as e:
    #         self._log(f"[CLEAR FAIL] {device.device_id} → {str(e)}")

    def _log(self, msg):
        print(msg)
        frappe.get_doc({
            "doctype": "Attendance Device Log",
            "log_entry": msg,
            "log_time": datetime.datetime.now(),
        }).insert(ignore_permissions=True)


    def retry_unsynced_records(self, limit=50):
        """
        Retry pushing unsynced attendance records to ERP
        """
        self._log("Retrying unsynced records...")
        records = frappe.get_all(
            "ZKT Raw Attendance",
            filters={
                "synced": 0
            },
            fields=["name", "device_id", "user_id", "timestamp", "punch"],
            limit=limit
        )

        if not records:
            self._log("All Records Allready marked as *Synced")
            return

        for record in records:
            try:
                device = self._get_device(record["device_id"])
                success, response = self._push_to_erp(
                    device,
                    {
                        "user_id": record["user_id"],
                        "timestamp": record["timestamp"],
                        "punch": record["punch"]
                    }
                )

                if success:
                    frappe.db.set_value(
                        "ZKT Raw Attendance",
                        record["name"],
                        {
                            "synced": 1,
                            "last_attempt_at": frappe.utils.now()
                        }
                    )
                else:
                    self._mark_retry_failed(record["name"], response) #just below at line 247

            except Exception as e:
                self._mark_retry_failed(record["name"], str(e)) 


    #here we finding device details by device id that fetching from zkt raw att             
    def _get_device(self, device_id):
        for device in self.devices:
            if device.device_id == device_id:
                return device
        raise Exception(f"Device not found for ID: {device_id}")
    

    def _mark_retry_failed(self, name, error):
        current_retry_count = frappe.db.get_value("ZKT Raw Attendance", name, "retry_count") or 0
        if current_retry_count == 3:
            frappe.get_doc({
                "doctype": "Attendance Device Log",
                "log_entry": f"Max retry attempts reached for record {name}: {error}",
                "log_time": datetime.datetime.now(),
            }).insert(ignore_permissions=True)
        frappe.db.set_value(
            "ZKT Raw Attendance",
            name,
            {
                "retry_count": current_retry_count + 1,
                "last_error": error,
                "last_attempt_at": frappe.utils.now()
            }
        )


    def _is_already_synced(self, device, log):
        return frappe.db.exists(
            "ZKT Raw Attendance",
            {
                "device_id": device.device_id,
                "user_id": log["user_id"],
                "timestamp": log["timestamp"],
                "synced": 1
            }
        )

    def _mark_synced(self, device, log):
        frappe.db.set_value(
            "ZKT Raw Attendance",
            {
                "device_id": device.device_id,
                "user_id": log["user_id"],
                "timestamp": log["timestamp"],
            },
            "synced",
            1,
        )

# ----------------------------------------------------------------------
# PUBLIC ENTRY POINT (Scheduler / Button / Cron)
# ----------------------------------------------------------------------
@frappe.whitelist()
def clear_logs():
	frappe.db.delete("Attendance Device Log")
	frappe.db.commit()


#pull logs from device after every hour
@frappe.whitelist()
def sync_attendance_log_to_erpnext():
    settings = frappe.get_doc("ZKT Settings")

    service = AttendanceSyncService(
        devices=settings.get("devices") or []
    )


    service.run()

@frappe.whitelist()
def clear_device_logs(device_id):
    settings = frappe.get_doc("ZKT Settings")
    device = None
    for d in settings.get("devices") or []:
        if d.device_id == device_id:
            device = d
            break
    if not device:
        frappe.throw(f"Device not found: {device_id}")

    service = AttendanceSyncService(
        devices=[device],
    )
    service._clear_device(device) #Code line 174