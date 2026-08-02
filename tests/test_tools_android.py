import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from unittest import mock
from importlib.machinery import SourceFileLoader


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS_ANDROID = REPO_ROOT / "tools" / "android"


def write_executable(path: pathlib.Path, contents: str) -> None:
    path.write_text(contents)
    path.chmod(0o755)


def png_bytes(width: int = 1080, height: int = 2400) -> bytes:
    import binascii
    import struct
    import zlib

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + chunk_type
            + data
            + struct.pack(">I", binascii.crc32(chunk_type + data) & 0xFFFFFFFF)
        )

    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    compressed = zlib.compress(raw, 9)
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            chunk(b"IDAT", compressed),
            chunk(b"IEND", b""),
        ]
    )


FAKE_ADB = r"""#!/usr/bin/env python3
import os
import pathlib
import sys


def load_arg(name, default=""):
    return os.environ.get(name, default)


args = sys.argv[1:]
device_id = None
if args[:2] == ["-s", args[1] if len(args) > 1 else ""]:
    device_id = args[1]
    args = args[2:]

if args == ["devices", "-l"]:
    sys.stdout.write(load_arg("FAKE_ADB_DEVICES", "List of devices attached\n"))
    sys.exit(0)

if args == ["exec-out", "screencap", "-p"]:
    path = load_arg("FAKE_ADB_PNG_PATH")
    prefix = load_arg("FAKE_ADB_PNG_PREFIX")
    if prefix:
        sys.stdout.buffer.write(prefix.encode() + b"\n")
    sys.stdout.buffer.write(pathlib.Path(path).read_bytes())
    sys.exit(0)

if args[:3] == ["shell", "uiautomator", "dump"]:
    xml = load_arg("FAKE_ADB_UI_XML")
    if args[3] == "/dev/tty":
        if load_arg("FAKE_ADB_UI_TTY_FAIL") == "1":
            sys.stderr.write("ERROR: dump failed\n")
            sys.exit(1)
        sys.stdout.write("UI hierchary dumped to: /dev/tty\n")
        sys.stdout.write(xml)
        sys.exit(0)
    if args[3] == "/sdcard/window_dump.xml":
        sys.stdout.write("UI hierchary dumped to: /sdcard/window_dump.xml\n")
        sys.exit(0)

if args == ["shell", "cat", "/sdcard/window_dump.xml"]:
    sys.stdout.write(load_arg("FAKE_ADB_UI_XML"))
    sys.exit(0)

if args == ["shell", "wm", "size"]:
    sys.stdout.write(load_arg("FAKE_ADB_WM_SIZE", "Physical size: 1080x2400\n"))
    sys.exit(0)

if args == ["shell", "wm", "density"]:
    sys.stdout.write(load_arg("FAKE_ADB_WM_DENSITY", "Physical density: 440\n"))
    sys.exit(0)

if args == ["shell", "getprop", "ro.product.model"]:
    sys.stdout.write(load_arg("FAKE_ADB_MODEL", "sdk_gphone64_arm64\n"))
    sys.exit(0)

if args == ["shell", "getprop", "ro.product.manufacturer"]:
    sys.stdout.write(load_arg("FAKE_ADB_MANUFACTURER", "Google\n"))
    sys.exit(0)

if args == ["shell", "getprop", "ro.build.version.release"]:
    sys.stdout.write(load_arg("FAKE_ADB_ANDROID_VERSION", "15\n"))
    sys.exit(0)

if args == ["shell", "getprop", "ro.build.version.sdk"]:
    sys.stdout.write(load_arg("FAKE_ADB_API_LEVEL", "35\n"))
    sys.exit(0)

if args == ["shell", "getprop", "ro.serialno"]:
    sys.stdout.write(load_arg("FAKE_ADB_SERIAL", (device_id or "emulator-5554") + "\n"))
    sys.exit(0)

if args == ["shell", "getprop", "ro.build.display.id"]:
    sys.stdout.write(load_arg("FAKE_ADB_BUILD", "test-build\n"))
    sys.exit(0)

if args == ["shell", "getprop", "sys.boot_completed"]:
    sys.stdout.write(load_arg("FAKE_ADB_BOOT_COMPLETED", "1\n"))
    sys.exit(0)

if args == ["shell", "dumpsys", "activity", "activities"]:
    sys.stdout.write(load_arg("FAKE_ADB_CURRENT_ACTIVITY", "mResumedActivity: ActivityRecord{ test com.example/.MainActivity}\n"))
    sys.exit(0)

if args[:3] == ["shell", "input", "text"]:
    sys.stdout.write("\n")
    sys.exit(0)

if args[:3] == ["shell", "input", "tap"]:
    sys.stdout.write("\n")
    sys.exit(0)

if args[:3] == ["shell", "input", "keyevent"]:
    sys.stdout.write("\n")
    sys.exit(0)

if args[:3] == ["shell", "input", "swipe"]:
    sys.stdout.write("\n")
    sys.exit(0)

if args[:2] == ["logcat", "-c"]:
    sys.stdout.write("\n")
    sys.exit(0)

if args[:2] == ["logcat", "-d"]:
    sys.stdout.write(load_arg("FAKE_ADB_LOGCAT", "03-20 12:00:00.000  1234  1234 E Example: boom\n"))
    sys.exit(0)

if args[:2] == ["shell", "pidof"]:
    sys.stdout.write(load_arg("FAKE_ADB_PIDOF", "1234\n"))
    sys.exit(0)

if args[:2] == ["install", "-r"]:
    sys.stdout.write(load_arg("FAKE_ADB_INSTALL_OUTPUT", "Success\n"))
    sys.exit(0)

if args[:3] == ["shell", "monkey", "-p"]:
    sys.stdout.write("Events injected: 1\n")
    sys.exit(0)

if args[:3] == ["shell", "am", "start"]:
    sys.stdout.write("Starting: Intent\n")
    sys.exit(0)

if args[:3] == ["shell", "am", "force-stop"]:
    sys.stdout.write("\n")
    sys.exit(0)

if args[:3] == ["shell", "pm", "clear"]:
    sys.stdout.write(load_arg("FAKE_ADB_PM_CLEAR", "Success\n"))
    sys.exit(0)

if args == ["shell", "ip", "route"]:
    sys.stdout.write(load_arg(
        "FAKE_ADB_IP_ROUTE",
        "192.168.1.0/24 dev wlan0 proto kernel scope link src 192.168.1.42\n",
    ))
    sys.exit(0)

if args == ["shell", "ip", "-4", "addr", "show", "wlan0"]:
    sys.stdout.write(load_arg("FAKE_ADB_IP_ADDR", ""))
    sys.exit(0)

if args[:1] == ["tcpip"]:
    sys.stdout.write("restarting in TCP mode port: " + args[1] + "\n")
    sys.exit(0)

if args[:1] == ["connect"]:
    sys.stdout.write(load_arg("FAKE_ADB_CONNECT_OUTPUT", "connected to " + args[1] + "\n"))
    sys.exit(0)

if args[:1] == ["disconnect"]:
    sys.stdout.write("disconnected " + (args[1] if len(args) > 1 else "everything") + "\n")
    sys.exit(0)

if args[:1] == ["pair"]:
    sys.stdout.write(load_arg("FAKE_ADB_PAIR_OUTPUT", "Successfully paired to " + args[1] + " [guid=adb-test]\n"))
    sys.exit(0)

sys.stderr.write("Unhandled fake adb args: " + " ".join(args) + "\n")
sys.exit(1)
"""


FAKE_EMULATOR = r"""#!/usr/bin/env python3
import os
import sys

args = sys.argv[1:]
if args == ["-list-avds"]:
    sys.stdout.write(os.environ.get("FAKE_EMULATOR_AVDS", "Pixel_9\nPixel_Fold\n"))
    sys.exit(0)

if args[:1] == ["-avd"]:
    sys.exit(0)

sys.stderr.write("Unhandled fake emulator args\n")
sys.exit(1)
"""


FAKE_TAILSCALE = r"""#!/usr/bin/env python3
import os
import sys

args = sys.argv[1:]
if args[:2] == ["ip", "-4"]:
    if args[2] == os.environ.get("FAKE_TAILSCALE_NAME", "my-phone"):
        sys.stdout.write(os.environ.get("FAKE_TAILSCALE_IP", "100.101.102.103") + "\n")
        sys.exit(0)
    sys.stderr.write("no such host\n")
    sys.exit(1)

sys.stderr.write("Unhandled fake tailscale args\n")
sys.exit(1)
"""


SAMPLE_UI_XML = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Login" resource-id="com.example:id/btn_login" class="android.widget.Button" content-desc="" clickable="true" enabled="true" focused="false" checked="false" scrollable="false" bounds="[100,200][300,260]" />
  <node index="1" text="" resource-id="" class="android.view.View" content-desc="Navigate up" clickable="true" enabled="true" focused="false" checked="false" scrollable="false" bounds="[0,0][80,80]" />
</hierarchy>
"""


@unittest.skipIf(os.name == "nt", "Fake adb/emulator binaries are POSIX shebang scripts")
class AndroidToolTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tempdir = tempfile.TemporaryDirectory()
        base = pathlib.Path(cls._tempdir.name)
        sdk = base / "sdk"
        platform_tools = sdk / "platform-tools"
        emulator_dir = sdk / "emulator"
        platform_tools.mkdir(parents=True)
        emulator_dir.mkdir(parents=True)

        cls.png_path = base / "screen.png"
        cls.png_path.write_bytes(png_bytes(320, 640))
        cls.apk_path = base / "app-debug.apk"
        cls.apk_path.write_bytes(b"fake-apk")

        extra_bin = base / "bin"
        extra_bin.mkdir()
        write_executable(platform_tools / "adb", FAKE_ADB)
        write_executable(emulator_dir / "emulator", FAKE_EMULATOR)
        write_executable(extra_bin / "tailscale", FAKE_TAILSCALE)

        cls.sdk = sdk
        cls.base = base
        cls.extra_bin = extra_bin

    @classmethod
    def tearDownClass(cls):
        cls._tempdir.cleanup()

    def base_env(self):
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["ANDROID_HOME"] = str(self.sdk)
        env["FAKE_ADB_DEVICES"] = (
            "List of devices attached\n"
            "emulator-5554          device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 device:emu64a transport_id:1\n"
        )
        env["FAKE_ADB_UI_XML"] = SAMPLE_UI_XML
        env["FAKE_ADB_PNG_PATH"] = str(self.png_path)
        env["FAKE_EMULATOR_AVDS"] = "Pixel_9\nPixel_Fold\n"
        return env

    def run_cli(self, *args, env=None):
        proc = subprocess.run(
            [sys.executable, str(TOOLS_ANDROID), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env=env or self.base_env(),
        )
        return proc

    def test_device_list_json(self):
        proc = self.run_cli("device", "list", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["devices"][0]["id"], "emulator-5554")

    def test_device_avds_json(self):
        proc = self.run_cli("device", "avds", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["avds"], ["Pixel_9", "Pixel_Fold"])

    def test_ui_find_returns_center_coordinates(self):
        proc = self.run_cli("ui", "find", "--by", "text", "--value", "Login", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["bestMatch"]["resourceId"], "com.example:id/btn_login")
        self.assertEqual(payload["bestMatch"]["center"], {"x": 200, "y": 230})

    def test_input_text_reports_escaped_value(self):
        proc = self.run_cli("input", "text", "--text", "Hello World!", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["escaped"], "Hello%sWorld\\!")

    def test_app_install_uses_explicit_package_name(self):
        proc = self.run_cli("app", "install", "--apk", str(self.apk_path), "--package", "com.example", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["packageName"], "com.example")
        self.assertEqual(payload["output"], "Success")

    def test_screenshot_reports_dimensions(self):
        out_path = pathlib.Path(self._tempdir.name) / "shot.png"
        proc = self.run_cli("screenshot", "--out", str(out_path), "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["width"], 320)
        self.assertEqual(payload["height"], 640)

    def test_screenshot_strips_multi_display_warning(self):
        env = self.base_env()
        env["FAKE_ADB_PNG_PREFIX"] = "[Warning] Multiple displays were found, but no display id was specified!"
        out_path = pathlib.Path(self._tempdir.name) / "shot-warned.png"
        proc = self.run_cli("screenshot", "--out", str(out_path), "--json", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["width"], 320)
        self.assertEqual(payload["height"], 640)
        self.assertTrue(out_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"))

    def test_input_long_press_reports_duration(self):
        proc = self.run_cli("input", "long-press", "--x", "100", "--y", "200", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["action"], "long-press")
        self.assertEqual(payload["durationMs"], 600)

    def test_input_double_tap_reports_gap(self):
        proc = self.run_cli("input", "double-tap", "--x", "100", "--y", "200", "--gap", "50", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["action"], "double-tap")
        self.assertEqual(payload["gapMs"], 50)

    def test_input_text_rejects_non_ascii(self):
        proc = self.run_cli("input", "text", "--text", "héllo", "--json")
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stderr)
        self.assertIn("non-ASCII", payload["error"])

    def test_app_stop_reports_package(self):
        proc = self.run_cli("app", "stop", "--package", "com.example", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["packageName"], "com.example")
        self.assertTrue(payload["stopped"])

    def test_app_clear_reports_success(self):
        proc = self.run_cli("app", "clear", "--package", "com.example", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["cleared"])

    def test_device_list_reports_connection_type(self):
        env = self.base_env()
        env["FAKE_ADB_DEVICES"] = (
            "List of devices attached\n"
            "R3CN30ABCDE            device model:SM_F956B\n"
            "192.168.1.42:5555      device model:SM_F956B\n"
            "emulator-5554          device model:sdk_gphone64_arm64\n"
        )
        proc = self.run_cli("device", "list", "--json", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        connections = {device["id"]: device["connection"] for device in payload["devices"]}
        self.assertEqual(connections["R3CN30ABCDE"], "usb")
        self.assertEqual(connections["192.168.1.42:5555"], "tcp")
        self.assertEqual(connections["emulator-5554"], "emulator")

    def test_connect_wifi_end_to_end(self):
        env = self.base_env()
        env["FAKE_ADB_DEVICES"] = (
            "List of devices attached\n"
            "R3CN30ABCDE            device model:SM_F956B\n"
        )
        proc = self.run_cli("connect", "wifi", "--json", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["usbDeviceId"], "R3CN30ABCDE")
        self.assertEqual(payload["deviceId"], "192.168.1.42:5555")
        self.assertTrue(payload["connected"])

    def test_connect_wifi_requires_usb_device(self):
        env = self.base_env()
        env["FAKE_ADB_DEVICES"] = (
            "List of devices attached\n"
            "192.168.1.42:5555      device model:SM_F956B\n"
        )
        proc = self.run_cli("connect", "wifi", "--json", env=env)
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stderr)
        self.assertIn("No USB-connected device", payload["error"])

    def test_connect_ip_reports_failure(self):
        env = self.base_env()
        env["FAKE_ADB_CONNECT_OUTPUT"] = "failed to connect to '10.0.0.9:5555': Connection refused\n"
        proc = self.run_cli("connect", "ip", "--host", "10.0.0.9", "--json", env=env)
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stderr)
        self.assertIn("Could not connect to 10.0.0.9:5555", payload["error"])

    def test_connect_tailscale_resolves_machine_name(self):
        env = self.base_env()
        env["PATH"] = str(self.extra_bin) + os.pathsep + env["PATH"]
        env["FAKE_TAILSCALE_NAME"] = "my-phone"
        env["FAKE_TAILSCALE_IP"] = "100.101.102.103"
        proc = self.run_cli("connect", "tailscale", "--host", "my-phone", "--json", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["host"], "100.101.102.103")
        self.assertEqual(payload["deviceId"], "100.101.102.103:5555")
        self.assertEqual(payload["tailscaleHost"], "my-phone")

    def test_connect_pair_succeeds(self):
        proc = self.run_cli(
            "connect", "pair", "--host", "192.168.1.42", "--port", "37123", "--code", "123456", "--json"
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["paired"])
        self.assertEqual(payload["endpoint"], "192.168.1.42:37123")

    def test_connect_disconnect_all(self):
        proc = self.run_cli("connect", "disconnect", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["disconnected"], "all")

    def test_app_clear_fails_cleanly(self):
        env = self.base_env()
        env["FAKE_ADB_PM_CLEAR"] = "Failed\n"
        proc = self.run_cli("app", "clear", "--package", "com.example", "--json", env=env)
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stderr)
        self.assertIn("pm clear failed", payload["error"])

    def test_multiple_devices_require_explicit_selection(self):
        env = self.base_env()
        env["FAKE_ADB_DEVICES"] = (
            "List of devices attached\n"
            "emulator-5554 device model:first\n"
            "emulator-5556 device model:second\n"
        )
        proc = self.run_cli("device", "info", "--json", env=env)
        self.assertEqual(proc.returncode, 1)
        payload = json.loads(proc.stderr)
        self.assertIn("Multiple devices detected", payload["error"])

    def test_debug_logs_filters_package_and_returns_lines(self):
        env = self.base_env()
        env["FAKE_ADB_LOGCAT"] = (
            "03-20 12:00:00.000  1234  1234 E Example: boom\n"
            "03-20 12:00:00.000  9999  9999 E Other: skip\n"
        )
        proc = self.run_cli("debug", "logs", "--package", "com.example", "--json", env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["lineCount"], 1)
        self.assertIn("Example: boom", payload["lines"][0])


class AndroidToolUnitTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loader = SourceFileLoader("android_tool", str(TOOLS_ANDROID))
        spec = importlib.util.spec_from_loader("android_tool", loader)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        cls.module = module

    def test_parse_bounds(self):
        self.assertEqual(
            self.module.parse_bounds("[10,20][110,220]"),
            {"x": 10, "y": 20, "width": 100, "height": 200},
        )

    def test_parse_bounds_rejects_non_positive_dimensions(self):
        self.assertIsNone(self.module.parse_bounds("[10,20][10,220]"))
        self.assertIsNone(self.module.parse_bounds("[10,20][110,20]"))

    def test_extract_xml_strips_trailing_status_line(self):
        output = SAMPLE_UI_XML.strip() + "UI hierchary dumped to: /dev/tty\n"
        xml = self.module.extract_xml(output)
        self.assertTrue(xml.endswith("</hierarchy>"))
        elements = self.module.parse_ui_xml(xml)
        self.assertEqual(len(elements), 2)

    def test_extract_xml_handles_status_lines_on_both_sides(self):
        output = (
            "UI hierchary dumped to: /dev/tty\n"
            + SAMPLE_UI_XML.strip()
            + "UI hierchary dumped to: /dev/tty\n"
        )
        xml = self.module.extract_xml(output)
        self.assertTrue(xml.startswith("<?xml"))
        self.assertTrue(xml.endswith("</hierarchy>"))

    def test_connection_type_classification(self):
        self.assertEqual(self.module.connection_type("R3CN30ABCDE"), "usb")
        self.assertEqual(self.module.connection_type("192.168.1.42:5555"), "tcp")
        self.assertEqual(self.module.connection_type("adb-R3CN30ABCDE-abcdef._adb-tls-connect._tcp"), "tcp")
        self.assertEqual(self.module.connection_type("emulator-5554"), "emulator")

    def test_is_ip_address(self):
        self.assertTrue(self.module.is_ip_address("100.101.102.103"))
        self.assertFalse(self.module.is_ip_address("my-phone"))
        self.assertFalse(self.module.is_ip_address("192.168.1.42:5555"))

    def test_parse_wifi_ip_from_route(self):
        route = "192.168.1.0/24 dev wlan0 proto kernel scope link src 192.168.1.42\n"
        self.assertEqual(self.module.parse_wifi_ip(route), "192.168.1.42")

    def test_parse_wifi_ip_falls_back_to_addr_output(self):
        addr = "    inet 10.0.0.7/24 brd 10.0.0.255 scope global wlan0\n"
        self.assertEqual(self.module.parse_wifi_ip("", addr), "10.0.0.7")

    def test_parse_wifi_ip_returns_none_without_wifi(self):
        self.assertIsNone(self.module.parse_wifi_ip("", ""))

    def test_find_elements_prefers_smaller_element_on_score_tie(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="" resource-id="com.example:id/navigation_item_layout" class="android.view.ViewGroup" content-desc="Alarm" clickable="true" enabled="true" focused="false" checked="false" scrollable="false" bounds="[58,320][761,425]" />
  <node index="0" text="" resource-id="com.example:id/icon_container" class="android.view.ViewGroup" content-desc="Alarm" clickable="true" enabled="true" focused="false" checked="false" scrollable="false" bounds="[58,320][174,425]" />
</hierarchy>
"""
        elements = self.module.parse_ui_xml(xml)
        matches = self.module.find_elements(elements, "content-desc", "Alarm")
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]["resourceId"], "com.example:id/icon_container")

    def test_find_elements_by_any_matches_content_desc_only(self):
        elements = self.module.parse_ui_xml(SAMPLE_UI_XML)
        matches = self.module.find_elements(elements, "any", "Navigate up")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["contentDesc"], "Navigate up")

    def test_find_elements_by_any_ranks_exact_text_match_first(self):
        elements = self.module.parse_ui_xml(SAMPLE_UI_XML)
        matches = self.module.find_elements(elements, "any", "Login")
        self.assertEqual(matches[0]["text"], "Login")

    def test_extract_png_strips_leading_warning(self):
        png = b"\x89PNG\r\n\x1a\n" + b"rest-of-png"
        data = self.module.extract_png(b"[Warning] Multiple displays were found\n" + png)
        self.assertEqual(data, png)

    def test_extract_png_returns_none_without_signature(self):
        self.assertIsNone(self.module.extract_png(b"error: device offline"))

    def test_escape_input_text_escapes_shell_metacharacters(self):
        self.assertEqual(self.module.escape_input_text("a b"), "a%sb")
        self.assertEqual(
            self.module.escape_input_text("*?~#[]{}"),
            "\\*\\?\\~\\#\\[\\]\\{\\}",
        )

    def test_validate_input_text_accepts_plain_ascii(self):
        self.module.validate_input_text("Hello World! 100% sure.")

    def test_validate_input_text_rejects_literal_percent_s(self):
        with self.assertRaises(self.module.ToolError):
            self.module.validate_input_text("discount: 10%s off")

    def test_validate_input_text_rejects_non_ascii(self):
        with self.assertRaises(self.module.ToolError):
            self.module.validate_input_text("héllo")

    def test_parse_ui_xml_filters_relevant_nodes(self):
        elements = self.module.parse_ui_xml(SAMPLE_UI_XML)
        self.assertEqual(len(elements), 2)
        self.assertEqual(elements[0]["text"], "Login")
        self.assertTrue(elements[1]["clickable"])

    def test_get_ui_xml_retries_until_xml_is_available(self):
        responses = iter(
            [
                subprocess.CompletedProcess(args=[], returncode=137, stdout="", stderr="Killed"),
                subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="dump failed"),
                subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr=""),
                subprocess.CompletedProcess(args=[], returncode=0, stdout="UI hierchary dumped to: /dev/tty\n" + SAMPLE_UI_XML, stderr=""),
            ]
        )

        with mock.patch.object(self.module, "adb_result", side_effect=lambda *args, **kwargs: next(responses)):
            with mock.patch.object(self.module.time, "sleep"):
                xml = self.module.get_ui_xml("emulator-5554")

        self.assertIn("<hierarchy", xml)

    def test_select_started_device_prefers_new_device(self):
        current_devices = [
            {"id": "emulator-5554", "state": "device"},
            {"id": "emulator-5556", "state": "device"},
        ]
        self.assertEqual(
            self.module.select_started_device(current_devices, {"emulator-5554"}),
            "emulator-5556",
        )

    def test_select_started_device_ignores_existing_ready_devices(self):
        current_devices = [{"id": "emulator-5554", "state": "device"}]
        self.assertIsNone(self.module.select_started_device(current_devices, {"emulator-5554"}))

    def test_select_started_device_requires_explicit_choice_for_multiple_new_devices(self):
        current_devices = [
            {"id": "emulator-5554", "state": "device"},
            {"id": "emulator-5556", "state": "device"},
        ]
        with self.assertRaises(self.module.ToolError):
            self.module.select_started_device(current_devices, set())


if __name__ == "__main__":
    unittest.main(verbosity=2)
