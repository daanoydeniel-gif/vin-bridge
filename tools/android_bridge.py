import os


class AndroidBridge:
    """Small, permission-aware bridge between Vin and Android/Termux tools.

    This bridge does not grant Android permissions. It exposes only actions that
    the installed Termux-side tools can actually perform, and delegates access
    checks to ControlledAndroidActions.
    """

    VERSION = "1.0"

    def __init__(self, root, controlled_actions, permission_manager):
        self.root = os.path.abspath(root)
        self.actions = controlled_actions
        self.permissions = permission_manager

    def status(self):
        storage = os.path.isdir(os.path.expanduser("~/storage/downloads"))
        return {
            "online": True,
            "version": self.VERSION,
            "termux_downloads": storage,
            "permission_system": True,
            "supported_actions": ["LIST_DOWNLOADS", "READ_DOWNLOAD_FILE", "OPEN_URL"],
        }

    def request(self, action, target):
        return {
            "success": False,
            "status": "PERMISSION_REQUIRED",
            "request_id": self.permissions.request(action, target),
            "action": action,
            "target": target,
        }

    def list_downloads(self):
        result = self.actions.list_downloads()
        return {
            "success": not str(result).startswith("PERMISSION REQUIRED"),
            "status": "COMPLETED" if not str(result).startswith("PERMISSION REQUIRED") else "PERMISSION_REQUIRED",
            "result": result,
        }

    def open_url(self, url):
        result = self.actions.open_url(url)

        return {
            "success": not str(result).startswith("PERMISSION REQUIRED"),
            "status": (
                "COMPLETED"
                if not str(result).startswith("PERMISSION REQUIRED")
                else "PERMISSION_REQUIRED"
            ),
            "result": result,
        }

    def read_download_file(self, filename):
        result = self.actions.read_file(filename)
        return {
            "success": not str(result).startswith("PERMISSION REQUIRED"),
            "status": "COMPLETED" if not str(result).startswith("PERMISSION REQUIRED") else "PERMISSION_REQUIRED",
            "result": result,
        }
