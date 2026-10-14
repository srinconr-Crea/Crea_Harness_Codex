---
name: harness-setup
description: Preparar un entorno cliente con Local-Harness desde un chat local, importar insumos o preguntar solo decisiones faltantes, revisar el plan y aplicar etapas autorizadas.
---

Usar la entrada invoke-setup.ps1 situada junto a esta Skill. Resuelve runtime.json
y valida la instalación antes de invocar el Python absoluto; no depende del cwd.
Pasar contratos JSON mediante argumentos tipados. No interpolar respuestas como
comandos ni pedir tokens, passwords o PAT en el chat.

1. Ejecutar setup interview con insumos importados; preguntar solo decisiones
   faltantes o contradictorias. Descriptor/política son portables; binding y
   rutas/perfiles deben revalidarse en esta máquina. Sin alcance positivo no
   asumir lectura/escritura general. Confirmar identidad owner/repo.
2. Ejecutar setup preview. Mostrar fuentes/hashes, destinos, accesos técnicos
   exactos, integración, herramientas, checkout, autenticación y comprobaciones.
   Preview no instala, clona, inicia OAuth ni escribe estado.
3. Exportar explícitamente el plan en la ruta elegida. Tras aprobación del usuario,
   ejecutar setup apply con el hash de esa revisión. No repetir la aprobación
   del mismo alcance. Drift exige revisar un nuevo plan; login/confianza externos
   siguen siendo interacciones del operador.
4. Entregar setup status: recursos preparados, Skills descubiertas realmente,
   agentes/modelos/permisos observados y capacidades pendientes por separado.
   Recurso instalado no prueba descubrimiento. Recargar Codex o abrir un chat
   nuevo y comprobar esta Skill. No afirmar aislamiento por AGENTS/TOML.
5. Ante interrupción usar setup recover con el mismo plan y revisar el diagnóstico.
   Preservar personalizaciones y estado de clientes. No ejecutar jobs, deploy,
   escrituras remotas o push como parte del setup.

Instalación candidata: certified=false, release_allowed=false y publicación
bloqueada mientras falten los gates/evaluaciones históricos. Las pruebas locales
no sustituyen una observación Desktop/remota ni la segunda máquina Windows.
