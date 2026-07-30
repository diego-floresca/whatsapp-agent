# Órdenes mockeadas para demo del challenge Rappi — Caso 1: Soporte WhatsApp
# Cada orden cubre un escenario deliberado de política para mostrar criterio real.
# Fecha de referencia: Julio 2026

MOCK_ORDERS = {
    # Caso 1: No entregada, GPS sin confirmación, monto bajo, sin reembolsos previos → APROBAR
    "RPP-001": {
        "order_id": "RPP-001",
        "usuario_id": "USR-1001",
        "monto": 189.00,
        "fecha": "2026-07-28",
        "estado_entrega": "fallida",
        "confirmacion_gps": False,
        "producto_solicitado": "Tacos de canasta x3 + refresco",
        "producto_entregado": None,
        "reembolsos_ultimos_30_dias": 0,
        "restaurante": "Tacos El Güero",
        "motivo_falla": "repartidor no encontró la dirección",
    },

    # Caso 2: Producto equivocado, monto bajo, sin reembolsos previos → APROBAR
    "RPP-002": {
        "order_id": "RPP-002",
        "usuario_id": "USR-1002",
        "monto": 245.50,
        "fecha": "2026-07-29",
        "estado_entrega": "entregada",
        "confirmacion_gps": True,
        "producto_solicitado": "Hamburguesa doble con papas",
        "producto_entregado": "Hamburguesa sencilla sin papas",
        "reembolsos_ultimos_30_dias": 1,
        "restaurante": "Smash Burgers",
        "motivo_falla": None,
    },

    # Caso 3: Usuario reporta "no entregada" pero GPS confirma entrega → RECHAZAR/ESCALAR (inconsistencia)
    "RPP-003": {
        "order_id": "RPP-003",
        "usuario_id": "USR-1003",
        "monto": 320.00,
        "fecha": "2026-07-27",
        "estado_entrega": "entregada",
        "confirmacion_gps": True,
        "producto_solicitado": "Sushi roll x8 piezas",
        "producto_entregado": "Sushi roll x8 piezas",
        "reembolsos_ultimos_30_dias": 0,
        "restaurante": "Sushi Tora",
        "motivo_falla": None,
    },

    # Caso 4: Usuario con 3 reembolsos en últimos 30 días → ESCALAR aunque caso parezca legítimo
    "RPP-004": {
        "order_id": "RPP-004",
        "usuario_id": "USR-1004",
        "monto": 150.00,
        "fecha": "2026-07-30",
        "estado_entrega": "fallida",
        "confirmacion_gps": False,
        "producto_solicitado": "Pizza mediana pepperoni",
        "producto_entregado": None,
        "reembolsos_ultimos_30_dias": 3,
        "restaurante": "Pizza Hut",
        "motivo_falla": "repartidor canceló el viaje",
    },

    # Caso 5: Producto equivocado, monto alto (>$500) → ESCALAR por excede límite de política
    "RPP-005": {
        "order_id": "RPP-005",
        "usuario_id": "USR-1005",
        "monto": 780.00,
        "fecha": "2026-07-29",
        "estado_entrega": "entregada",
        "confirmacion_gps": True,
        "producto_solicitado": "Carne asada 500g + guarniciones",
        "producto_entregado": "Pollo asado 300g",
        "reembolsos_ultimos_30_dias": 0,
        "restaurante": "La Parrilla del Norte",
        "motivo_falla": None,
    },

    # Caso 6: Cancelación sin reembolso → SIEMPRE ESCALA
    "RPP-006": {
        "order_id": "RPP-006",
        "usuario_id": "USR-1006",
        "monto": 210.00,
        "fecha": "2026-07-28",
        "estado_entrega": "cancelada",
        "confirmacion_gps": False,
        "producto_solicitado": "Pad Thai + primavera",
        "producto_entregado": None,
        "reembolsos_ultimos_30_dias": 0,
        "restaurante": "Thai Garden",
        "motivo_falla": "restaurante cerró antes del horario publicado",
    },

    # Caso 7: Problema de pago → SIEMPRE ESCALA
    "RPP-007": {
        "order_id": "RPP-007",
        "usuario_id": "USR-1007",
        "monto": 340.00,
        "fecha": "2026-07-30",
        "estado_entrega": "pendiente",
        "confirmacion_gps": False,
        "producto_solicitado": "Despensa semanal básica",
        "producto_entregado": None,
        "reembolsos_ultimos_30_dias": 0,
        "restaurante": "Rappi Supermercado",
        "motivo_falla": "cargo duplicado en tarjeta",
    },

    # Caso 8: Demora excesiva, sin criterio de reembolso automático definido → ESCALA
    "RPP-008": {
        "order_id": "RPP-008",
        "usuario_id": "USR-1008",
        "monto": 175.00,
        "fecha": "2026-07-30",
        "estado_entrega": "en_camino",
        "confirmacion_gps": False,
        "producto_solicitado": "Burritos x2 + agua",
        "producto_entregado": None,
        "reembolsos_ultimos_30_dias": 1,
        "restaurante": "Burritos La Paloma",
        "motivo_falla": "más de 90 minutos sin entrega",
    },

    # Caso 9: Datos completos y consistentes, reembolso simple → APROBAR (segundo caso feliz)
    "RPP-009": {
        "order_id": "RPP-009",
        "usuario_id": "USR-1009",
        "monto": 98.00,
        "fecha": "2026-07-29",
        "estado_entrega": "fallida",
        "confirmacion_gps": False,
        "producto_solicitado": "Café americano + croissant",
        "producto_entregado": None,
        "reembolsos_ultimos_30_dias": 0,
        "restaurante": "Café Punta del Cielo",
        "motivo_falla": "repartidor tuvo accidente menor, orden no completada",
    },

    # Caso 10: Borderline — exactamente $500 MXN y exactamente 2 reembolsos previos → AMBIGUO
    "RPP-010": {
        "order_id": "RPP-010",
        "usuario_id": "USR-1010",
        "monto": 500.00,
        "fecha": "2026-07-30",
        "estado_entrega": "entregada",
        "confirmacion_gps": True,
        "producto_solicitado": "Botana familiar + refrescos x4",
        "producto_entregado": "Botana familiar sin refrescos",
        "reembolsos_ultimos_30_dias": 2,
        "restaurante": "Oxxo Rappi",
        "motivo_falla": None,
    },
}
