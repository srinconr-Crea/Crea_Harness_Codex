# Tasks

## 1. Recursos OpenSpec verificables

- [x] 1.1 Generar en fixture temporal aislado los siete workflows con OpenSpec 1.13.2, tools codex y profile custom; verificar comando, diferencias, licencia y snapshots de HOME/XDG original, sin tocar clientes; si no se obtiene contenido verificable, bloquear y revisar design antes de continuar.
- [x] 1.2 Empaquetar configuración genérica y siete Skills con manifiesto de versión/SHA-256; probar recursos completos, alterados y ausentes, y documentar procedencia/reproducción sin invocar CLI OpenSpec en runtime.

## 2. Contratos, preview y exportación

- [x] 2.1 Añadir modelos estrictos de plan/journal y schemas generados; verificar versiones desconocidas, duplicados, secretos, límites de tamaño/operaciones y concordancia schemas/modelos sin cambiar contratos cliente v1.
- [x] 2.2 Incorporar binding propuesto desde flags explícitos y contenido concreto de recursos OpenSpec ausentes; verificar clientes preparados/no preparados, datos incompletos, raíces relativas y snapshots del dry-run sin escritura.
- [x] 2.3 Definir validación de destinos Windows y operaciones autorizadas por patrones/límites de política; probar paths equivalentes, ADS/device names, traversal, junctions, `.harness/` protegido, exceso de archivos/bytes y solapamientos externos sin bypass.
- [x] 2.4 Exportar plan mediante creación exclusiva y JSON canónico; verificar determinismo, hash/payload, destino existente/enlazado y que solo se crea el plan explícitamente solicitado.
- [x] 2.5 Separar `applicable` de readiness y documentar ambos modos de binding y exportación; comprobar códigos 0/1/2, snapshots, ejemplos CLI y conservación de los escenarios anteriores de preview.

## 3. Estado y exclusión por checkout

- [x] 3.1 Implementar journal externo con estados/operaciones, intent y completion durables; inyectar fallos antes/después de cada persistencia y probar corrupción/registro de otro cliente sin filtrar secretos.
- [x] 3.2 Implementar lock exclusivo por cliente/checkout y verificación de identidad del proceso dueño; probar procesos simultáneos, PID reutilizado/lock huérfano y que dry-run no crea ni elimina locks.
- [x] 3.3 Documentar formato, confianza, estados y límites de recuperación; verificar ejemplos contra schemas y evidencia de que no se crean SQLite ni archivos globales.

## 4. Aplicación local del plan

- [x] 4.1 Añadir preflight del plan contra target/política seleccionados y contenidos regenerados del kit; probar planes modificados, stale hashes/origin, destinos redirigidos y ausencia de escrituras cliente ante rechazo.
- [x] 4.2 Implementar creaciones exclusivas confinadas en Windows con protección reparse en apertura; probar sustitución concurrente de ancestros/destinos, ausencia de overwrite y fallo cerrado cuando no pueda garantizarse confinamiento.
- [x] 4.3 Aplicar operaciones allowlist con journal/binding final y preservación de contenido existente; probar cliente preparado/no preparado, AGENTS personalizado, incompatibilidad OpenSpec y specs/changes/código preexistentes intactos.
- [x] 4.4 Reconocer repetición completada del mismo plan e integrar doctor read-only; probar no duplicación de archivos/ejecuciones, modificaciones posteriores, herramienta opcional ausente y checks Desktop/auth pendientes.
- [x] 4.5 Exponer init apply con reportes humano/JSON y documentar autorización/preparación versus readiness; verificar CLI, hashes mostrados, campos efectivos y códigos de entrada/conflicto/fallo/éxito.

## 5. Recuperación conservadora

- [x] 5.1 Añadir preview de recuperación desde binding existente o plan validado cuando binding aún no se creó; probar interrupción previa al binding, journal ajeno/alterado y snapshots sin cambios ni locks nuevos.
- [x] 5.2 Recuperar con exclusión solo creaciones propias intactas y directorios propios vacíos; probar archivo editado, archivo ambiguo/parcial, directorio no vacío, policy cambiada y ausencia de borrados recursivos o preexistentes.
- [x] 5.3 Registrar recuperación/conflictos y documentar intervención manual para ownership incierto/lock vivo; probar salida JSON sanitizada y que no se afirma rollback completo si queda algún conflicto.

## 6. Integración del incremento

- [x] 6.1 Ejecutar matriz Windows de dos clientes sintéticos con inyección de fallos/races y guardia de comandos; verificar aislamiento target/binding/estado/global y ausencia de red, instalación, modelos, auth o tests del cliente.
- [x] 6.2 Ejecutar suite previa y nueva, construir wheel e instalarlo en venv aislado; comprobar entry points, schemas/recursos relevantes, preview/export/apply/recover y conservar evidencia real.
- [x] 6.3 Trazar cada escenario de las tres delta specs a pruebas/evidencia y usar openspec-verify-change; verificar validación estricta y marcar solo tareas probadas, sin sync/archive/publicación automática.
