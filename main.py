# Tienda-Magika_Back/main.py (CORREGIDO)

import connexion
from pathlib import Path

# La aplicación correrá en el puerto 3000 para que el Frontend (ej. 5173) se conecte
API_PORT = 3000

# Inicializa la aplicación Connexion. 
# Le decimos que busque la implementación de la API en el archivo openapi.yml
app = connexion.FlaskApp(__name__, specification_dir=Path("./swagger"))

# Añade la API a partir de la especificación, y mapea las operaciones a las funciones en controllers.py
app.add_api("openapi.yml", 
            base_path="/api/v1",
            # 🌟 CORRECCIÓN: Se añade 'name' para evitar el conflicto de ValueError: The name '/api/v1' is already registered...
            arguments={"title": "Tienda Magika API", "name": "v1_api_blueprint"},
            pythonic_params=True)

if __name__ == "__main__":
    print(f"Backend API corriendo en http://localhost:{API_PORT}/api/v1/ui")
    # Argumento 'debug=True' eliminado. Connexion usa uvicorn y no lo requiere/acepta.
    app.run(port=API_PORT)