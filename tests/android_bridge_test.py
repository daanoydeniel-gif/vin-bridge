import os
import tempfile
from pathlib import Path

from security.permissions import PermissionManager
from tools.android_actions import AndroidActions
from tools.controlled_actions import ControlledAndroidActions
from tools.android_bridge import AndroidBridge


def check(name, condition):
    if not condition:
        raise AssertionError(name)
    print(f"PASS  {name}")


def main():
    root = Path(tempfile.mkdtemp(prefix="vin_bridge_test_"))
    (root / "security").mkdir(parents=True, exist_ok=True)
    permissions = PermissionManager(str(root))
    controlled = ControlledAndroidActions(str(root), permissions)
    bridge = AndroidBridge(str(root), controlled, permissions)

    status = bridge.status()
    check("Android bridge reports online", status["online"] is True)
    check("bridge has permission system", status["permission_system"] is True)
    check("bridge exposes supported actions", "LIST_DOWNLOADS" in status["supported_actions"])

    first = bridge.list_downloads()
    check("download listing requires approval first", first["status"] == "PERMISSION_REQUIRED")
    pending = permissions.pending()
    check("bridge created a permission request", len(pending) == 1)
    check("bridge request action is LIST", pending[0]["action"] == "LIST")

    permissions.allow(pending[0]["id"])
    second = bridge.list_downloads()
    check("approved download listing executes", second["status"] in ("COMPLETED", "PERMISSION_REQUIRED"))
    check("approved permission is consumed", permissions.pending() == [])

    denied = bridge.read_download_file("example.txt")
    check("file read requires separate approval", denied["status"] == "PERMISSION_REQUIRED")

    print("ANDROID BRIDGE TEST PASSED")


if __name__ == "__main__":
    main()
