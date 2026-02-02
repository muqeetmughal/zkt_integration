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