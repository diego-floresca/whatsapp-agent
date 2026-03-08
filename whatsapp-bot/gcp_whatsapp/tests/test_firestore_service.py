import pytest
import sys
import os

# --- (Tu bloque de sys.path hack si lo estás usando) ---
# ...

# Importamos las funciones a probar
from gcp_whatsapp.services.firestore_service import get_or_create_user, add_message, get_chat_history

# Constantes para la prueba
PHONE = "527221215525"

# ✅ ESTO ES LO QUE BUSCA PYTEST: Una función que empieza con 'test_'
def test_firestore_integration_flow():
    """
    Prueba de integración: Crea usuario -> Guarda mensaje -> Lee historial
    """
    print(f"\n🧪 Iniciando test para: {PHONE}")

    # 1. Probar creación de usuario
    # No hay assert aquí porque tu función no retorna nada, pero si falla lanzaría excepción
    get_or_create_user(PHONE, "Pytest User")
    
    # 2. Probar guardar mensajes
    add_message(PHONE, "user", "Mensaje de prueba Pytest 1")
    add_message(PHONE, "ai", "Respuesta de prueba Pytest 1")
    
    # 3. Probar recuperar historial
    history = get_chat_history(PHONE, limit=5)
    
    # --- ASSERTS (Verificaciones) ---
    # Esto es lo que define si el test pasa o falla
    assert isinstance(history, list), "El historial debería ser una lista"
    assert len(history) > 0, "El historial no debería estar vacío"
    
    # Verificamos que el último mensaje tenga la estructura correcta
    last_msg = history[-1]
    assert "role" in last_msg
    assert "content" in last_msg
    
    print("✅ Test finalizado exitosamente")

