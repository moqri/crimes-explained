"""Local preview server for the site root, with caching switched off so the browser always shows the current build.
Usage: python3 serve.py   (serves http://localhost:8000/)"""
import http.server

class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

http.server.ThreadingHTTPServer(("", 8000), NoCache).serve_forever()
