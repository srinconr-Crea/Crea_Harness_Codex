# Pruebas Crea 0.1.4 Implementation Plan

> Ejecución local en esta sesión; sin commits ni publicaciones. La autorización
> inicial pide comenzar si no hay dudas; no se añaden aprobaciones de diseño.

**Goal:** distribución manual con Tester y pruebas deterministas trazables.
**Architecture:** selector puro + adaptadores locales separados + configuración
fail-closed + cuatro perfiles secuenciales.
**Tech Stack:** Python >=3.11, Git, PowerShell, jsonschema Draft2020-12, pytest/JUnit.
**Spec:** ../specs/2026-10-21-pruebas-design.md

## Restricciones

- Conservar fuente 0.1.3, rama del usuario, licencias y skills upstream.
- Sin operaciones remotas, instalaciones globales, commit, push o PR.
- Catálogo ejecutable único; capacidades no entregadas bloquean al requerirse.
- No incorporar referencias cliente; lista de neutralidad fuera del entregable.

## Archivos afectados y tareas

- [x] 1. Copiar 0.1.3 a artifacts/crea-manual-kit-0.1.4; integrar carpeta completa
  .agents/skills/Crea/crea-pruebas, perfil tester.toml, docs/pruebas/*.
- [x] 2. Añadir tests/crea/test_testing_adapters.py con fixtures Git reales y procesos
  locales. Verificar fallos antes de implementar scripts/crea/testing/{git_adapter,
  schemas,reports,execution,workflow}.py y scripts/crea/pruebas.py.
- [x] 3. Combinar docs/proyecto.json/schema, roles, AGENTS, orquestador,
  scripts/crea/verificar-kit.ps1 y validador Python. Registrar paths anidados únicos
  y contenidos; probar fallos de referencias, schemas, perfiles y capacidades.
- [x] 4. Actualizar configuracion-manual.md, LEEME, catálogo/extensiones,
  handoffs/evidencia, buenas prácticas/contexto y tareas OpenSpec por rol.
- [x] 5. Ejecutar helper/adaptadores, demo sintético y escenarios locales; comparar
  fuente/upstream; validar TOML/YAML/schemas/referencias original y personalizada.
- [x] 6. Registrar validación/límites, regenerar inventario/manifest, auditar árbol
  completo y ZIP con herramienta del paquete; entregar ZIP y sha256 locales.

## Foco de revisión

Untracked/renames/delete/conflictos; exclusiones peligrosas o circulares; proceso
timeout/entorno/logs; reporte cero tests/skips/criterios faltantes; evidencia vieja,
modificada o de otro plan; runtime requerido nunca se omite para pasar el gate.

## Registro

Exploración: fuente real 0.1.3 y paquete 0.1.0; helper sin adaptadores reales.
Decisión: conservar rama pedida, distribuir 0.1.4 en staging dentro del clon.
Semántica oficial consultada: límite de threads excluye principal; secuencialidad
y prohibición de subdelegación siguen siendo procedimiento, no sandbox técnico.

Verificado: 58 tests del kit, original 310 checks, personalizada 36 checks,
auditoria arbol/ZIP sin pendientes, 275 entradas del ZIP; fuente 0.1.3 intacta.
Suite del motor legado interrumpida con dos fallos reproducidos, documentados
por separado en docs/INTEGRACION-PRUEBAS-0.1.4.md. No se declara pasada.
