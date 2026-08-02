<p align="center">
  <img src="assets/logo.png" alt="Android ADB Control" width="240">
</p>

<h1 align="center">Android ADB Skill</h1>

<p align="center">
  <b>Control real Android phones and emulators from AI coding agents.</b><br>
  Skill-driven orchestration over a deterministic, tested command layer — no MCP server required.
</p>

<p align="center">
  <a href="https://github.com/Freespirits/android-control-skill/actions/workflows/test.yml">
    <img src="https://github.com/Freespirits/android-control-skill/actions/workflows/test.yml/badge.svg" alt="Test">
  </a>
</p>

<p align="center">
  🎬 <a href="assets/demo.mp4"><b>Watch the demo video</b></a>
</p>

---

## What is this?

Two thin layers that turn any coding agent into an Android operator:

- **`./tools/android`** — a single Python executable that wraps `adb` with a stable,
  JSON-first command surface: screenshots, UI inspection, element targeting, gestures,
  waits, app lifecycle, logs, and network connectivity.
- **`skills/*/SKILL.md`** — short task workflows that tell the agent how to compose
  those commands (navigate, test, debug, install, connect, …).

The agent stays high-level; the runtime contract stays deterministic and testable.

## Highlights

- **`--json` everywhere** — agents reason over structured output, never scraped prose.
- **Semantic targeting** — find, tap, wait, and scroll by `resource-id`, `text`,
  `content-desc`, or `any`; smart ranking prefers the real control over clipped
  layout containers.
- **Wi-Fi & Tailscale control** — `connect wifi` flips a USB phone to network adb in
  one command; `connect tailscale` reaches it from anywhere on your tailnet.
- **Battle-tested on real hardware** — verified on a Galaxy Z Fold6 (Android 16):
  multi-display screenshot quirks, slow UI dumps, icon-only navigation rails, and
  Samsung's uiautomator output format are all handled.
- **Cross-platform** — Linux, macOS, and Windows (`tools\android.cmd` shim, SDK
  discovery under `%LOCALAPPDATA%`, `.exe`/`.bat` resolution).
- **CI-backed** — the whole command layer is tested against fake `adb`/`emulator`
  binaries; no device needed on the runner.

## Why not an MCP server?

The useful part of device automation is the *command design*, not the transport.
A local CLI is testable, versioned with the repo, composable with ordinary shell
logic, and needs no server lifecycle. Agents with shell access (Claude Code, Codex,
Cursor, Copilot) get everything MCP would offer — and if you ever need MCP (shell-less
clients, persistent sessions), wrapping this CLI in one is trivial.

## Prerequisites

- Android SDK with `adb` on your PATH, or `ANDROID_HOME` set
- Python 3 (`python3` on POSIX, `python` on Windows)
- A connected Android device or running emulator

```bash
# quick check (POSIX)
./tools/android device list --json
```

```powershell
# quick check (Windows)
tools\android.cmd device list --json
```

SDK discovery checks `ANDROID_HOME`/`ANDROID_SDK_ROOT`, then the default install
locations on macOS (`~/Library/Android/sdk`), Linux (`~/Android/Sdk`), and Windows
(`%LOCALAPPDATA%\Android\Sdk`).

## Command tour

```bash
# Devices & connectivity
./tools/android device list --json
./tools/android connect wifi --json                    # USB → network adb in one step
./tools/android connect tailscale --host my-phone --json
./tools/android connect pair --host 192.168.1.42 --port 37123 --code 123456

# See the screen
./tools/android screenshot --out screen.png --json
./tools/android ui dump --json
./tools/android ui find --by any --value "Login" --json

# Interact
./tools/android input tap-element --by any --value "Login" --json
./tools/android input text --text "user@example.com" --json
./tools/android input swipe --x1 540 --y1 1800 --x2 540 --y2 600
./tools/android input long-press --x 540 --y 1600 --json
./tools/android wait element --by any --value "Home" --timeout 10000 --json
./tools/android scroll find --by text --value "Privacy" --json

# Apps & debugging
./tools/android app install --apk ./app-debug.apk --json
./tools/android app launch --package com.example.app --json
./tools/android app clear --package com.example.app --json   # clean-state repro
./tools/android debug logs --package com.example.app --level E --json
```

Full contract: [`docs/command-contract.md`](docs/command-contract.md)

## Installation

Copy the core folders into your project:

```bash
cp -r docs skills tools /path/to/project/
```

Then add the adapter file for your agent:

| Agent | Adapter |
|---|---|
| Claude Code | `CLAUDE.md` |
| Codex | `AGENTS.md` |
| Cursor | `.cursor/rules/android-adb.mdc` |
| GitHub Copilot | `.github/copilot-instructions.md` |

## Skills

| Skill | Purpose |
|---|---|
| `android` | General orchestration |
| `android-connect` | Connect over Wi-Fi debugging or Tailscale |
| `android-screenshot` | Capture and inspect screenshots |
| `android-ui` | Dump and search the UI tree |
| `android-tap` | Tap elements or coordinates |
| `android-navigate` | Multi-step navigation with verification |
| `android-scroll` | Scroll to find off-screen elements |
| `android-gesture` | Swipe, long press, double tap |
| `android-test` | Run a test flow with evidence |
| `android-debug` | Collect logs and diagnose failures |
| `android-install` | Install and launch an APK |
| `android-device` | Device and emulator management |

Example usage:

```text
/android open Settings and navigate to Privacy
/android-connect connect to my phone over tailscale
/android-test login with user@example.com and verify the home screen
/android-debug crashes in com.example.app after tapping Settings
```

## Development workflow

To use this repo as part of an AI-driven Android feature/debug loop — edit, build,
install, navigate, verify, iterate — see
[`docs/ai-development-workflow.md`](docs/ai-development-workflow.md).

## Testing

```bash
python3 -m unittest discover -s tests -v
```

CI runs the suite on every push via
[`.github/workflows/test.yml`](.github/workflows/test.yml). Tests use fake
`adb`/`emulator` binaries, so no SDK or device is required. The fakes are POSIX
shebang scripts, so on Windows the integration tests skip automatically and only
the unit tests run; CI covers the full suite.

## Repo structure

```text
android-control-skill/
├── tools/
│   ├── android              # the command layer (single-file Python CLI)
│   └── android.cmd          # Windows shim
├── docs/
│   ├── command-contract.md
│   └── ai-development-workflow.md
├── tests/
│   └── test_tools_android.py
├── skills/                  # android-* agent skills
├── assets/                  # logo & demo video
├── AGENTS.md · CLAUDE.md · .cursor/ · .github/
└── README.md
```

## Credits

- Original project by **[Amit Nayar](https://github.com/amit-nayar)** —
  [amit-nayar/android-adb-skill](https://github.com/amit-nayar/android-adb-skill).
  This fork builds on his command-layer design with Windows support, real-device
  fixes, gesture/app-lifecycle commands, and Wi-Fi/Tailscale connectivity.

## License

MIT
