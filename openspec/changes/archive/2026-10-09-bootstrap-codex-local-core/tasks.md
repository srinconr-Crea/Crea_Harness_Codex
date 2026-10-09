# Tasks

## 1. Base del paquete

- [x] 1.1 Crear `pyproject.toml`, paquetes `harness_core`/`harness_local` y entry point `harness`; verificar en venv aislado que `harness --version` y `python -m harness_local --help` terminan correctamente.
- [x] 1.2 Definir dependencias de runtime/desarrollo y exclusiones Git de venv/build/caché; verificar que construir e instalar el wheel incluye recursos del paquete sin datos de cliente.
- [x] 1.3 Agregar README con alcance, instalación de desarrollo y límites; verificar que los comandos documentados coinciden con la CLI y que no presentan agentes, SQLite o ejecución remota como implementados.

## 2. Configuración de clientes

- [x] 2.1 Implementar los tres contratos estrictos versión 1 y generar schemas; verificar aceptación de fixtures válidos, rechazo de versiones/campos desconocidos y concordancia entre schemas y modelos.
- [x] 2.2 Implementar lectura segura/acotada, detección de claves duplicadas y rechazo de secretos; verificar malformed YAML/JSON, tamaño excedido, archivos no regulares y sanitización de mensajes.
- [x] 2.3 Implementar validación de rutas, traversal, symlinks/junctions y separación de estado cliente/checkout; verificar rechazos sin crear carpetas y cubrir junctions Windows con una prueba disponible en el entorno objetivo.
- [x] 2.4 Implementar validación cruzada de cliente, target, rama, remote y hash de política explícita; verificar HTTPS/SSH equivalentes, origin ausente/incorrecto, política cambiada y binding de otro cliente.
- [x] 2.5 Documentar los tres contratos y confianza en `docs/configuracion-clientes.md`; verificar los ejemplos contra schemas y que ninguna configuración permite al repo activar permisos por sí mismo.

## 3. Diagnóstico local

- [x] 3.1 Implementar sondas inyectables de versión con argumentos fijos, límites y timeout; verificar herramientas ausentes, versión no interpretable, proceso lento y salida excesiva, sin shell interpolado ni red.
- [x] 3.2 Agregar matriz de compatibilidad y agregación de estados; verificar que mínimos/versiones fijadas, fallos independientes y `not_checked` producen estados/códigos previstos sin inventar certificación Desktop.
- [x] 3.3 Implementar inspección target con Git de solo lectura, soporte de worktree y detección de OpenSpec/siete Skills; verificar target inexistente, worktree válido, verify ausente y generatedBy incompatible.
- [x] 3.4 Exponer `harness doctor` humano/JSON y validación opcional de configuración; verificar stdout JSON parseable, combinación incompleta de flags, códigos 0/1/2 y snapshots sin escrituras.
- [x] 3.5 Documentar diagnóstico en `docs/operacion-local.md`; verificar que distingue preparación local, autenticación remota y capacidades Desktop pendientes y ofrece remedios sin ejecutarlos.

## 4. Preview de onboarding

- [x] 4.1 Implementar `harness init` solo con `--dry-run` y validación de entradas; verificar error `apply_not_supported` sin el flag y ausencia de clonación ante target inexistente.
- [x] 4.2 Incorporar descriptor y plantilla AGENTS genérica como propuestas revisables; verificar contenido/hash deterministas, datos explícitos para descriptor ausente y conflicto sin sobrescritura de AGENTS personalizado.
- [x] 4.3 Planificar preservación/preparación OpenSpec y revisión manual de Codex; verificar cliente preparado, workflows faltantes e incompatibles sin invocar instalación ni generar agentes/hooks operativos.
- [x] 4.4 Implementar acciones ordenadas y render humano/JSON; verificar igualdad semántica de dos previews, hashes de entrada y códigos 0/1/2 ante plan válido, bloqueado y entradas inválidas.
- [x] 4.5 Agregar pruebas con dos clientes sintéticos y snapshots de target/estado/configuración; verificar que preview no escribe, no importa/ejecuta código del cliente y no invoca red, modelos o autenticación.
- [x] 4.6 Documentar ejemplos de preview y acciones futuras en `docs/operacion-local.md`; verificar que los comandos corresponden a la CLI y que el plan no se presenta como onboarding aplicado.

## 5. Integración y cierre del incremento

- [x] 5.1 Ejecutar la suite completa y smoke test del wheel en venv Windows; conservar evidencia real de entry point, recursos, códigos y aislamiento sin instalación global.
- [x] 5.2 Revisar trazabilidad entre escenarios de las tres specs y pruebas entregadas; verificar que ningún requisito quedó cubierto solo por una afirmación del modelo.
- [x] 5.3 Ejecutar validación OpenSpec estricta y usar `openspec-verify-change` para contrastar implementación y evidencia; verificar que tareas no realizadas permanecen pendientes.
- [x] 5.4 Presentar resultados para revisión antes de sync/archive o publicación; verificar que el diff final se limita al incremento y que no se creó repo remoto ni se alteraron clientes reales.
