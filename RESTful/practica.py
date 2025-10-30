from flask import Flask, Response, request
import xml.etree.ElementTree as ET

app = Flask(__name__)

clientes = [    
    {"id": 1, "nombre": "Juan Pérez", "correo":  "juan@hotmail.com"},
    {"id": 2, "nombre": "María López", "correo": "maria@hotmailcom"},
]

def convertir_a_xml(lista_clientes):
    root = ET.Element("clientes")
    for c in lista_clientes:
        cliente = ET.SubElement(root, "cliente")
        ET.SubElement(cliente, "id").text = str(c["id"])
        ET.SubElement(cliente, "nombre").text = c["nombre"]
        ET.SubElement(cliente, "correo").text = c["correo"]
    return ET.tostring(root, encoding="utf-8")

#metodo para obtener todos los clientes
@app.route("/lista_clientes", methods=["GET"])
def obtener_clientes():
    xml_data = convertir_a_xml(clientes)
    return Response(xml_data, mimetype="application/xml")

#metodo para obtener un cliente por id
@app.route("/cliente/<int:id_cliente>", methods=["GET"])
def obtener_cliente_por_id(id_cliente):
    cliente = next((c for c in clientes if c["id"] == id_cliente), None)
    if cliente:
        xml_data = convertir_a_xml([cliente])
        return Response(xml_data, mimetype="application/xml")
    else:
        return Response("<error>Cliente no encontrado</error>", mimetype="application/xml", status=404)

#metodo para agregar un cliente
@app.route("/agregar_cliente", methods=["POST"])
def agregar_cliente():
    xml = request.data.decode("utf-8")
    root = ET.fromstring(xml)
    nuevo_cliente = {
        "id": len(clientes) + 1,
        "nombre": root.find("nombre").text,
        "correo": root.find("correo").text
    }
    clientes.append(nuevo_cliente)
    return Response("<mensaje>Cliente agregado correctamente</mensaje>", mimetype="application/xml", status=201)

#metodo para actualizar un cliente
@app.route("/actualizar_cliente/<int:id_cliente>", methods=["PUT"])
def actualizar_cliente(id_cliente):
    cliente = next((c for c in clientes if c["id"] == id_cliente), None)
    if not cliente:
        return Response("<error>Cliente no encontrado</error>", mimetype="application/xml", status=404)
    xml = request.data.decode("utf-8")
    root = ET.fromstring(xml)
    cliente["nombre"] = root.find("nombre").text
    cliente["correo"] = root.find("correo").text
    return Response("<mensaje>Cliente actualizado correctamente</mensaje>", mimetype="application/xml", status=200)

#metodo para eliminar un cliente
@app.route("/eliminar_cliente/<int:id_cliente>", methods=["DELETE"])
def eliminar_cliente(id_cliente):
    global clientes
    cliente = next((c for c in clientes if c["id"] == id_cliente), None)
    if not cliente:
        return Response("<error>Cliente no encontrado</error>", mimetype="application/xml", status=404)
    clientes = [c for c in clientes if c["id"] != id_cliente]
    return Response("<mensaje>Cliente eliminado correctamente</mensaje>", mimetype="application/xml", status=200)

if __name__ == "__main__":
    app.run(debug=True)