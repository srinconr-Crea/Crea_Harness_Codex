# Diagnóstico y propuesta de adaptación de 02

Fecha: 2026-10-09, America/Bogota. Adaptación aprobada por el usuario y aplicada a los artefactos de
planificación de 02/03. Implementación y sync de 02 completos y verificados.
Habilita 03 para preparación supervisada; no certifica aislamiento ni capacidades fallidas.

## Evidencia y causa probable

El chat `01a12248-1ea3-7ad3-a0d8-035f6d577236` seleccionó roles personalizados.
Su registro de llamadas indica agent_type, sin overrides de modelo/esfuerzo;
el contrato runtime expuso gpt-5.6-luna/medium para los tres roles comprobados.
Auditor y verifier crearon archivos vacíos sin escalación pese al TOML read-only.
El fallo de aislamiento está observado, no es un check pendiente ni un passed.
Los documentos originales y las seis respuestas de eval están conservados con
hashes en manifest.json. La anotación humana continúa pendiente. E04 propone
tests de null explícitos en una de tres respuestas originales, no en todas.

La documentación oficial confirma que las elecciones runtime de sandbox del
padre se reaplican al hijo incluso cuando su archivo declara otros defaults:
https://learn.chatgpt.com/docs/agent-configuration/subagents
Esto es compatible con el workspace-write observado. No se ha demostrado
que esta versión de Desktop permita un padre escritor y un hijo restringido.
No se considera un error corregible inventando una nueva clave TOML.

## Última prueba acotada, si la app expone el ajuste

En una sesión independiente de revisión, seleccionar modo read-only para el
padre antes de delegar. Repetir una creación exclusiva de archivo descartable
con auditor y verifier, sin escalación. Usar nombres nuevos para no confundir
archivo existente con denegación del sandbox. Conservar error y parámetros.
Si la app no expone ese modo, registrar unsupported; no repetir indefinidamente.
Esta prueba requiere selección manual en Desktop y no certifica sesiones mixtas.

## Revisión aprobada de artefactos existentes

1. proposal.md: ampliar What Changes y criterio de salida con dos resultados
   separados: integración preparada para uso supervisado y capacidades certificadas.
   Poder preparar no autoriza afirmar aislamiento ni disponibilidad remota.
2. design.md: permitir revisores supervisados en esta versión cuando el sandbox
   esté en conflict. Revisar candidato identificado por commit/hash/snapshot;
   comparar contenido antes y después y rechazar aceptación ante cambios. Esto
   detecta alteraciones persistentes; no impide escritura ni detecta necesariamente
   un cambio restaurado. No equivale a control de permisos ni a candidato inmutable.
3. specs/role-tool-catalog/spec.md: mantener el escenario Read-only reviewer
   (nunca certificar si escribe) y añadir alternativa explícita: un conflicto de
   sandbox permite únicamente revisión supervisada aceptada por el operador;
   identidad/evidencia del candidato se conservan y drift bloquea aceptación.
4. specs/desktop-integration/spec.md: añadir requisito de preparación supervisada
   con informe por capacidad y fallos observados. La certificación estricta se
   conserva sin excepciones; unsupported/not_checked/conflict no pasan a passed.
5. tasks.md: distinguir comprobación realizada con resultado fallido de capacidad
   certificada. Añadir validación del modo supervisado y conservar evals originales,
   scores/anotación humana pendientes y resultados negativos. No cerrar pendientes
   por cambiar solo su descripción.

## Implementación y sincronización verificadas

Sincronizar main specs; aplicar cualquier delta de implementación y probarlo.
Mantener assess_certificate estricto: el certificado completo continúa false
si la observación de permisos contradice el perfil. La preparación supervisada
es un resultado separado, nunca una excepción dentro de ese certificado.

Ajustar docs/desktop-integration.md, la evidencia, roadmap.md y roadmap.json.
Revisar 03 (proposal/design/tasks/specs): su dependencia debe aceptar 02 verificado
para preparación supervisada y continuar mostrando prepared/certified por separado.
El onboarding preparado no garantiza aislamiento ni habilita fases que exijan una
capacidad fallida. Evaluar también referencias de permisos/candidato de 04–08.
Solo tras implementar y verificar ese alcance se habilita avanzar a 03.

No se propone borrar el fallo, marcar autoevaluación como aceptación humana,
desactivar controles de seguridad ni dar por completo 02 con sus requisitos actuales.

Resultado final: véase verification.md y supervised-verification.json. La prueba opcional de padre read-only sigue no observada; no es condición de éxito del alcance supervisado aprobado.
