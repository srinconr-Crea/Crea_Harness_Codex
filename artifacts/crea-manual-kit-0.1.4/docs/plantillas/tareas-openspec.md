# Tareas OpenSpec separadas por responsabilidad

Adaptar al cambio real; no son estados nuevos de CLI. Marcar solo la acción propia
ejecutada y con evidencia; separar tareas mixtas antes de completarlas.

## Implementación — Developer

- [ ] Implementar criterios y documentar consumidores afectados.
- [ ] Escribir tests/fixtures previstos con expected independiente; regresión justificada si aparece un defecto.
- [ ] Entregar ready_for_test, rutas exactas y diagnóstico focalizado.

## Ejecución — Tester

- [ ] Recibir plan final reconciliado desde Git completo y comprobar vigencia.
- [ ] Ejecutar checks seleccionados/configurados con efectos autorizados.
- [ ] Conservar recibos/IDs/assertions/cobertura y gate; ready_for_review o bloqueo con causa.

## Revisión — Reviewer

- [ ] Revisar código, riesgos/consumidores, fixtures/expected, cobertura/recibos; sin repetición rutinaria de batería.
- [ ] Seguir openspec-verify-change y resolver pendientes vía principal.
- [ ] Seguir openspec-sync-specs con revisión favorable; presentar diff para cierre.

## Cierre aprobado — Reviewer / Principal

- [ ] Registrar aprobación humana de archive y alcance de publicación si aplica.
- [ ] Reviewer sigue openspec-archive-change para el candidato aprobado.
- [ ] Principal realiza solo entrega Git/proveedor autorizada y comprueba resultado.

Existencia del código no completa ejecución/revisión; JSON válido no es aprobación
humana. No modificar skills upstream para incorporar estas casillas.
