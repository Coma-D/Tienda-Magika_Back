# Tienda-Magika_Back/data.py (CORREGIDO)
import json
import os
import copy
# Se eliminó la importación de 'time' que solo se usa en controllers.py

# ==============================================================
# DATOS GLOBALES Y BASES DE DATOS EN MEMORIA (In-Memory DBs)
# ==============================================================

GLOBAL_IMAGE = '/sp_res5myxp7z.jpg' 

# --- Persistencia para el Catálogo ---
# Define la ruta para el archivo de persistencia
# Se utiliza 'os.path.join' para compatibilidad con Windows/Linux
CATALOG_FILE = os.path.join(os.path.dirname(__file__), 'catalog_db.json')

# --- MOCK_CARDS (Datos Iniciales si no existe el archivo de persistencia) ---
_INITIAL_MOCK_CARDS = [
  {"id": '1', "name": 'Lightning Bolt', "image": GLOBAL_IMAGE, "rarity": 'Common', "color": 'Red', "type": 'Spell', "set": 'Colección Básica 2024', "description": 'Hace 3 puntos de daño a cualquier objetivo.', "price": 5990, "manaCoat": 1},
  {"id": '2', "name": 'Black Lotus', "image": GLOBAL_IMAGE, "rarity": 'Legendary', "color": 'Colorless', "type": 'Artifact', "set": 'Alpha', "description": 'Agrega tres maná de cualquier un color a tu reserva de maná.', "price": 250000000000000, "manaCoat": 0},
  {"id": '3', "name": 'Serra Angel', "image": GLOBAL_IMAGE, "rarity": 'Rare', "color": 'White', "type": 'Creature', "set": 'Colección Básica 2024', "description": 'Vuela, vigilancia.', "price": 12990, "manaCoat": 5},
  {"id": '4', "name": 'Counterspell', "image": GLOBAL_IMAGE, "rarity": 'Uncommon', "color": 'Blue', "type": 'Land', "set": 'Legends', "description": 'Contrarresta el hechizo objetivo.', "price": 8500, "manaCoat": 2},
  {"id": '5', "name": 'Giant Growth', "image": GLOBAL_IMAGE, "rarity": 'Common', "color": 'Green', "type": 'Creature', "set": 'Colección Básica 2024', "description": 'La criatura objetivo obtiene +3/+3 hasta el final del turno.', "price": 2000, "manaCoat": 1},
]

MOCK_CARDS = [] # Se inicializa vacía, será poblada por _load_catalog

def _save_catalog():
    """Guarda el estado actual de MOCK_CARDS en un archivo JSON."""
    global MOCK_CARDS
    try:
        with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(MOCK_CARDS, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"ERROR: No se pudo guardar el catálogo en {CATALOG_FILE}. {e}")
        return False

def _load_catalog():
    """Carga el catálogo desde el archivo o usa los datos iniciales y guarda."""
    global MOCK_CARDS
    if os.path.exists(CATALOG_FILE):
        try:
            with open(CATALOG_FILE, 'r', encoding='utf-8') as f:
                MOCK_CARDS = json.load(f)
            return
        except (json.JSONDecodeError, IOError) as e:
            # En caso de archivo corrupto o error de lectura, usar datos iniciales
            print(f"WARNING: Error al cargar catalog_db.json: {e}. Usando datos iniciales.")
            
    # Si el archivo no existe o falla la carga, usar datos iniciales y guardar
    MOCK_CARDS = copy.deepcopy(_INITIAL_MOCK_CARDS)
    # Crea el directorio si es necesario antes de guardar
    os.makedirs(os.path.dirname(CATALOG_FILE) or '.', exist_ok=True)
    _save_catalog()

# 🌟 Llama a la función de carga al iniciar el módulo para inicializar MOCK_CARDS
_load_catalog()

# --- USUARIOS (USERS_DB) ---
# Solo mantenemos al Administrador.
USERS_DB = [
    {
        "id": "1", "name": "Administrador", "username": "admin", 
        "email": "admin@tiendamagika.com", "password": "admin", "avatar": "", "isOnline": True
    }
]

# --- MARKETPLACE LISTINGS (MARKETPLACE_LISTINGS_DB) ---
MARKETPLACE_LISTINGS_DB = []

# --- COLECCIONES DE USUARIO (USER_COLLECTIONS_DB) ---
USER_COLLECTIONS_DB = {}

# --- PREGUNTAS FRECUENTES (FAQ_DATA) ---
FAQ_DATA = [
  {'question': '¿Cómo puedo comprar cartas?', 'answer': 'Puedes navegar por nuestro catálogo, añadir cartas al carrito y proceder al checkout. Aceptamos tarjetas de crédito y débito.'},
  {'question': '¿Cómo funciona el marketplace?', 'answer': 'En el marketplace puedes comprar cartas de otros usuarios o vender las tuyas. Solo necesitas publicar tu carta con un precio y esperar compradores.'},
  {'question': '¿Puedo rastrear mis pedidos?', 'answer': 'Sí, recibirás un email de confirmación con información de seguimiento una vez que tu pedido sea procesado.'},
  {'question': '¿Hay garantía en las cartas?', 'answer': 'Todas nuestras cartas vienen con garantía de autenticidad. Si recibes una carta dañada, puedes solicitar un reembolso.'}
]

# --- REGISTRO DE TICKETS (TICKETS_DB) ---
TICKETS_DB = [] 

# --- REGISTRO DE NOTIFICACIONES (NOTIFICATIONS_DB) ---
NOTIFICATIONS_DB = {} 

# --- CARRITOS DE USUARIO (CARTS_DB) ---
CARTS_DB = {}

# ==============================================================
# --- BASES DE DATOS DE COMUNIDAD ---
# ==============================================================

CHAT_MESSAGES_DB = [] 
BANNED_USERS_DB = {}
USER_BLOCKS_DB = {}