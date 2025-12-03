# Tienda-Magika_Back/src/controllers.py (FINAL CORREGIDO)

import time
import uuid
import copy 
from datetime import datetime
# Imports de datos centralizados
from data import (
    USERS_DB, MOCK_CARDS, MARKETPLACE_LISTINGS_DB, 
    USER_COLLECTIONS_DB, FAQ_DATA, TICKETS_DB, NOTIFICATIONS_DB,
    CARTS_DB, 
    CHAT_MESSAGES_DB, BANNED_USERS_DB, USER_BLOCKS_DB, 
    # 🌟 Importaciones necesarias para persistencia y helpers
    _save_catalog, GLOBAL_IMAGE 
) 

# ==============================================================
# HELPERS PRIVADOS & UTILIDADES
# ==============================================================

def _check_admin_auth(admin_id):
    """Verifica si el ID proporcionado corresponde al administrador."""
    return admin_id == '1'

def _cleanup_user_data(user_id):
    """Elimina todos los rastros de un usuario en todas las bases de datos."""
    # 1. Bases de datos directas
    for db in [USER_COLLECTIONS_DB, CARTS_DB, NOTIFICATIONS_DB, BANNED_USERS_DB, USER_BLOCKS_DB]:
        if user_id in db:
            del db[user_id]
            
    # 2. Limpiar referencias en listas de bloqueos de otros
    for blocker_id in list(USER_BLOCKS_DB.keys()):
        if user_id in USER_BLOCKS_DB[blocker_id]:
            USER_BLOCKS_DB[blocker_id].remove(user_id)

    # 3. Limpiar Tickets
    global TICKETS_DB
    TICKETS_DB = [t for t in TICKETS_DB if t.get('user_id') != user_id]
    
    # 4. Limpiar Mensajes de Chat
    global CHAT_MESSAGES_DB
    CHAT_MESSAGES_DB = [
        msg for msg in CHAT_MESSAGES_DB
        if msg['sender']['id'] != user_id and (not msg.get('recipient') or msg['recipient']['id'] != user_id)
    ]

    # 5. Limpiar Listings del Marketplace
    global MARKETPLACE_LISTINGS_DB
    MARKETPLACE_LISTINGS_DB = [
        listing for listing in MARKETPLACE_LISTINGS_DB 
        if listing['seller']['id'] != user_id
    ]

def get_user_by_id(user_id):
    return next((user for user in USERS_DB if user['id'] == user_id), None)

def add_system_notification(user_id: str, message: str, type: str = "info", read: bool = False):
    if user_id not in NOTIFICATIONS_DB:
        NOTIFICATIONS_DB[user_id] = []
    new_notification = {
        "id": str(uuid.uuid4()), "userId": user_id, "message": message, "type": type,
        "date": datetime.now().strftime('%d/%m/%Y %H:%M'), "read": read
    }
    NOTIFICATIONS_DB[user_id].insert(0, new_notification)
    return new_notification

def _get_next_card_id():
    """Genera un nuevo ID numérico único basado en el ID numérico más alto actual."""
    max_id = 0
    for card in MOCK_CARDS:
        try:
            # Convertir el ID a entero para encontrar el máximo
            current_id = int(card.get('id', '0'))
            max_id = max(max_id, current_id)
        except ValueError:
            # Ignorar IDs no numéricos
            pass
    return str(max_id + 1)

# ==============================================================
# CONTROLADORES DE USUARIOS
# ==============================================================

def register_user(body):
    username, email = body.get('username'), body.get('email')
    if any(u['username'].lower() == username.lower() or u['email'].lower() == email.lower() for u in USERS_DB):
        return {"error": "Usuario o email ya existe"}, 409
        
    # Usar el tiempo en milisegundos como ID
    new_user_id = str(int(time.time() * 1000))
    
    # Limpieza preventiva usando el helper (Asegura que no haya datos residuales)
    _cleanup_user_data(new_user_id)
    
    new_user = {
        "id": new_user_id, "name": body.get('name'), "username": username,
        "email": email, "password": body.get('password'), "avatar": "", "isOnline": True
    }
    USERS_DB.append(new_user)
    
    # Inicializar DBs vacías
    USER_COLLECTIONS_DB[new_user_id] = []
    CARTS_DB[new_user_id] = []
    NOTIFICATIONS_DB[new_user_id] = []
    
    return {"message": "Registro exitoso", "user": new_user}, 201

def login_user(body):
    email_or_username = body.get('emailOrUsername')
    password = body.get('password')
    found_user = next((u for u in USERS_DB if (u['email'] == email_or_username or u['username'] == email_or_username) and u['password'] == password), None)
    
    if found_user:
        found_user['isOnline'] = True
        # CAMBIO: Retornamos el objeto usuario completo para que el frontend lo use
        return {
            "message": "Login exitoso", 
            "token": "DUMMY_TOKEN", 
            "user": found_user
        }, 200
        
    return {"error": "Credenciales inválidas"}, 401

def change_password(body):
    user = get_user_by_id(body.get('userId'))
    if user and user.get('password') == body.get('currentPassword'):
        user['password'] = body.get('newPassword')
        return {"success": True, "message": "Contraseña actualizada"}, 200
    return {"success": False, "message": "Contraseña actual incorrecta"}, 401
    
def get_all_users():
    return [{k: v for k, v in user.items() if k != 'password'} for user in USERS_DB], 200

def delete_user(user_id, admin_id=None):
    # Permitimos que un usuario se borre a sí mismo si admin_id coincide con user_id,
    # O si el admin real ('1') lo solicita.
    if not _check_admin_auth(admin_id) and admin_id != user_id:
        return {"error": "Acción no autorizada."}, 403

    global USERS_DB
    initial_len = len(USERS_DB)
    USERS_DB = [user for user in USERS_DB if user['id'] != user_id]
    
    if len(USERS_DB) == initial_len:
        return {"error": "Usuario no encontrado"}, 404

    _cleanup_user_data(user_id)
    return {"message": f"Usuario {user_id} eliminado correctamente."}, 200

# ==============================================================
# CONTROLADORES DE COMUNIDAD (BAN & BLOCK)
# ==============================================================

def toggle_block(body):
    blocker_id, target_id = body.get('blockerId'), body.get('targetId')
    if blocker_id not in USER_BLOCKS_DB: USER_BLOCKS_DB[blocker_id] = []
        
    if target_id in USER_BLOCKS_DB[blocker_id]:
        USER_BLOCKS_DB[blocker_id].remove(target_id)
        action = "unblocked"
    else:
        USER_BLOCKS_DB[blocker_id].append(target_id)
        action = "blocked"
    return {"message": f"User {target_id} {action}"}, 200

def toggle_ban(body):
    if not _check_admin_auth(body.get('adminId')):
        return {"error": "Acción no autorizada."}, 403
    
    target_id = body.get('targetId')
    if target_id in BANNED_USERS_DB:
        del BANNED_USERS_DB[target_id]
        action = "unbanned"
    else:
        duration = body.get('durationMinutes')
        ban_until = time.time() * 1000 + (100 * 365 * 24 * 3600 * 1000) if duration == -1 else time.time() * 1000 + (duration * 60 * 1000)
        BANNED_USERS_DB[target_id] = ban_until
        action = "banned"

    return {"message": f"User {target_id} {action}"}, 200

def get_bans_and_blocks(user_id):
    active_bans = {k: v for k, v in BANNED_USERS_DB.items() if v > time.time() * 1000}
    return {"bannedUsers": active_bans, "blocks": USER_BLOCKS_DB.get(user_id, [])}, 200

# ==============================================================
# CONTROLADORES DE CHAT
# ==============================================================

def get_all_messages(user_id):
    messages = [msg for msg in CHAT_MESSAGES_DB if not msg.get('isPrivate') or (msg.get('isPrivate') and (msg['sender']['id'] == user_id or msg['recipient']['id'] == user_id))]
    return messages, 200

def send_message(body):
    sender_id = body.get('sender', {}).get('id')
    recipient_id = body.get('recipient', {}).get('id')
    
    if sender_id in BANNED_USERS_DB and BANNED_USERS_DB[sender_id] > time.time() * 1000:
        return {"error": "Usuario baneado"}, 403
    if recipient_id and sender_id in USER_BLOCKS_DB.get(recipient_id, []):
         return {"error": "El destinatario te ha bloqueado"}, 403

    new_message = {
        "id": str(uuid.uuid4()), "sender": body['sender'], "message": body['message'],
        "timestamp": datetime.now().isoformat(), "isPrivate": body.get('isPrivate', False),
        "recipient": body.get('recipient'), "read": body.get('read', False) 
    }
    CHAT_MESSAGES_DB.append(new_message)
    return new_message, 201

# ==============================================================
# CONTROLADORES DE CARRITO Y CHECKOUT
# ==============================================================

def get_user_cart(user_id):
    return CARTS_DB.get(user_id, []), 200

def add_item_to_cart(body):
    user_id, card = body.get('userId'), body.get('card')
    if not user_id: return {"error": "User ID required"}, 400
    if user_id not in CARTS_DB: CARTS_DB[user_id] = []
        
    cart = CARTS_DB[user_id]
    existing = next((i for i in cart if i['card']['id'] == card['id'] and i['source'] == body.get('source', 'catalog')), None)
    if existing: existing['quantity'] += body.get('quantity', 1)
    else: cart.append({"card": card, "quantity": body.get('quantity', 1), "source": body.get('source', 'catalog')})
    return cart, 200

def remove_item_from_cart(body):
    user_id, card_id = body.get('userId'), body.get('cardId')
    if not user_id or not card_id or user_id not in CARTS_DB: return {"error": "Invalid request"}, 400
    
    cart = CARTS_DB[user_id]
    for i, item in enumerate(cart):
        if item['card']['id'] == card_id:
            item['quantity'] += body.get('quantity', -1)
            if item['quantity'] <= 0: del cart[i]
            return cart, 200
    return {"error": "Item not found"}, 404

def complete_checkout(body):
    user_id, items = body.get('userId'), body.get('purchasedItems', [])
    if not user_id or not items: return {"error": "Datos incompletos"}, 400

    if user_id not in USER_COLLECTIONS_DB: USER_COLLECTIONS_DB[user_id] = []
    
    newly_bought_ids = []
    for item in items:
        card, qty, source = item['card'], item['quantity'], item.get('source', 'catalog')
        
        # OBTENER PROPIEDADES ESTABLES PARA LA BÚSQUEDA
        card_name = card.get('name')
        card_set = card.get('set')
        
        # FIX DE DUPLICACIÓN: Usar nombre y set como clave de agrupamiento (más robusto que originalId).
        existing_card = next((
            c for c in USER_COLLECTIONS_DB[user_id] 
            if c.get('name') == card_name and c.get('set') == card_set and c.get('source') == source
        ), None)
        
        if existing_card:
            existing_card['quantity'] = existing_card.get('quantity', 1) + qty
        else:
            # Creamos una nueva CollectionCard si no existe una instancia para la misma carta
            instance = {
                **card,
                'originalId': card.get('id'), # ID del catálogo
                'id': str(uuid.uuid4()),      # Nuevo ID único de instancia
                'source': source,
                'quantity': qty,
                'isFavorite': False,
                'addedAt': datetime.now().isoformat()
            }
            # Aseguramos que los campos numéricos estén presentes
            if 'price' not in instance: instance['price'] = 0
            USER_COLLECTIONS_DB[user_id].append(instance)

        if source == 'marketplace' and item.get('listingId'):
            newly_bought_ids.append(item.get('listingId'))
            
    if newly_bought_ids:
        global MARKETPLACE_LISTINGS_DB
        MARKETPLACE_LISTINGS_DB = [l for l in MARKETPLACE_LISTINGS_DB if l['id'] not in newly_bought_ids]
    
    if user_id in CARTS_DB: CARTS_DB[user_id] = []
    add_system_notification(user_id, "¡Tu compra fue exitosa!", "success")

    return {"message": "Checkout OK", "remainingListings": MARKETPLACE_LISTINGS_DB, "userCollectionCount": len(USER_COLLECTIONS_DB[user_id])}, 200


# ==============================================================
# CONTROLADORES DE COLECCIÓN (MODIFICAR)
# ==============================================================

def add_or_update_collection_card(body):
    user_id = body.get('userId')
    card = body.get('card')
    source = body.get('source', 'catalog')
    quantity_to_add = body.get('quantity', 1)

    if not user_id or not card:
        return {"error": "User ID and card are required"}, 400

    if user_id not in USER_COLLECTIONS_DB:
        USER_COLLECTIONS_DB[user_id] = []

    # OBTENER PROPIEDADES ESTABLES PARA LA BÚSQUEDA
    card_name = card.get('name')
    card_set = card.get('set')
    
    # 🌟 FIX DE DUPLICACIÓN IMPLEMENTADO: Usar nombre y set como clave de agrupamiento.
    existing_card = next((
        c for c in USER_COLLECTIONS_DB[user_id] 
        if c.get('name') == card_name and c.get('set') == card_set and c.get('source') == source
    ), None)

    if existing_card:
        # Si ya existe, incrementamos la cantidad
        existing_card['quantity'] = existing_card.get('quantity', 1) + quantity_to_add
        return {"message": "Card quantity updated successfully", "card": existing_card}, 200
    else:
        # Si no existe, creamos una nueva CollectionCard
        new_card = {
            **card,
            'originalId': card.get('id'), # ID del catálogo (para agrupar si se añade de nuevo)
            'id': str(uuid.uuid4()),      # Nuevo ID único de instancia (CRÍTICO para eliminación/edición individual)
            'source': source,
            'quantity': quantity_to_add,
            'isFavorite': card.get('isFavorite', False), 
            'addedAt': datetime.now().isoformat()
        }
        # Asegurar que los campos numéricos se manejen correctamente si faltan
        if 'price' not in new_card: new_card['price'] = 0
             
        USER_COLLECTIONS_DB[user_id].append(new_card)
        return {"message": "Card added successfully", "card": new_card}, 201

def remove_quantity_from_collection_card(body):
    user_id = body.get('userId')
    card_instance_id = body.get('cardId')
    quantity_to_remove = body.get('quantityToRemove', 1)

    if not user_id or not card_instance_id:
        return {"error": "User ID and card ID are required"}, 400

    if user_id not in USER_COLLECTIONS_DB:
        return {"error": "Collection not found"}, 404

    collection = USER_COLLECTIONS_DB[user_id]
    
    # Buscar el índice de la carta por su ID de instancia (el ID único generado por uuid)
    card_index = next((i for i, c in enumerate(collection) if c.get('id') == card_instance_id), -1)

    if card_index == -1:
        return {"error": "Card instance not found"}, 404
        
    card_to_update = collection[card_index]
    current_quantity = card_to_update.get('quantity', 1)

    if quantity_to_remove >= current_quantity:
        # Si se pide eliminar más o toda la cantidad, eliminar la instancia
        del collection[card_index]
        return {"message": "Card instance removed completely"}, 200
    else:
        # Si se pide eliminar una cantidad parcial, decrementar
        card_to_update['quantity'] -= quantity_to_remove
        return {"message": f"Quantity reduced by {quantity_to_remove}", "card": card_to_update}, 200
        
def update_collection_card_metadata(body):
    user_id = body.get('userId')
    updated_card = body.get('updatedCard')
    
    # updated_card es un CollectionCard que contiene el ID de instancia único
    if not user_id or not updated_card or not updated_card.get('id'):
        return {"error": "User ID and updated card (with ID) are required"}, 400
        
    card_instance_id = updated_card['id']

    if user_id not in USER_COLLECTIONS_DB:
        return {"error": "Collection not found"}, 404

    collection = USER_COLLECTIONS_DB[user_id]
    
    # Buscar el índice de la carta por su ID de instancia
    card_index = next((i for i, c in enumerate(collection) if c.get('id') == card_instance_id), -1)

    if card_index == -1:
        return {"error": "Card instance not found"}, 404

    # Reemplazar el objeto completo (el frontend ya maneja la lógica de actualización)
    collection[card_index] = updated_card
    
    return {"message": "Card metadata updated successfully", "card": updated_card}, 200

def toggle_favorite_card(body):
    user_id = body.get('userId')
    card_instance_id = body.get('cardId') 
    
    if not user_id or not card_instance_id:
        return {"error": "User ID and card ID are required"}, 400

    if user_id not in USER_COLLECTIONS_DB:
        return {"error": "Collection not found"}, 404

    collection = USER_COLLECTIONS_DB[user_id]
    
    card_to_update = next((c for c in collection if c.get('id') == card_instance_id), None)

    if not card_to_update:
        return {"error": "Card instance not found"}, 404

    # Cambiar el estado de favorito
    card_to_update['isFavorite'] = not card_to_update.get('isFavorite', False)
    
    return {"message": "Favorite status toggled successfully", "card": card_to_update}, 200

# ==============================================================
# CONTROLADORES DEL CATÁLOGO
# ==============================================================

def add_card_to_catalog(body):
    """
    Agrega una nueva carta al catálogo de forma persistente.
    """
    # Generación de un ID único y secuencial
    new_card_id = _get_next_card_id()
    
    # Construcción de la nueva carta a partir del cuerpo con valores por defecto
    new_card = {
        "id": new_card_id, 
        "name": body.get('name', f'Card {new_card_id}'), 
        "image": body.get('image', GLOBAL_IMAGE),
        "rarity": body.get('rarity', 'Common'), 
        "color": body.get('color', 'Colorless'), 
        "type": body.get('type', 'Unknown'), 
        "set": body.get('set', 'Custom Set'), 
        "description": body.get('description', 'Nueva carta personalizada.'), 
        "price": body.get('price', 0), # Precio en centavos/moneda menor
        "manaCoat": body.get('manaCoat', 0)
    }

    # Añadir la carta a la lista global en memoria
    MOCK_CARDS.append(new_card)
    
    # 🌟 Persistir el catálogo en el archivo
    _save_catalog() 

    return {"message": "Card added successfully to catalog", "card": new_card}, 201


# ==============================================================
# CONTROLADORES DE DATOS (LEER)
# ==============================================================

def get_user_collection(user_id):
    # Aseguramos que si no hay colección, devolvemos un array vacío, no un error 400 si el user_id es válido
    if user_id in USERS_DB or user_id in USER_COLLECTIONS_DB:
        return USER_COLLECTIONS_DB.get(user_id, []), 200
    return {"error": "ID required or User not found"}, 400

def get_all_cards(): return MOCK_CARDS, 200
def get_all_listings(): return MARKETPLACE_LISTINGS_DB, 200
def get_faq(): return FAQ_DATA, 200
def get_user_notifications(user_id): return NOTIFICATIONS_DB.get(user_id, []), 200

def publish_listing(body):
    new_listing = {
        "id": f"listing_{int(time.time() * 1000)}", "card": body.get("card"),
        "seller": body.get("seller"), "price": body.get("price"),
        "condition": body.get("condition"), "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    MARKETPLACE_LISTINGS_DB.append(new_listing)
    return new_listing, 201

def submit_support_ticket(body):
    TICKETS_DB.append({"id": str(uuid.uuid4()), "created_at": datetime.now().isoformat(), "status": "Pending", **body})
    if body.get('user_id'):
        add_system_notification(body.get('user_id'), f"Ticket recibido: '{body.get('subject')}'", "success")
        add_system_notification('1', f"NUEVO TICKET: {body.get('subject')}", "warning")
    return {"message": "Ticket registrado"}, 201