# -*- coding: utf-8 -*-
import requests
import json

# URL del servidor JSON-RPC
url = "http://localhost:5000/jsonrpc"

# Peticion en formato JSON-RPC (puedes cambiar el metodo)
#payload = {
#    "jsonrpc": "2.0",
#   "method": "insertar_usuario",
#   "params": ["Luis", 25],
#   "id": 12
#}

payload = {
    "jsonrpc": "2.0",
    "method": "sumar",
    "params": [10, 20, 5],
    "id": 2
}
# Enviar solicitud POST
response = requests.post(url, json=payload)

# Mostrar resultado
print("Respuesta del servidor:", response.json())

