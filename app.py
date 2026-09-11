import logging

from bottle import Bottle, request

from server.api_handlers import format_gap, register_routes
from server.autosave import AUTOSAVE_PATH, load_state, save_state
from server.network import get_local_ips, print_qr
from server.race_state import RaceState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("app")

app = Bottle()
STATE = RaceState()

gap = load_state(STATE, AUTOSAVE_PATH)
if gap is not None:
    suffix = f" (resumed after {format_gap(gap)})" if gap > 0 else ""
    log.info("restored race state from %s%s", AUTOSAVE_PATH, suffix)

STATE.on_change = lambda: save_state(STATE, AUTOSAVE_PATH)


@app.hook("after_request")
def log_request():
    log.info("%s %s", request.method, request.path)


register_routes(app, STATE)


def main():
    import os
    import threading
    import time
    import urllib.request
    import webbrowser
    from waitress import serve

    port = 8095
    ips = get_local_ips()
    log.info("Server started on port %d -- share one of these addresses:", port)
    for ip in ips:
        log.info("  http://%s:%d", ip, port)
        print_qr(f"http://{ip}:{port}")
    if not ips:
        log.info("  http://localhost:%d  (no network interface detected)", port)
        print_qr(f"http://localhost:{port}")
    log.info("  http://localhost:%d  (for local)", port)
    print_qr(f"http://localhost:{port}")

    if os.environ.get("RACE_LAP_LAUNCHER") == "1":
        # only auto-open when started via a launcher script, never on a plain `uv run app.py`
        # (that would also fire on every hupper dev-reload)
        def open_browser_when_ready():
            url = f"http://localhost:{port}"
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    urllib.request.urlopen(url, timeout=0.5)
                    break
                except OSError:
                    time.sleep(0.2)
            webbrowser.open(url)

        threading.Thread(target=open_browser_when_ready, daemon=True).start()

    serve(app, host="0.0.0.0", port=port, threads=8)


if __name__ == "__main__":
    import hupper
    hupper.start_reloader("app.main")
