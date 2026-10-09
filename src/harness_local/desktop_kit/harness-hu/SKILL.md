---
name: harness-hu
description: Iniciar una HU supervisada con roles de proyecto y prácticas de Harness, sin activar coordinación completa ni acciones remotas.
---

1. Seleccionar cliente, checkout, HU y límites autorizados; leer AGENTS cliente.
2. Consultar harness_local.quality_resources.load_quality(); practices.json es
   recurso empaquetado pasivo. No ejecutar scripts upstream ni instalar globalmente.
3. Consultar harness_local.desktop_resources.load_desktop(). Perfiles activados
   necesitan selección explícita de modelo/esfuerzo y disponibilidad de cuenta;
   ausencia bloquea, nunca sustituir silenciosamente.
4. Para HU pequeña usar principal. Para mayor impacto asignar analyst,
   impact-analyzer o planner con entradas/salidas acotadas. Registrar role,
   write_paths, isolation y delegation_depth; llamar check_assignments antes
   de delegar. No exceder cuatro assignments ni un nivel de delegación.
5. Developer es único escritor del candidato. Tester escribe solo tests asignados.
   Auditor/verifier reciben candidato inmutable y permisos efectivos read-only.
6. Required ausente => blocked; optional ausente => unavailable/not_checked.
   Configuración TOML no prueba sandbox/MCP/hook efectivo. No habilitar hooks
   sin evento observado; registrar cobertura por evento y versión.
7. Emitir evidencia sintética con versión app/motor, configuración efectiva y
   referencia sanitizada. Files/CLI => not_checked. E03/E04 requieren protocolo
   Desktop manual con anotación humana y tres repeticiones antes de passed.
8. Presentar resultado y pendientes. La coordinación HU/gates completa llega
   en 04; configurar no autoriza publicar, conectar producción ni ejecutar remoto.
