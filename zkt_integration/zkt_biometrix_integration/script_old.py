import requests
import datetime
import json
import os
import time
# from pickledb import PickleDB
from zk import ZK
import frappe

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

    def create_log(self, text):
        print(text)
        current_time = datetime.datetime.now()
        doc = frappe.new_doc("Attendance Device Log")
        doc.log_entry = text
        doc.log_time = current_time
        doc.insert(ignore_permissions=True)

    # ---------------- INITIALIZER ---------------- #

    def __init__(self, devices, shift_type_device_mapping, pull_frequency=15):
        # for device in devices:
        #     print(device.device_id,device.ip, device.punch_direction, device.clear_from_device_on_fetch, device.latitude, device.longitude)
        # if not os.path.exists(self.LOGS_DIRECTORY):
        #     os.makedirs(self.LOGS_DIRECTORY)
        # self.status = PickleDB(f"{self.LOGS_DIRECTORY}/status.json")
        # self.status = json.loads(last_status)   or {}
        self.shift_type_device_mapping = json.loads(
            shift_type_device_mapping) or []
        self.devices = devices or []
        self.PULL_FREQUENCY = pull_frequency

        self.device_punch_values_IN = [0, 4]
        self.device_punch_values_OUT = [1, 5]

        self.create_log("Initialized AttendanceSyncService with devices:"+ str(self.devices) + "\n" + 
        "Initialized AttendanceSyncService with pull frequency:"+str(self.PULL_FREQUENCY) + " minutes" + "\n" + 
        "Initialized AttendanceSyncService with shift type device mapping:"+str(self.shift_type_device_mapping) + "\n")

    # ---------------- MAIN LOOP ---------------- #
    def run_once(self):

        try:
            last_lift_off = self._safe_date(
                frappe.cache.get_value('lift_off_timestamp'))

            self.create_log("Last Lift Off:"+str(last_lift_off)+"\n"+
            "Current Time:"+ str(datetime.datetime.now())+ "\n"+ 
            "Pull Frequency (minutes):"+ str(self.PULL_FREQUENCY))

            if (not last_lift_off) or (last_lift_off < datetime.datetime.now() - datetime.timedelta(minutes=self.PULL_FREQUENCY)):
                self.create_log("\n--- Starting Pull Cycle ---")
                frappe.cache.set_value(
                    'lift_off_timestamp', str(datetime.datetime.now()))

                for device in self.devices:
                    self.create_log(
                        f"Processing Device: {device.device_id} ({device.ip})")
                    self._pull_process_push(device)

                self._update_shift_sync()

                frappe.cache.set_value(
                    'mission_accomplished_timestamp', str(datetime.datetime.now()))
                self.create_log("--- Cycle Complete ---\n")

        except Exception as e:
            self.create_log("ERROR in main:"+ str(e))

    # ---------------- PULL + PROCESS + PUSH ---------------- #

    def _pull_process_push(self, device):
        logs = self._fetch_from_device(device)

        for log in logs:
            punch_dir = self._determine_direction(device, log['punch'])

            code, msg = self._send_to_erpnext(log['user_id'], log['timestamp'], device.device_id, punch_dir,
                                              device.latitude, device.longitude)

            if code == 200:
                self.create_log(f"[SUCCESS] [DEVICE: {device.device_id}] {msg} | {log}")
            else:
                self.create_log(f"[FAILED] {msg} | {log}")
                # continue

                if not any(err in msg for err in self.allowlisted_errors):
                    self.create_log(f"[HALT SYNC] Non-Allowlisted ERPNext Error: {msg}")
                    raise Exception(
                        "Halting Sync: Non-Allowlisted ERPNext Error")

    # ---------------- DEVICE FETCH ---------------- #

    def _fetch_from_device(self, device):
    
        zk = ZK(device.ip, port=4370, password=device.get_password("device_password"), timeout=30)
        conn = None
        logs = []

        try:
            conn = zk.connect()
            conn.disable_device()
            logs = conn.get_attendance()

            print("Raw logs fetched:", len(logs))

            # Convert objects to dict
            logs = [x.__dict__ for x in logs]
            self.create_log(
                f"Fetched {len(logs)} logs from device {device.device_id} ({device.ip})")
            frappe.cache.set_value(
                f"{device.device_id}_pull_timestamp", str(datetime.datetime.now()))

            if device.clear_from_device_on_fetch:
                conn.clear_attendance()

            conn.enable_device()

        except Exception as e:
            self.create_log("ERROR fetching from device:" + device.ip + " " + str(e))
        finally:
            if conn:
                conn.disconnect()

        return logs

    # ---------------- PUSH TO ERPNext ---------------- #

    def _send_to_erpnext(self, user_id, timestamp, device_id, log_type, latitude, longitude):
        # if self.ERPNEXT_VERSION > 13:

        # else:
        #     from erpnext.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field

        from hrms.hr.doctype.employee_checkin.employee_checkin import add_log_based_on_employee_field
        try:

            add_log_based_on_employee_field(
                employee_field_value=user_id,
                timestamp=str(timestamp),
                device_id=device_id,
                log_type=log_type,
                latitude=latitude,
                longitude=longitude
            )
            response = {
                'code': 200, 'message': f"Log for user {user_id} at {timestamp} added successfully."}
        except Exception as e:
            response = {'code': 500, 'message': str(e)}

        self.create_log("ERPNext Response:"+str(response))

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
        return response['code'], response['message']

    # ---------------- SHIFT TIME SYNC ---------------- #
    def _update_shift_sync(self):
        for mapping in self.shift_type_device_mapping:
            for shift in mapping["shift_type_name"] if isinstance(mapping["shift_type_name"], list) else [mapping["shift_type_name"]]:
                frappe.cache.set_value(
                    f"{shift}_sync_timestamp", str(datetime.datetime.now()))

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

    # print("Service Running...")
    # while True:
    service.run_once()
    # time.sleep(15)
