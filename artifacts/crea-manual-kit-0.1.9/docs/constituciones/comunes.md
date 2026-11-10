# Reglas comunes

Estado: active
Revisión: 1

Reglas iniciales del kit, activadas solo al adoptar esta configuración en el proyecto.
Fundamento local: AGENTS.md y docs/buenas-practicas/general.md de la entrega anterior.

### CREA-COM-001
Aplicación: toda HU antes de implementar.
Obligación: definir objetivo, entradas, salidas, criterios y plan proporcional de validación.
Fundamento: evitar implementar un comportamiento diferente del solicitado.
Evidencia: referencias a criterios OpenSpec/solicitud y plan preliminar.
Comprobación: review
Excepciones: no omitir criterios; el responsable puede simplificar su detalle proporcionalmente.

### CREA-COM-002
Aplicación: cuando se afirme ejecución o resultado técnico.
Obligación: conservar estado real y recibos ligados a candidato, plan y entorno vigentes.
Fundamento: un JSON válido, mock o exit 0 sin casos no demuestra el comportamiento requerido.
Evidencia: plan, resultados, recibos y gate canónicos; not_run/blocked cuando corresponda.
Comprobación: automatic
Excepciones: no convertir una ejecución ausente o simulada en passed.

### CREA-COM-003
Aplicación: toda escritura y entrega.
Obligación: respetar rutas y acciones autorizadas, cambios ajenos y ausencia de secretos versionados.
Fundamento: la coordinación no implica permisos generales sobre el proyecto.
Evidencia: snapshots de intervalo, diff completo, revisión y autorizaciones aplicables.
Comprobación: review
Excepciones: ampliar rutas requiere decisión del responsable; no hay excepción para versionar credenciales.
