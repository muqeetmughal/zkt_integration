# Copyright (c) 2026, Muqeet Mughal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from zkt_integration.zkt_biometrix_integration.script import get_users,delete_user_from_device,set_user

class ZKTDeviceUser(Document):

	# ------------------------------------------------------------------
    # Function call while saving or updating
    # ------------------------------------------------------------------

	def save(self, *args, **kwargs):

		if not self.name:

			self.db_insert()

		else:

			self.db_update()

		return self
	
	# ------------------------------------------------------------------
    # Function call while Creating new user
    # ------------------------------------------------------------------
		
	def db_insert(self,*args, **kwargs):
		try:
			set_user(
            name=self.employee_name or "Employee",
            user_id=str(self.attendance_device_id) or "",
            uid=int(self.uid or 0),           
            password=self.password or "",    
            group_id=self.group_id or "",
            privilege=int(self.privilege or 0),
            card=int(self.card or 0)
        )
			if self.employee_name and self.attendance_device_id:
				
				frappe.db.set_value("Employee", self.employee_name, "attendance_device_id", self.attendance_device_id)
				
				frappe.msgprint(f"Employee {self.employee_name} Attendence Device Id {self.attendance_device_id} Updated.")
		except Exception as e:
			frappe.throw(f"Failed to add user {self.name}: {str(e)}")

	# ------------------------------------------------------------------
    # Function call while updating existing user
    # ------------------------------------------------------------------

	def db_update(self,*args,**kwargs):
		self.db_insert()

	# ------------------------------------------------------------------
    # Function call while Loading Data for Form View
    # ------------------------------------------------------------------

	def load_from_db(self):

		all_data = get_users()

		match = next((u for u in all_data if str(u.get("user_id")) == self.name), None)
		
		if not match:

			frappe.throw(f"Device user with ID {self.name} not found", frappe.DoesNotExistError)

		d = {
			"name": match.get("user_id"),
			"employee_name": match.get("name"),
			"attendance_device_id": match.get("user_id"),
			"uid":match["uid"],
			"password":match["password"],
			"group_id":match["group_id"],
			"card":match["card"],
			"privilege":match["privilege"]
		}

		super(Document, self).__init__(d)
	
	# ------------------------------------------------------------------
    # Function call while Deleting User (Single/Bulk)
    # ------------------------------------------------------------------
	

	def delete(self):
		try:
			delete_user_from_device(self.name)
			frappe.db.set_value("Employee", self.employee_name, "attendance_device_id", "")
			
			frappe.msgprint(f"Employee {self.employee_name} Attendence Device Record {self.attendance_device_id} Deleted.")			
		except Exception as e:
			frappe.throw(f"Failed to delete device user {self.name}: {str(e)}")

	# ------------------------------------------------------------------
    # Function call For List view
    # ------------------------------------------------------------------

	@staticmethod
	def get_list(args):
		
		raw_users = get_users()
		formatted_list = []

		for user in raw_users:

			formatted_list.append({
				"name": user.get("user_id"), 
				"employee_name": user.get("name"), 
				"attendance_device_id": user.get("user_id")
			})
		
		return formatted_list

		

	@staticmethod
	def get_count(args):
		count=get_users()
		return len(count)

	@staticmethod
	def get_stats(args):
		pass



	






