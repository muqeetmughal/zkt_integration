app_name = "zkt_integration"
app_title = "ZKT Biometrix Integration"
app_publisher = "Muqeet Mughal"
app_description = "A Frappe App for Frappe HRMS to Sync Biometric Employee Checkins From Device to ERPNext"
app_email = "muqeetmughal786@gmail.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["frappe/hrms"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "zkt_integration",
# 		"logo": "/assets/zkt_integration/logo.png",
# 		"title": "ZKT Biometrix Integration",
# 		"route": "/zkt_integration",
# 		"has_permission": "zkt_integration.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/zkt_integration/css/zkt_integration.css"
# app_include_js = "/assets/zkt_integration/js/zkt_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/zkt_integration/css/zkt_integration.css"
# web_include_js = "/assets/zkt_integration/js/zkt_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "zkt_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "zkt_integration/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "zkt_integration.utils.jinja_methods",
# 	"filters": "zkt_integration.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "zkt_integration.install.before_install"
after_install = "zkt_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "zkt_integration.uninstall.before_uninstall"
# after_uninstall = "zkt_integration.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "zkt_integration.utils.before_app_install"
# after_app_install = "zkt_integration.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "zkt_integration.utils.before_app_uninstall"
# after_app_uninstall = "zkt_integration.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "zkt_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"zkt_integration.tasks.all"
# 	],
# 	"daily": [
# 		"zkt_integration.tasks.daily"
# 	],
# 	"hourly": [
# 		"zkt_integration.tasks.hourly"
# 	],
# 	"weekly": [
# 		"zkt_integration.tasks.weekly"
# 	],
# 	"monthly": [
# 		"zkt_integration.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "zkt_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "zkt_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "zkt_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["zkt_integration.utils.before_request"]
# after_request = ["zkt_integration.utils.after_request"]

# Job Events
# ----------
# before_job = ["zkt_integration.utils.before_job"]
# after_job = ["zkt_integration.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"zkt_integration.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }


fixtures = [

  
    {"dt": "Server Script", "filters": [
        ["module", "in", [
            "ZKT Biometrix Integration"
        ]]
    ]},
]
