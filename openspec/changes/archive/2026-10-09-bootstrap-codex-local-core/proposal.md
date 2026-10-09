# Proposal

## Why

Local-Harness tiene una propuesta arquitectónica, pero aún no dispone de un producto ejecutable que compruebe el equipo o prepare la incorporación de un cliente. Necesitamos una primera base verificable que mantenga separados producto, configuración cliente y estado local antes de instalar agentes, conectar Databricks o automatizar HUs.

## What Changes

- Crear un paquete Python genérico con módulos separados para contratos/validación y comandos locales, distribuido mediante un entry point `harness`.
- Definir tres contratos versión 1: descriptor portable del cliente, política seleccionada por el operador y binding local del desarrollador. Validar identidad, rutas, integridad y ausencia de credenciales sin activar permisos desde el repositorio.
- Incorporar `harness doctor` para diagnosticar herramientas locales y preparación del target, con salida humana y JSON, sin autenticación ni acceso remoto.
- Incorporar `harness init --dry-run` para presentar un plan de onboarding de un checkout existente. Informar archivos propuestos, existentes y conflictos sin instalar, clonar, escribir en el target o persistir bindings.
- Probar el producto con repositorios y perfiles sintéticos de dos clientes; usar la estructura conocida de NaturaPet como referencia, sin incluir sus credenciales, recursos ni código en el paquete.
- Documentar instalación de desarrollo, comandos, contratos y límites del diagnóstico.

El esquema detallado de módulos, archivos y pruebas se define en `design.md` y `tasks.md`. Este cambio no implementa el flujo completo de HU, aprobación/manifiestos de cambios, ejecución remota, SQLite, instalador Windows, plugin, hooks o agentes operativos. Tampoco publica un repositorio GitHub ni modifica configuraciones globales de Codex.

## Capabilities

### New Capabilities

- `client-configuration`: contratos versionados para descriptor, política y binding, con validación de identidad, integridad y separación por cliente.
- `local-diagnostics`: diagnóstico local reproducible de herramientas y preparación del repositorio mediante `harness doctor`.
- `onboarding-preview`: plan de incorporación sin efectos laterales mediante `harness init --dry-run`, preservando configuraciones existentes.

### Modified Capabilities

Ninguna. El inventario actual de `openspec/specs/` está vacío y no existe implementación previa del producto.

## Impact

- Nuevos archivos previstos: `pyproject.toml`, `src/harness_core/`, `src/harness_local/`, `schemas/`, `tests/`, `README.md` y documentación de contratos/operación.
- Dependencias propuestas: Python 3.13, Pydantic 2, PyYAML y pytest de desarrollo. Git, Node, OpenSpec y Databricks CLI se detectan; este incremento no los instala.
- Los clientes siguen siendo repositorios externos. Las pruebas no requieren red, credenciales, modelos ni recursos Databricks.
- La configuración OpenSpec y sus siete Skills ya quedaron inicializadas como preparación autorizada; completar estos artefactos no significa que el producto esté implementado.
