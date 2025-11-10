import requests
import datetime
import json
import os
import time
# from pickledb import PickleDB
from zk import ZK
import frappe
from frappe.utils import convert_utc_to_system_timezone 

class AttendanceSyncService:

    # ---------------- CONFIGS (INLINE INSTEAD OF local_config) ---------------- #
    
    ERPNEXT_VERSION = 15

    # PULL_FREQUENCY = 0
    # LOGS_DIRECTORY = 'logs'
    IMPORT_START_DATE = None

    # devices = [
    #     {'device_id': 'k40', 'ip': '192.168.100.197', 'punch_direction': 'AUTO', 'clear_from_device_on_fetch': False,
    #      'latitude': 31.4926522, 'longitude': 74.3732663}
    # ]

    # shift_type_device_mapping = [
    #     {'shift_type_name': 'Standard Office Shift', 'related_device_id': ['k40']}
    # ]

    allowlisted_errors = [
        "No Employee found for the given employee field value",
        "Transactions cannot be created for an Inactive Employee",
        "This employee already has a log with the same timestamp"
    ]


    # ---------------- INITIALIZER ---------------- #
    def __init__(self, devices, shift_type_device_mapping, pull_frequency=15):
        # for device in devices:
        #     print(device.device_id,device.ip, device.punch_direction, device.clear_from_device_on_fetch, device.latitude, device.longitude)
        # if not os.path.exists(self.LOGS_DIRECTORY):
        #     os.makedirs(self.LOGS_DIRECTORY)
        # self.status = PickleDB(f"{self.LOGS_DIRECTORY}/status.json")
        # self.status = json.loads(last_status)   or {}
        
        self.shift_type_device_mapping = json.loads(shift_type_device_mapping) or []
        self.devices = devices or []
        self.PULL_FREQUENCY = pull_frequency


        self.device_punch_values_IN = [0, 4]
        self.device_punch_values_OUT = [1, 5]

        # print("Initialized AttendanceSyncService with devices:", self.devices)
        # print("Initialized AttendanceSyncService with pull frequency:", self.PULL_FREQUENCY)
        # print("Initialized AttendanceSyncService with shift type device mapping:", self.shift_type_device_mapping)
    def clear_attendance_from_machine(self, device):
        zk = ZK(device.ip, port=4370, timeout=10)
        conn = None
        for attempt in range(3):
            try:
                conn = zk.connect()
                conn.disable_device()
                conn.clear_attendance()
                print(f"Cleared attendance from device {device.device_id} ({device.ip})")
                conn.enable_device()
                break
            except Exception as e:    
                frappe.log_error(title="ZKT Sync Error", message=frappe.get_traceback())
                print("ERROR clearing attendance from device:", device.ip, str(e))
                time.sleep(3)
            finally:
                if conn: 
                    conn.disconnect()
        # if len(logs) > 1000:
        #     self.clear_attendance_from_machine(device)

    # ---------------- MAIN LOOP ---------------- #
    def run_once(self):
        
        try:
            last_lift_off = self._safe_date(frappe.cache.get_value('lift_off_timestamp'))

            print("Last Lift Off:", last_lift_off)
            print("Current Time:", datetime.datetime.now())
            print("Pull Frequency (minutes):", self.PULL_FREQUENCY)


            if (not last_lift_off) or (last_lift_off < datetime.datetime.now() - datetime.timedelta(minutes=self.PULL_FREQUENCY)):
                print("\n--- Starting Pull Cycle ---")
                frappe.cache.set_value('lift_off_timestamp', str(datetime.datetime.now()))

                for device in self.devices:
                    print(f"Processing Device: {device.get('device_id')} ({device.get('ip')})")
                    # print(f"Processing Device: {device.device_id} ({device.ip})")
                    self._pull_process_push(device)

                self._update_shift_sync()

                frappe.cache.set_value('mission_accomplished_timestamp', str(datetime.datetime.now()))
                print("--- Cycle Complete ---\n")

        except Exception as e:
            frappe.log_error(title="ZKT Sync Error", message=frappe.get_traceback())
            print("ERROR in main:", e)


    # ---------------- PULL + PROCESS + PUSH ---------------- #
    def _pull_process_push(self, device):
        logs = self._fetch_from_device(device)

        for log in logs:
            punch_dir = self._determine_direction(device, log['punch'])

            code, msg = self._send_to_erpnext(log['user_id'], log['timestamp'], device.device_id, punch_dir,
                                              device.latitude, device.longitude)

            if code == 200:
                print(f"[SUCCESS] {msg} | {log}")
            else:
                print(f"[FAILED] {code} | {msg} | {log}")

                if not any(err in msg for err in self.allowlisted_errors):
                    raise Exception("Halting Sync: Non-Allowlisted ERPNext Error")


    # ---------------- DEVICE FETCH ---------------- #
    def _fetch_from_device(self, device):
        zk = ZK(device.ip, port=4370, timeout=30)
        conn = None
        logs = []

        try:
            conn = zk.connect()
            conn.disable_device()
            try:
                device_time = conn.get_time()
                diff = abs((device_time - datetime.datetime.now()).total_seconds())

                if diff > 60:
                    print(f"Syncing device time for {device.device_id} (diff {diff:.1f}s)")
                    conn.set_time(datetime.datetime.now())

            except Exception as e:
                print(f"Time sync failed for {device.device_id}: {e}")

            last_sync_str = frappe.cache.get_value(f"{device.device_id}_last_sync")
            last_sync_time = self._safe_date(last_sync_str) if last_sync_str else None
            logs = conn.get_attendance()
            # Convert objects to dict
            logs = [x.__dict__ for x in logs]

            if last_sync_time:
                logs = [l for l in logs if l["timestamp"] > last_sync_time]
            print(f"Fetched {len(logs)} logs from device {device.device_id} ({device.ip})")

            if logs:
                last_timestamp = max(l["timestamp"] for l in logs)
                frappe.cache.set_value(f"{device.device_id}_last_sync", str(last_timestamp))

            # frappe.cache.set_value(f"{device.device_id}_last_sync", last_timestamp)
            frappe.cache.set_value(f"{device.device_id}_pull_timestamp", str(datetime.datetime.now()))
            # logs = [l for l in logs if l["timestamp"] > last_sync_time]

            if device.clear_from_device_on_fetch:
                conn.clear_attendance()

            conn.enable_device()

        except Exception as e:
            frappe.log_error(title="ZKT Sync Error", message=frappe.get_traceback())
            print("ERROR fetching from device:", device.ip, str(e))
        finally:
            if conn: conn.disconnect()

        return logs


    # ---------------- PUSH TO ERPNext ---------------- #
    def _send_to_erpnext(self, user_id, timestamp, device_id, log_type, latitude, longitude):
        # if self.ERPNEXT_VERSION > 13:
             
        # else:
        #     from erpnext.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field

        # from hrms.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field
        try:
            from hrms.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field
        except ImportError:
            from erpnext.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field


        for attempt in range(3):
            try:

                add_log_based_on_employee_field(
                    employee_field_value=user_id,
                    timestamp=str(timestamp),
                    device_id=device_id,
                    log_type=log_type,
                    latitude=latitude,
                    longitude=longitude
                )
                response = {'code':200, 'message': f"Log for user {user_id} at {timestamp} added successfully."}
                break
            except Exception as e:
                print(f"Attempt {attempt+1}: ERPNext push failed -> {e}")
                time.sleep(2)
                response = {'code':500, 'message': str(e)}

        if response['code'] != 200:
            print(f"Failed after 3 retries for user {user_id} at {timestamp}")
        return response['code'], response['message']


        print("ERPNext Response:", response)

                
            # url = f"{self.ERPNEXT_URL}/api/method/{endpoint_app}.hr.doctype.employee_checkin.employee_checkin.add_log_based_on_employee_field"

            # payload = {
            #     "employee_field_value": user_id,
            #     "timestamp": str(timestamp),
            #     "device_id": device_id,
            #     "log_type": log_type,
            #     "latitude": latitude,
            #     "longitude": longitude
            # }
            # print(
            #     "Payload: ", payload
            # )

            # headers = {
            #     "Authorization": f"token {self.ERPNEXT_API_KEY}:{self.ERPNEXT_API_SECRET}",
            #     "Accept": "application/json"
            # }


            # r = requests.post(url, json=payload, headers=headers)

            # if r.status_code == 200:
            #     return 200, r.json()["message"]["name"]
            # else:
            #     return r.status_code, self._extract_error(r)
    # 
            # print("Sending to ERPNext:", url)
            # return response['code'], response['message']

    # ---------------- SHIFT TIME SYNC ---------------- #
    # def _update_shift_sync(self):
    #     for mapping in self.shift_type_device_mapping:
    #         for shift in mapping["shift_type_name"] if etime.datetime.now()))
    def _update_shift_sync(self):
        for mapping in self.shift_type_device_mapping:
            shift_names = mapping.get("shift_type_name")
            if isinstance(shift_names, str):
                shift_names = [shift_names]
            for shift in shift_names:
                frappe.cache.set_value(f"{shift}_sync_timestamp", str(datetime.datetime.now()))



    # ---------------- UTILITIES ---------------- #
    def _determine_direction(self, device, punch_value):
        if device.punch_direction != "AUTO":
            return device.punch_direction
        if punch_value in self.device_punch_values_OUT:
            return "OUT"
        if punch_value in self.device_punch_values_IN:
            return "IN"
        return None

    def _extract_error(self, res):
        try:
            data = res.json()
            return data.get("exc", str(data))
        except:
            return str(res.text)

    def _safe_date(self, s):
        try:
            return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
        except:
            return None


# ---------------- RUN LOOP ---------------- #
if __name__ == "__main__":
    service = AttendanceSyncService()
    print("Service Running...")
    while True:
        try:
            service.run_once()
        except Exception as e:
            print(f"[ERROR] Cycle failed: {e}")
        time.sleep(60)


# if __name__ == "__main__":
#     service = AttendanceSyncService()

#     # print("Service Running...")
#     # while True:
#     service.run_once()
#         # time.sleep(15)
