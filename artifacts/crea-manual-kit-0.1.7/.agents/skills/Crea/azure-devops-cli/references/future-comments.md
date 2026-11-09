# Publicación futura, deshabilitada

La ayuda Azure CLI 2.91.0 con azure-devops 1.0.9 muestra
`az boards work-item update --discussion`. Disponibilidad no significa permiso.
El helper no implementa update, discussion, POST, PATCH, PUT ni DELETE.

Habilitar publicación requeriría otro cambio de capacidad: texto y destino exactos
presentados a la persona, autorización concreta, identidad/proyecto comprobados,
verificación posterior y reconciliación/idempotencia para evitar duplicados tras un
timeout. No pedir ahora aprobación de una operación que este kit no puede ejecutar.
Preparar texto local cuando se solicite y señalar capacidad futura deshabilitada.
