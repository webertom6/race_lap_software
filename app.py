import logging

from bottle import Bottle, request

from network import get_local_ips, print_qr
from race_state import RaceState
from api_handlers import register_routes, format_gap
from autosave import AUTOSAVE_PATH, load_state, save_state

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
    serve(app, host="0.0.0.0", port=port, threads=8)


if __name__ == "__main__":
    import hupper
    hupper.start_reloader("app.main")
