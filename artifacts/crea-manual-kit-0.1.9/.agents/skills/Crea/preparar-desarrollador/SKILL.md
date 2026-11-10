---
name: crea-preparar-desarrollador
description: Use when another developer needs to prepare a local machine for an already configured Crea project, or when the user selects section C of the kit prompt.
---

# Preparar desarrollador en proyecto configurado

Leer `AGENTS.md`, `docs/proyecto.json` y [la guía local](../../../../docs/preparar-desarrollador.md).
Esta entrada es preparación personal, no onboarding A, actualización B ni HU.
El prompt de distribución puede no estar en el clon.

1. Inspeccionar checkout, revisión, configuración y herramientas con
   `python -B scripts/crea/preparar-desarrollador.py inspect --repo .`, usando un Python existente.
   No instalar, autenticar, contactar servicios o escribir por inspeccionar.
2. Si el onboarding compartido está incompleto o hay consumidores incompatibles,
   informar pendiente al responsable; no completar setup ni ejecutar `openspec init`.
   Conservar skills, modelos, reglas, catálogos, specs y recibos.
3. Elegir el intérprete personal. `bind` presenta el cambio; `--apply-local` aplica
   únicamente el binding local pedido. Si hay una HU activa, explicar primero el
   efecto de cambiar su entorno y conservar planes/recibos anteriores.
4. Para herramientas ausentes, usar solo instalaciones/actualizaciones dentro del
   alcance autorizado; no asumirlo por necesitar la herramienta. Continuar lo independiente.
   Credenciales, MFA, confianza y permisos corresponden a la persona. No iniciar login por ella.
5. `inspect --online` permite lecturas acotadas de servicios aplicables con identidad
   disponible. No consultas Boards sin HU/fase, pipelines o escrituras de prueba.
   Leer un repo no acredita permiso de push, PR o merge. No activar Databricks/hooks/MCP.
6. Informar ready/partial/blocked, herramientas, pendientes y comprobaciones not_run.
   Exportar diagnóstico solo si se solicita a `.crea/diagnosticos/<id>.json` nuevo.
   Si ya estaba preparado, conservar el binding equivalente sin reescribirlo.

Windows: usar el Python explícito y wrappers `.cmd` cuando corresponda; no exigir
Activate, cambiar ExecutionPolicy o modificar configuración global. No declarar
roles nativos, hooks o runtime observados por existir sus archivos.
