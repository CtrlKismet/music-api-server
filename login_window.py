#!/usr/bin/env python3
"""
QQ Music login window — opens y.qq.com in a Qt WebEngine view,
automatically captures cookies after successful login.

Usage: python login_window.py [--output /path/to/config.py]
If --output is specified, writes cookies directly to the config file.
Otherwise prints the cookie dict as JSON to stdout.

Requires: PyQt6 PyQt6-WebEngine
"""

import json
import re
import sys
import argparse
from pathlib import Path

from PyQt6.QtCore import QUrl, pyqtSignal, QObject
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineCore import QWebEngineProfile
from PyQt6.QtWebEngineWidgets import QWebEngineView


LOGIN_URL = "https://y.qq.com"

# Cookie domains to capture
COOKIE_DOMAINS = ["qq.com", "y.qq.com"]

# Essential cookie names for QQ Music
REQUIRED_COOKIE_SETS = [
    ["qqmusic_key", "wxuin", "qm_keyst"],
    ["qqmusic_key", "uin", "qm_keyst"],
]


class LoginWindow(QMainWindow):
    login_succeed = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QQ Music Login — Antares")
        self.resize(1200, 800)

        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            (screen.height() - self.height()) // 2,
        )

        self.saved_cookies = {}

        # Set up the web engine profile with cookie monitoring
        profile = QWebEngineProfile.defaultProfile()
        cookie_store = profile.cookieStore()
        cookie_store.deleteAllCookies()
        cookie_store.cookieAdded.connect(self._on_cookie_added)

        self.webview = QWebEngineView()
        self.webview.load(QUrl(LOGIN_URL))

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.webview)
        self.setCentralWidget(central)

        self.login_succeed.connect(self._on_login_succeed)

    def _on_cookie_added(self, cookie):
        domain = cookie.domain()
        if not any(d in domain for d in COOKIE_DOMAINS):
            return

        name = cookie.name().data().decode()
        value = cookie.value().data().decode()
        self.saved_cookies[name] = value

        # Check if all required cookies are present
        for required_set in REQUIRED_COOKIE_SETS:
            if all(name in self.saved_cookies for name in required_set):
                self.login_succeed.emit(self.saved_cookies.copy())
                return

    def _on_login_succeed(self, cookies):
        self.cookies = cookies
        self.close()


def write_config(config_path, cookies):
    """Write cookies into the QQ_USER_CONFIG section of config.py."""
    content = Path(config_path).read_text()

    uin = cookies.get("uin", "")
    qqmusic_key = cookies.get("qqmusic_key", "")
    qm_keyst = cookies.get("qm_keyst", qqmusic_key)
    refresh_token = cookies.get("refresh_token", cookies.get("psrf_qqrefresh_token", ""))

    # Replace the QQ_USER_CONFIG block
    pattern = r'QQ_USER_CONFIG\s*=\s*\{[^}]*\}'
    replacement = (
        'QQ_USER_CONFIG = {\n'
        f'        "uin": "{uin}",\n'
        f'        "qqmusic_key": "{qqmusic_key}",\n'
        f'        "qm_keyst": "{qm_keyst}",\n'
        f'        "refresh_token": "{refresh_token}",\n'
        '    }'
    )
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    Path(config_path).write_text(new_content)
    print(f"Cookies written to {config_path}")


def main():
    parser = argparse.ArgumentParser(description="QQ Music Login Window")
    parser.add_argument("--output", help="Path to config.py to update with captured cookies")
    parser.add_argument("--json", action="store_true", help="Output cookies as JSON to stdout")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Antares-Login")

    window = LoginWindow()
    window.show()

    app.exec()

    cookies = getattr(window, "cookies", {})
    if not cookies:
        print("Login cancelled or no cookies captured", file=sys.stderr)
        sys.exit(1)

    if args.output:
        write_config(args.output, cookies)
    elif args.json:
        print(json.dumps(cookies, indent=2))
    else:
        print(json.dumps(cookies, indent=2))

    print("Login successful!", file=sys.stderr)


if __name__ == "__main__":
    main()
