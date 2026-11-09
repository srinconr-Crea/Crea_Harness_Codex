# Borrador de PR — <change>

Fuente canónica de estructura para GitHub y Azure DevOps. En HU adoptadas, el contenido
canónico está en `evidence.delivery` del handoff presentado: title/body, repositorio, ramas
y SHA previsto. Materializar `docs/hu/<change>/pr-title.txt` y `pr-body.md` con solo esos textos;
`pr.md` es una vista derivada con referencias y estado. No enviar instrucciones de plantilla
como descripción ni mantener una plantilla nativa GitHub editada independientemente.

Contenido común del cuerpo: problema y comportamiento resultante, alcance, HU/OpenSpec,
pruebas reales y límites, reglas/excepciones pertinentes y referencias de objetos/entrega.
Preparar y presentar antes de autorizar publicación. Registrar digest del paquete aprobado.

Estados: draft (borrador local), form_prepared (campos preparados comprobados),
creation_unconfirmed (resultado ambiguo), created_verified (ID/URL y lectura contrastada).
Draft del proveedor es una propiedad diferente del borrador local. Un enlace no acredita PR.

## 1. Identidad y enlace
- Rama origen: feature/<hu>
- Rama destino: valor real de project.base_branch
- Remoto y repositorio web:
- Proveedor y modo (Azure CLI aprobado / formulario web):
- Enlace previsto al repo/formulario:
- Estado: borrador hasta comprobar el push; un enlace no es un PR creado.

## 2. Titulo para copiar
Describir el cambio funcional concreto en una linea.

## 3. Descripcion para copiar
Problema, comportamiento resultante y alcance. Referenciar HU y cambio OpenSpec archivado.
Incluir pruebas realmente ejecutadas, resultado y limitaciones pendientes; no secretos.

## 4. Configuracion y extensiones
Adaptar al template real del repositorio si existe. El principal prepara este archivo antes
del commit. El SHA y el recibo de push van en la respuesta final para evitar modificar
archivos despues de versionarlos. Azure: el principal crea el PR aprobado y entrega ID/URL y verificacion en la respuesta final.
GitHub: la persona crea el PR desde el formulario. No guardar como creado un PR aun no confirmado.
