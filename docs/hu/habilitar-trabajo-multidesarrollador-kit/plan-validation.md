# Plan reconciliado de validación

La implementación se valida como un único candidato 0.1.9. El fixture exacto se registra en fixture-019.json: sus 492 archivos corresponden byte por byte a la selección de distribución. El script reproducible scripts/validate_manual_019.py prepara catálogo, execution, binding personal, snapshot Git, handoff canónico y plan; run ejecuta la selección mediante los consumidores reales workflow.run y workflow.gate. Los recibos primarios se copian sin reescritura a pruebas/attempt-1. El expediente distingue la raíz del fixture de la raíz del mantenedor; los SHA del fixture no son commits de este repositorio.

Criterios CA01 entrega, CA02 entorno, CA03 preparación C, CA04 independencia A, CA05 semántica C/D, CA06 content-v3 con gate real y CA07 composición cliente. La policy contiene el ID real kit-regression y siete assertions con IDs JUnit reales previstos por estructura de colección. No duplica comandos en required_checks: el proyecto sintético conserva esa lista vacía para no contaminar fixtures internos; criterios y reglas seleccionan el check.

La configuración de validación es propia del fixture: no se añade al catálogo de negocio de clientes. El wrapper revisado añade al proceso de pruebas únicamente el directorio del Git existente, explícito en el argv. No se relaja el entorno mínimo del ejecutor productivo. El binding usa el Python ya preparado; no hay instalación, login ni servicios reales.

Las rutas aprobadas son la lista cerrada candidate/<ruta> del handoff. El rol Tester escribe exclusivamente los outputs revisados y sus temporales de prueba ignorados. Entrada canónica en handoffs/planificacion-1-entrada.json; handoff planificacion-1.json validado por schema sin resultados futuros. agent_id=null indica ejecución del rol en este flujo de validación, sin inventar UUID nativo. Los archivos del fixture se conservan para diagnóstico, fuera del paquete.

D1-D14 permanecen aplicables. Dependencias: 2→5→6→7 comparten B/V/H/Q y proyección; 3→4 comparte binding; 8→9 comparte composición/manifest; 10→11 exige recibos antes de revisión/cierre. A configura una vez, B migra por diff, C prepara a otra persona sin repetir setup. No se autoriza merge, rebase, deploy, Boards, pipelines, commit/push o PR por esta validación.

No se acreditan autenticación/MFA real, piloto de cuatro roles, hooks nativos o dos personas reales. Se usan Git local y dobles explícitos para fallos de servicios. Las pruebas sobre H y la simulación textual se mantienen separadas; no se afirma ejecución de árbol combinado.
