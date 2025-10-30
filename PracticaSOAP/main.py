from fastapi import FastAPI, Request, Response
from fastapi.responses import Response as FastAPIResponse
import json
from pathlib import Path
from typing import List
from pydantic import BaseModel

# Creamos nuestra aplicación con FastAPI
app = FastAPI()

# Definimos el modelo de datos "User" usando Pydantic.
# Este modelo servirá como estructura base para validar y manipular los datos de los usuarios.
class User(BaseModel):
    id: int
    name: str
    email: str
    age: int

# Guardamos el nombre del archivo de la base de datos en una variable
DATA_FILE = "users.json"

# -------------------------------------------------------
# Funciones auxiliares de manejo de la "base de datos"
# -------------------------------------------------------

def init_db():
    """
    Inicializa el archivo de base de datos si no existe.
    Si el archivo no está presente, se crea uno vacío con una lista vacía de usuarios.
    """
    if not Path(DATA_FILE).exists():
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)

def read_users() -> List[User]:
    """
    Lee los usuarios almacenados en el archivo JSON y los convierte a objetos del modelo User.
    """
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        # Comprensión de listas: crea una lista de objetos User a partir de los diccionarios del JSON.
        return [User(**user) for user in data]

def write_users(users: List[User]):
    """
    Guarda la lista de usuarios (objetos User) en el archivo JSON.
    Convierte cada objeto User a un diccionario antes de almacenarlo.
    """
    with open(DATA_FILE, 'w') as f:
        json.dump([user.dict() for user in users], f, indent=2)

# -------------------------------------------------------
# Funciones auxiliares para manejo de SOAP y XML
# -------------------------------------------------------

def create_soap_response(body_content: str) -> str:
    """
    Crea la estructura XML estándar de una respuesta SOAP, 
    envolviendo el contenido (body_content) dentro de un sobre SOAP.
    """
    return f'''<?xml version="1-0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        {body_content}
    </soap:Body>
</soap:Envelope>'''

def user_to_xml(user: User) -> str:
    """
    Convierte un objeto User a su representación en XML.
    """
    return f"""<User>
    <id>{user.id}</id>
    <name>{user.name}</name>
    <email>{user.email}</email>
    <age>{user.age}</age>
</User>"""

def parse_soap_request(xml_content: str) -> dict:
    """
    Parsea una petición SOAP en formato XML y extrae:
    - El nombre de la operación (por ejemplo: CreateUserRequest → "CreateUser")
    - Los parámetros enviados dentro del cuerpo del XML (id, name, email, age)
    Retorna un diccionario con las claves 'operation' y 'params'.
    """
    import re

    # Busca el nombre de la operación (por ejemplo, "CreateUserRequest", "GetUserRequest", etc.)
    operation = re.search(r'<(\w+)Request', xml_content)
    if not operation:
        return {}

    # Convierte el nombre de la operación a una más simple (de GetUserRequest → GetUser)
    op_name = operation.group(1)
    params = {}

    # A continuación se extraen los parámetros enviados en el XML.
    # Se usan expresiones regulares simples para obtener los valores entre las etiquetas.
    if 'id>' in xml_content:
        id_match = re.search(r'<id>(\d+)</id>', xml_content)
        if id_match:
            params['id'] = int(id_match.group(1)) # Convierte <id>1</id> a solo 1
    
    if 'name>' in xml_content:
        name_match = re.search(r'<name>([^<]+)</name>', xml_content)
        if name_match:
            params['name'] = name_match.group(1) # Convierte <name>Pepe</name> a solo Pepe
    
    if 'email>' in xml_content:
        email_match = re.search(r'<email>([^<]+)</email>', xml_content)
        if email_match:
            params['email'] = email_match.group(1) # Convierte <email>pepe@example.com</email> a solo pepe@example.com
    
    if 'age>' in xml_content:
        age_match = re.search(r'<age>(\d+)</age>', xml_content)
        if age_match:
            params['age'] = int(age_match.group(1))

    return {'operation': op_name, 'params': params} # Convierte <age>20</age> a solo 20

# -------------------------------------------------------
# Eventos y endpoints de la aplicación
# -------------------------------------------------------

@app.on_event('startup')
def startup_event():
    """
    Evento que se ejecuta automáticamente al iniciar el servidor.
    Se asegura de que la base de datos esté inicializada antes de procesar peticiones.
    """
    init_db()

@app.post("/soap")
async def soap_endpoint(request: Request):
    """
    Endpoint principal que maneja las peticiones SOAP.
    Recibe el XML, lo interpreta y ejecuta la operación correspondiente.
    """

    # Se obtiene el cuerpo de la petición y se decodifica a texto (UTF-8)
    body = await request.body()
    xml_content = body.decode('utf-8')
    
    # Se interpreta el XML para extraer operación y parámetros
    soap_data = parse_soap_request(xml_content)
    operation = soap_data.get('operation')
    params = soap_data.get('params', {})
    
    # Aquí se determina qué operación ejecutar según el nombre encontrado
    if operation == "GetAllUsers":
        users = read_users()
        users_xml = "\n        ".join([user_to_xml(u) for u in users])
        response_body = f"""<GetAllUsersResponse>
        {users_xml}
    </GetAllUsersResponse>"""
    
    elif operation == "GetUser":
        user_id = params.get('id')
        users = read_users()
        user = next((u for u in users if u.id == user_id), None)
        if user:
            response_body = f"""<GetUserResponse>
        {user_to_xml(user)}
    </GetUserResponse>"""
        else:
            response_body = f"""<GetUserResponse>
        <error>User not found</error>
    </GetUserResponse>"""
    
    elif operation == "CreateUser":
        users = read_users()
        # Asignamos un nuevo ID basado en el mayor ID existente
        new_id = max([u.id for u in users], default=0) + 1
        new_user = User(
            id=new_id,
            name=str(params.get('name')),
            email=params.get('email'),
            age=params.get('age')
        )
        users.append(new_user)
        write_users(users)
        response_body = f"""<CreateUserResponse>
        <success>true</success>
        {user_to_xml(new_user)}
    </CreateUserResponse>"""
    
    elif operation == "UpdateUser":
        user_id = params.get('id')
        users = read_users()
        # Buscamos el usuario a editar
        user_found = False
        for i, user in enumerate(users):
            if user.id == user_id:
                # Actualizamos solo los campos que vienen en los parámetros
                if 'name' in params:
                    users[i].name = params['name']
                if 'email' in params:
                    users[i].email = params['email']
                if 'age' in params:
                    users[i].age = params['age']
                user_found = True
                updated_user = users[i]
                break
        
        if user_found:
            write_users(users)
            response_body = f"""<UpdateUserResponse>
        <success>true</success>
        <message>User updated successfully</message>
        {user_to_xml(updated_user)}
    </UpdateUserResponse>"""
        else:
            response_body = f"""<UpdateUserResponse>
        <success>false</success>
        <error>User not found</error>
    </UpdateUserResponse>"""
    
    elif operation == "DeleteUser":
        user_id = params.get('id')
        users = read_users()
        # Filtra la lista eliminando el usuario con el ID indicado
        users = [u for u in users if u.id != user_id]
        write_users(users)
        response_body = f"""<DeleteUserResponse>
        <success>true</success>
        <message>User deleted successfully</message>
    </DeleteUserResponse>"""
    
    else:
        # Si la operación no se reconoce, se devuelve un mensaje de error en formato SOAP
        response_body = """<Error>
        <message>Unknown operation</message>
    </Error>"""

    # Crea la estructura SOAP completa de respuesta
    soap_response = create_soap_response(response_body)

    # Devuelve la respuesta con el tipo MIME correspondiente a XML
    return FastAPIResponse(
        content=soap_response,
        media_type="text/xml"
    )

@app.get("/")
def root():
    """
    Endpoint raíz que solo sirve como mensaje informativo.
    Indica que el servidor SOAP está en funcionamiento y cómo usarlo.
    """
    return {"message": "SOAP API Server - Utiliza la ruta POST /soap"}