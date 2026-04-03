"""Entry point for the Hotel Compliance Tracker application."""

import os
import sys

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))

    if getattr(sys, "frozen", False):
        import threading
        import time
        import urllib.request
        import webbrowser

        def _open_browser():
            url = f"http://127.0.0.1:{port}"
            for _ in range(50):
                try:
                    urllib.request.urlopen(url, timeout=1)
                    webbrowser.open(url)
                    return
                except Exception:
                    time.sleep(0.5)

        threading.Thread(target=_open_browser, daemon=True).start()
        app.run(host="127.0.0.1", port=port, debug=False)
    else:
        app.run(debug=True, host="0.0.0.0", port=port)
