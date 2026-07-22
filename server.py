from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/operator"):
            self.path = "/static/operator.html"
        elif self.path == "/scoreboard":
            self.path = "/static/scoreboard.html"
        super().do_GET()

    def log_message(self, format, *args):
        print(f"{self.address_string()} {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8094), Handler)
    print("Serving at http://localhost:8094")
    print("Scoreboard: http://localhost:8094/scoreboard")
    print("Press Ctrl+C to stop")
    server.serve_forever()
