
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

NOMBRE = os.environ["SERVICE_NAME"]
RUTA = os.environ["SERVICE_PATH"]
DATOS = json.loads(os.environ["SERVICE_RESPONSE"])
PUERTO = 3000


class ServicioHTTP(BaseHTTPRequestHandler):
    def do_GET(self):
        ruta_solicitada = self.path.split("?")[0]

        if ruta_solicitada == RUTA:
            codigo = 200
            respuesta = DATOS
        else:
            codigo = 404
            respuesta = {
                "error": "Ruta no encontrada",
                "servicio": NOMBRE
            }

        contenido = json.dumps(
            respuesta, ensure_ascii=False
        ).encode("utf-8")

        self.send_response(codigo)
        self.send_header(
            "Content-Type", "application/json"
        )
        self.send_header("X-Servicio", NOMBRE)
        self.send_header(
            "Content-Length", str(len(contenido))
        )
        self.end_headers()
        self.wfile.write(contenido)


print(f"Iniciando {NOMBRE} en puerto {PUERTO}", flush=True)

servidor = ThreadingHTTPServer(
    ("0.0.0.0", PUERTO), ServicioHTTP
)

servidor.serve_forever()
