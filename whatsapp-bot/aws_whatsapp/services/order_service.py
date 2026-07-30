from aws_whatsapp.data.mock_orders import MOCK_ORDERS

MOTIVOS_AUTONOMOS = {"orden_no_entregada", "producto_equivocado", "reembolso_solicitado"}
MOTIVOS_SIEMPRE_ESCALAN = {"cancelacion_sin_reembolso", "problema_pago"}
MONTO_MAXIMO_REEMBOLSO = 500.00
MAX_REEMBOLSOS_30_DIAS = 2


def consultar_orden(order_id: str) -> dict:
    """
    Busca la orden en el mock. Devuelve el dict completo o un error estructurado.
    """
    order = MOCK_ORDERS.get(order_id.upper().strip())
    if not order:
        return {
            "error": True,
            "mensaje": f"No encontré la orden {order_id}. Verifica que el número sea correcto.",
        }
    return {"error": False, **order}


def evaluar_reembolso(order_id: str, motivo: str) -> dict:
    """
    Aplica la política de reembolso de forma literal (if/else explícitos).
    Devuelve {"decision": "aprobado"|"rechazado"|"ambiguo", "razon": "..."}.
    """
    result = consultar_orden(order_id)
    if result.get("error"):
        return {"decision": "ambiguo", "razon": result["mensaje"]}

    motivo_lower = motivo.lower().strip()

    # Motivos que siempre escalan — sin excepción
    if motivo_lower in MOTIVOS_SIEMPRE_ESCALAN:
        return {
            "decision": "rechazado",
            "razon": f"El motivo '{motivo}' siempre requiere atención de un agente humano según la política actual.",
        }

    # Motivos fuera del alcance autónomo
    if motivo_lower not in MOTIVOS_AUTONOMOS:
        return {
            "decision": "rechazado",
            "razon": f"El motivo '{motivo}' no tiene criterio de reembolso automático definido — debe escalar a un agente.",
        }

    monto = result.get("monto", 0)
    reembolsos_previos = result.get("reembolsos_ultimos_30_dias", 0)
    confirmacion_gps = result.get("confirmacion_gps", False)
    estado_entrega = result.get("estado_entrega", "")
    producto_solicitado = result.get("producto_solicitado", "")
    producto_entregado = result.get("producto_entregado", "")

    # Inconsistencia: usuario reporta no entregada pero GPS confirma entrega exitosa
    if motivo_lower == "orden_no_entregada" and confirmacion_gps and estado_entrega == "entregada":
        return {
            "decision": "rechazado",
            "razon": "El GPS del repartidor confirma que la orden fue entregada. Hay inconsistencia entre el reporte y los datos del sistema — requiere revisión humana.",
        }

    # Verificar condición de producto equivocado
    if motivo_lower == "producto_equivocado":
        if producto_solicitado == producto_entregado or producto_entregado is None and estado_entrega != "entregada":
            return {
                "decision": "ambiguo",
                "razon": "Los datos de la orden no confirman que se haya entregado un producto diferente al solicitado.",
            }

    # Verificar condición de no entregada
    if motivo_lower == "orden_no_entregada":
        if estado_entrega not in ("fallida", "cancelada") and not (not confirmacion_gps and estado_entrega != "entregada"):
            return {
                "decision": "ambiguo",
                "razon": "El estado de la orden no confirma falla de entrega de forma inequívoca.",
            }

    # Caso borderline: exactamente en el límite de reembolsos previos y monto
    if reembolsos_previos == MAX_REEMBOLSOS_30_DIAS and monto == MONTO_MAXIMO_REEMBOLSO:
        return {
            "decision": "ambiguo",
            "razon": f"El usuario tiene exactamente {reembolsos_previos} reembolsos en los últimos 30 días y el monto es exactamente ${monto} MXN — está en el límite de la política, requiere revisión humana.",
        }

    # Excede límite de monto
    if monto >= MONTO_MAXIMO_REEMBOLSO:
        return {
            "decision": "rechazado",
            "razon": f"El monto de la orden (${monto} MXN) excede el límite de ${MONTO_MAXIMO_REEMBOLSO} MXN para reembolso automático.",
        }

    # Excede límite de reembolsos previos
    if reembolsos_previos > MAX_REEMBOLSOS_30_DIAS:
        return {
            "decision": "rechazado",
            "razon": f"El usuario ya tiene {reembolsos_previos} reembolsos en los últimos 30 días, superando el límite de {MAX_REEMBOLSOS_30_DIAS} permitidos para aprobación automática.",
        }

    # Todas las condiciones se cumplen → aprobar
    return {
        "decision": "aprobado",
        "razon": f"La orden cumple todos los criterios de política: entrega fallida o producto incorrecto confirmado, monto ${monto} MXN dentro del límite, y {reembolsos_previos} reembolsos previos dentro del rango permitido.",
    }
