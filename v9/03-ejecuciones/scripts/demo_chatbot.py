"""Chatbot de prueba local con una regresión funcional opcional."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = """<!doctype html><html lang="es"><title>Consulta de trámites</title>
<h1>Estado de un trámite</h1><form><label>Número <input id="tramite" required></label>
<button>Consultar</button></form><p id="respuesta" role="status"></p><small id="fuente"></small>
<script>document.querySelector('form').onsubmit = async event => {
 event.preventDefault();
 const response = await fetch('/consulta', {method:'POST',headers:{'Content-Type':'application/json'},
 body:JSON.stringify({tramite:document.querySelector('input').value})});
 const data = await response.json();
 document.querySelector('#respuesta').textContent=data.respuesta;
 document.querySelector('#fuente').textContent=data.fuente || '';
};</script></html>"""


class Chat(BaseHTTPRequestHandler):
    def send(self, status, data, mime):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.send(200, PAGE.encode(), "text/html; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/consulta":
            return self.send_error(404)
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if payload.get("tramite") == "QA-17":
            state = "cerrado" if self.server.regression else "en revisión"
            data = {
                "estado": state,
                "respuesta": f"Tu trámite está {state}.",
                "fuente": "REG-17",
            }
            status = 200
        else:
            data = {"respuesta": "Podés consultar otro número de trámite."}
            status = 404
        self.send(status, json.dumps(data).encode(), "application/json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=8766, type=int)
    parser.add_argument(
        "--regression",
        action="store_true",
        help="Devolver un estado incorrecto en QA-17",
    )
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Chat) as server:
        server.regression = args.regression
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()
