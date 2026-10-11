from .android_actions import AndroidActions


class ControlledAndroidActions:

    def __init__(self, root, permission_manager):
        self.permissions = permission_manager
        self.actions = AndroidActions(root)

    def list_downloads(self):
        target = "Downloads/"

        if not self.permissions.consume_approved("LIST", target):
            request_id = self.permissions.request("LIST", target)

            return (
                "PERMISSION REQUIRED\n"
                f"Request ID: {request_id}\n"
                f"Action: LIST\n"
                f"Target: {target}\n\n"
                "Use #permissions to review.\n"
                f"Use #allow {request_id} to approve."
            )

        return self.actions.list_downloads()

    def read_file(self, filename):
        safe_filename = filename.strip()
        target = f"Downloads/{safe_filename}"

        if not self.permissions.consume_approved("READ", target):
            request_id = self.permissions.request("READ", target)

            return (
                "PERMISSION REQUIRED\n"
                f"Request ID: {request_id}\n"
                f"Action: READ\n"
                f"Target: {target}\n\n"
                "Use #permissions to review.\n"
                f"Use #allow {request_id} to approve."
            )

        return self.actions.read_download_file(safe_filename)

    def open_url(self, url):
        url = url.strip()
        target = f"URL:{url}"

        if not self.permissions.consume_approved("OPEN_URL", target):
            request_id = self.permissions.request("OPEN_URL", target)

            return (
                "PERMISSION REQUIRED\n"
                f"Request ID: {request_id}\n"
                "Action: OPEN_URL\n"
                f"Target: {target}\n\n"
                "Use #permissions to review.\n"
                f"Use #allow {request_id} to approve."
            )

        return self.actions.open_url(url)
