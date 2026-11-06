# Contexto del proyecto

> Plantilla editable. Los ejemplos explican que escribir y NO son hechos del cliente.
> Completar los apartados aplicables; usar "No aplica" con motivo. Se pueden agregar secciones.

## 1. Identidad y objetivo

Nombre, responsable y problema que resuelve. Ejemplo: "Consolidar pedidos diarios de
canales digitales para conciliacion; el equipo de operaciones consume el resultado".
Indicar que queda fuera del proyecto y como se mide el exito.
En docs/proyecto.json → project.repository registrar proveedor (github o azure_devops),
URL del repositorio sin credenciales, organizacion y proyecto si aplican. Registrar la
rama base real en project.base_branch. Ejemplo Azure DevOps: organizacion "mi-organizacion",
proyecto "mi-equipo" y URL copiada desde Repos > Files > Clone. Estos son ejemplos,
no datos del cliente. La conexion Git local usa Git Credential Manager; para el trabajo Git. Si el proveedor es Azure DevOps Services, instalar Azure CLI y azure-devops para crear el PR. Completar organization con la URL HTTPS y project con el nombre o ID real.

## 2. Dominio y reglas de negocio

Definir entidades, terminos, indicadores y excepciones. Ejemplo explicativo: "Un pedido
puede contener varias lineas; una devolucion referencia la linea original". Explicar
grano, claves, monedas, zona horaria y tratamiento de anulaciones/nulos.

## 3. Arquitectura y flujo

Describir entradas → transformaciones → salidas y dependencias. Si existen capas,
explicar responsabilidades; no asumir Bronze/Silver/Gold si el proyecto usa otra estructura.
Referenciar diagramas o decisiones existentes sin copiar todo su contenido.

## 4. Fuentes, contratos y consumidores

Origen, formato, frecuencia, esquema y propietario de cada fuente. Destinos y consumidores.
Definir controles de unicidad, integridad, calidad y compatibilidad. Usar nombres reales
cuando se conozcan; nunca inventar tablas. No pegar muestras sensibles ni credenciales.

## 5. Entornos y conexiones

Describir dev/staging/prod que realmente existan. En docs/proyecto.json registrar perfil,
host, catalog/schema, target, warehouse y versiones aplicables; aqui explicar su finalidad.
Credenciales en login/perfil local o gestor de secretos, nunca en este documento.

## 6. Stack, versiones y convenciones

Lenguajes, herramientas y restricciones compatibles con el runtime. Explicar nombres,
modularizacion y formatos de notebooks. El inventario de rutas/extensiones vive en
docs/proyecto.json; actualizarlo al crear o mover componentes.

## 7. Desarrollo y validacion

Como preparar dependencias y ejecutar pruebas del proyecto. Registrar comandos concretos
en docs/pruebas/policy.json; validation.required_checks solo referencia IDs.
Justificar runtime por comportamiento/politica, sin asumir recursos del cliente. Explicar fixtures, oraculos,
criterios de aceptacion y pruebas remotas que requieren autorizacion. Un comando de
ejemplo no cuenta como prueba ejecutada.

## 8. Operacion, despliegue y recuperacion

Quien puede desplegar, recursos/targets, ejecucion, alertas y procedimiento de reversion.
Para esta version manual, dejar claro que el workflow no despliega automaticamente.

## 9. Restricciones y decisiones

Limites funcionales, de datos, costos, cumplimiento y permisos. Enlazar decisiones con
fecha y motivo. Cuando una practica comun no aplique, justificar la excepcion aqui.

## 10. HU y criterios de terminado

Como se expresa una HU y que evidencia requiere su cierre. Flujo: planner → nueva solicitud
humana de apply → developer → reviewer → sync → aprobacion humana de archivo/publicacion
→ archive → commit/push en feature/<hu> → enlace de PR. Definir quien acepta funcionalmente la HU.
Configurar delivery.remote, branch_prefix y web_repository_url si la URL de clonacion
no permite derivar la pagina web. No se hace merge ni deploy desde el workflow.

## 11. Configuracion y extensiones

Referenciar nuevas skills de Project, agentes, MCP y hooks desde docs/proyecto.json.
Describir para que se usan y sus limites. Cambiar perfil en .codex/agents/*.toml y
configuracion nativa del padre en .codex/config.toml. Ver docs/extensiones.md.

## 12. Pendientes de configuracion

Enumerar preguntas abiertas con propietario. Al terminar setup, comprobar el inventario,
definir checks y cambiar project.setup_complete a true en docs/proyecto.json.

## 10. Perfil de pruebas del cliente
Completar catalogo de fallos/fixtures, dependencias/consumidores, criterios, oraculos
independientes y herramientas aplicables. Revisar execution.json y su huella de
politica antes de habilitar setup. Indicar capacidades requeridas inactivas como
bloqueo explicito; docs/pruebas/capabilities.json registra los limites de esta version.
