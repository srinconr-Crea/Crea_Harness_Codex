# Archivo administrativo con aceptación pendiente

Fecha: 2026-10-14, America/Bogota. Schema: spec-driven.

El usuario autorizó explícitamente archivar este cambio con los pendientes
conocidos para realizar una prueba real y abrir cambios posteriores si aparecen
defectos o mejoras. Esta decisión sustituye la preferencia anterior de mantener
08 activo hasta aceptación. También autorizó commit y push del archivo.

La implementación local está verificada y las dos capacidades principales están
sincronizadas: seis requisitos y quince escenarios. Se conservan ocho tareas
completas de trece. Las tareas 3.1, 3.2, 3.3, 3.4 y 4.3 permanecen sin marcar;
su traslado a archive no prueba ejecución ni aceptación.

Persisten las 144 evaluaciones reales de 06/07, el sandbox compatible, los
recorridos HU/PR/reanudación del harness, alpha/beta, piloto sintético NaturaPet,
usuario nuevo e instalación en otro entorno. Los once protocolos preparados
siguen not_run y los gates mantienen certified=false, release_allowed=false,
publication_allowed=false y next_increment_enabled=false.

El archivo conserva código, contratos, manifiesto candidato y resultados locales;
no certifica release ni elimina los criterios de aceptación de las main specs.
La prueba real posterior deberá conservar resultados observados y restricciones.
Los defectos o mejoras se gestionarán mediante nuevos cambios; no se convierten
resultados pendientes en passed para cerrar este registro.

Ver [verificación](../../../../docs/evidence/distribution-verification.md) y
[protocolos](../../../../docs/evidence/distribution/protocols.json).
