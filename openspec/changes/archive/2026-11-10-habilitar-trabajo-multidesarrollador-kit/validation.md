# Validación de la propuesta frente a la conversación

## Alcance y resultado

Se revisó la planificación del cambio único `habilitar-trabajo-multidesarrollador-kit` contra el pedido original adjunto, el resultado de Explore y la petición posterior de agruparlo todo en un cambio y validarlo. El resultado es **cobertura de planificación completa del alcance identificado**, con las limitaciones indicadas abajo. No significa implementación, aprobación del diseño por terceros, ejecución de las regresiones futuras o certificación del producto.

Artefactos: proposal, design, tasks y siete deltas de specs; adicionalmente este informe de revisión. La metadata `.openspec.yaml` fue creada por el CLI. La planificación contiene 47 requisitos, 90 escenarios y 74 tareas pendientes; ninguna casilla de implementación está marcada.

## Comprobaciones realizadas

| Comprobación | Resultado observado | Alcance |
| --- | --- | --- |
| `openspec validate habilitar-trabajo-multidesarrollador-kit --strict --json` | Válido, 1 passed, 0 failed, issues vacío | Forma y consistencia OpenSpec del cambio |
| `openspec status --change habilitar-trabajo-multidesarrollador-kit` | Proposal/specs/design/tasks completos como planificación | Existencia de artefactos, no avance de implementación |
| Inventario proposal↔specs | Dos capacidades nuevas y cinco existentes ampliadas; siete deltas coincidentes | Sin capacidad anunciada carente de spec ni delta ajeno a proposal |
| Requisitos/escenarios | 47 requisitos con SHALL/MUST y 90 escenarios WHEN/THEN | Sin descripción normativa mayor a 500 caracteres ni requisito sin escenario |
| Deltas MODIFIED | Dos títulos existentes comprobados en manual-kit-distribution | No se apunta a requisitos inexistentes ni se sustituye un bloque por un fragmento |
| Tareas | 74 IDs únicos, todos pendientes y con verificación | Trabajo organizado por dependencia y rol; Archive como seguimiento posterior |
| Revisión de contenido | Matriz de trazabilidad y recorridos A-F contrastados | Juicio de cobertura, adicional a la validación estructural |
| Límites de edición | Únicamente archivos de este cambio nuevos; sin diff de archivos rastreados del producto | Sin implementación, cambios a specs permanentes, ramas, commit/push o publicación |

La comprobación auxiliar de inventario, requisitos, escenarios y tareas se ejecutó con Python de biblioteca estándar en memoria, sin añadir un script al producto. Las verificaciones finales deben volverse a ejecutar tras cualquier edición posterior de estos artefactos.

## Matriz de trazabilidad del alcance

Abreviaturas de spec: **DL** developer-local-preparation; **HC** hu-target-compatibility; **MD** manual-delivery-traceability; **MP** manual-phase-contracts; **PC** project-context-lifecycle; **PT** project-testing-lifecycle; **MK** manual-kit-distribution. Todas las filas son cobertura prevista, no capacidades implementadas.

| ID | Compromiso del pedido/Explore | Contrato o evidencia en la propuesta | Diseño | Tareas |
| --- | --- | --- | --- | --- |
| R01 | Revisar rama, revisión y fuente efectiva 0.1.8 antes de diseñar | Context registra SHA y límites remotos/dependencias; MK preserva fuente | Context; D1 | 1.1-1.3 |
| R02 | Diagnóstico real y matriz implementado/parcial/pendiente | Tablas de fuentes, funciones observadas y brechas; distinction del motor histórico | Context | 1.4-1.6 |
| R03 | Un onboarding compartido y sesiones/checkouts independientes | DL Existing checkout and shared readiness; PC Shared versioned context across independent checkouts | D2; D12 | 4.1-4.2; 7.8 |
| R04 | Roles secuenciales por sesión y sin orquestador central | MP Session scoped sequential roles | D2 | 7.8; 11.1 |
| R05 | Base de creación y destino PR independientes con fallback | MD Independent feature origin and PR target | D3 | 2.1; 2.7 |
| R06 | Ramas, remotos, SHA reales, colisiones y refspec | MD Verified Git delivery provenance | D3-D4 | 2.2; 2.4; 5.2 |
| R07 | Evitar trabajo/push directo a quality, test y protegidas | MD Protected development and publication branches | D3 | 2.3; 2.8 |
| R08 | No publicar commits heredados de sprint como si fueran solo HU | MD Reviewed effective PR scope; HC Separate story target and inherited changes | D3; D6 | 2.5; 6.2 |
| R09 | Conservar archive/commit/push/PR aprobados y límites por proveedor | MD Canonical target bound authorization; contratos anteriores preservados | D3; D8; D12 | 2.6-2.8; 11.4 |
| R10 | Compatibilidad proporcional, informativa y opt-in | HC Optional target compatibility observation; MP Informative compatibility transition consumption | D3; D5; D8 | 6.1; 7.5 |
| R11 | Solapamientos de archivos, bajas, renombres e inventarios | HC Separate story target and inherited changes; PC Reference scoped cross revision reading | D6 | 6.2; 6.7 |
| R12 | Componentes y consumidores dependientes reutilizando contexto 0.1.7 | HC Dependency and consumer impact; PC Reverse consumer impact from existing component mappings | D6 | 6.3 |
| R13 | Contratos/reglas y contradicciones sin conflicto Git | HC Semantic review independent of textual conflicts | D5-D6 | 6.4 |
| R14 | Simular integración sin actualizar/fusionar ramas de trabajo | HC Isolated textual integration inspection; Bounded inspection and immutable report export | D4 | 5.4-5.6 |
| R15 | Cuatro categorías con motivos, acciones, responsables y límites | HC Actionable compatibility report | D5 | 6.1; 6.8 |
| R16 | Caso A: HU independientes continúan tras integración de HU001 | HC A independent concurrent stories | D6, tabla A | 6.6; 10.3 |
| R17 | Caso B: identificar contratos/checks de consumidor afectado | HC B changed consumed component; PT Catalog based target impact recommendations | D6-D7 | 6.5; 10.3 |
| R18 | Caso C: misma spec/regla incompatible exige reconciliación humana | HC C incompatible edits of one rule | D6, tabla C | 6.4; 10.3 |
| R19 | Caso D: Git limpio con contratos contradictorios | HC D contradictory contracts in different files | D6, tabla D | 6.4; 10.3 |
| R20 | Caso E: quality cambia y evidencia inicial queda desactualizada | HC Target freshness at PR preparation and creation | D5; D8 | 7.6; 10.3 |
| R21 | Caso F: rama ausente, inaccesible o no verificable | HC Missing and unverifiable target handling | D4-D6 | 5.1-5.3; 10.3 |
| R22 | Diferenciar base de nacimiento, base técnica y snapshot destino | HC Exact source and target anchors; MD Verified Git delivery provenance | D3-D6 | 2.4; 5.1; 6.2 |
| R23 | No rebase/merge resolutivo automático; acciones concretas al equipo | HC Human reconciliation and integration boundary | D4; D6-D7; D12 | 5.4; 6.8; 7.7 |
| R24 | Conservar evidencia/permisos intactos y no reiniciar rondas | HC Preserve valid evidence without cross plan adoption; MP Scoped invalidation and unchanged approvals | D7-D8 | 7.4-7.7 |
| R25 | Catálogo único y sin framework/runner/contexto nuevo | PT Catalog based target impact recommendations; PC Useful compatibility without context activation | D6-D7 | 1.5; 6.3; 6.5-6.6 |
| R26 | No afirmar validación combinada con pruebas solo de la feature | PT Distinct feature and combined candidate evidence | D7 | 6.8; 7.4; 10.3 |
| R27 | Enlazar informe canónico sin circularidad ni ocultar entradas funcionales | MP Canonical compatibility reference; Non circular compatibility evidence binding | D5; D8 | 7.1-7.4 |
| R28 | Sección C independiente y accesible aun sin prompt extenso | DL Persistent entry point independent of distribution prompt; MK Consistent portable setup documentation | D10-D12 | 4.1; 8.2; 9.2 |
| R29 | Detectar onboarding ya completo y evitar sobrescribirlo | DL Existing checkout and shared readiness; Preserve configured project resources | D10 | 4.2; 4.6 |
| R30 | Detectar SO/herramientas/dependencias e instalar solo lo autorizado | DL Applicable tools and authorized preparation | D10 | 4.2; 4.5 |
| R31 | Autenticaciones personales, MFA y permisos con intervención humana | DL Personal authentication and interactive authority | D9-D10 | 4.5; 4.7 |
| R32 | Comprobar acceso por lecturas seguras sin inferir permiso de escritura | DL Safe connection checks | D10 | 4.4; 4.7 |
| R33 | No reinstalar skills, init OpenSpec ni modificar modelos/reglas/specs | DL Preserve configured project resources | D10 | 4.6 |
| R34 | Configuración personal separada y Python absoluto por máquina | DL Bounded personal environment binding; PT Optional local execution environment resolution | D9 | 3.1-3.6 |
| R35 | Repetibilidad, diagnóstico y Windows sin cambiar ExecutionPolicy | DL Repeatable Windows preparation; Local diagnostic record and honest status; Side effect free default inspection | D10 | 4.2-4.3; 4.8; 10.5 |
| R36 | No contacto remoto o escrituras por inspección implícita | HC Bounded inspection and immutable report export; DL Side effect free default inspection | D4; D10 | 5.6; 6.1; 10.5 |
| R37 | Clasificar distribución/compartido/local e investigar consumidores | MK Explicit client installation composition | D11 | 8.1-8.2; 8.6 |
| R38 | Decidir Prompt, LEEME, manifest, VALIDACION y tests/crea con criterio | MK Preserve validation and provenance surfaces; Consistent portable setup documentation | D11; D13 | 8.2-8.3; 9.1-9.3 |
| R39 | Preservar licencias/NOTICE/upstream y archivos operativos | MK Explicit client installation composition; baseline de distribución | D11; D14 | 8.1-8.3; 9.4; 11.2 |
| R40 | Exclusiones incorporadas desde onboarding sin ocultar evidencia | MK Initial local exclusions without hidden changes | D11 | 8.4; 10.6 |
| R41 | Diferenciar copia/ignore/contexto/publicación; ya rastreado sigue rastreado | MK Separate copy context ignore and publication controls | D11 | 8.5-8.6 |
| R42 | Corregir referencias obsoletas sin alterar contratos o cifras históricas | MK Consistent portable setup documentation | D13 | 9.1-9.3 |
| R43 | Preservar kit 0.1.8 y trabajar en candidato nuevo único | MK Portable tooling release preserves customized source | D1; D13 | 1.2-1.3; 9.4; 10.7 |
| R44 | Adopción nueva/legacy, schemas/consumidores y rollback conjunto | MK Compatible reviewed team adoption and rollback; caminos opcionales DL/HC/PT | D9; Migration Plan | 3.6; 9.5; 10.6 |
| R45 | Conservar contexto/lifecycle opcionales e independientes | PC Useful compatibility without context activation; PT Selective rechecking within existing guarantees | D6-D9 | 6.6; 9.5; 10.4; 10.6 |
| R46 | Azure CLI, AI Tools/hooks, aprobaciones y capacidades inactivas intactos | MD Canonical target bound authorization; DL Preserve configured project resources; PT Selective rechecking within existing guarantees | D10; D14; Non-Goals | 2.7-2.8; 4.7; 10.4; 11.2 |
| R47 | Integración humana a quality y promoción a test fuera del harness | HC Human reconciliation and integration boundary; MD política por proveedor | D2; D12; Non-Goals | 11.4; Workflow follow-up |
| R48 | Plan priorizado y pruebas/regresiones proporcionales | Tasks 1-11 con dependencia, rol y verificación por tarea | D14; Migration Plan | Todas, con ejecución propia de Tester en 10 y revisión en 11 |
| R49 | Un solo cambio, aun extenso, y revisión final contra el chat | Proposal identifica un cambio; este informe complementa validación CLI | D1 | No requiere subdividir OpenSpec; tareas internas |
| R50 | Propose termina con artefactos, sin aplicar código | Scope de proposal/tasks y comprobación del diff | Context; Migration Plan | Workflow follow-up requiere nueva petición de Apply |

## Revisión de consistencia y precisiones incorporadas

La revisión adicional comprobó los siguientes puntos que el validador estructural por sí solo no demuestra:

1. La base de la feature no se sustituye por quality divergente: B, V, H y Q tienen funciones distintas y la historia heredada se presenta separada.
2. La vigencia de compatibilidad no equivale a vigencia de las pruebas locales. Los intentos nuevos conservan recibos intactos cuando procede, pero no se promete reutilización entre planes que el kit no soporta.
3. La simulación que crea objetos/temporales se separa de inspect puro y se ejecuta aislada; no se presenta como un comando sin efectos.
4. Las contradicciones funcionales requieren evidencia y revisión semántica; ni un diff textual ni Git limpio generan una aprobación funcional automática.
5. La resolución del binding se integra también en la reconstrucción/gate y en attempts, no solo al ejecutar. Sus campos efectivos participan en la huella técnica.
6. El opt-in tiene ubicación concreta `delivery.compatibility.enabled`, false por defecto, sin un segundo modo de enforcement o catálogo.
7. La preparación contrasta soporte efectivo de consumidores mediante identificación offline de contratos. Schema permisivo o número nominal de manifest no bastan.
8. Un diagnóstico offline no declara ready una continuación que exige lecturas personales pendientes. La ausencia de PyYAML/jsonschema produce diagnóstico útil mediante imports diferidos.
9. La guía/skill C permanece en el clon; sacar prompt/LEEME del perfil nuevo no rompe preparación, inventario o enlaces. En clientes existentes su retirada no es automática.
10. Las correcciones de 0.1.8 se expresan como fe de erratas y candidato siguiente, preservando los artefactos históricos y sus hashes.

## Límites y trabajo que sigue pendiente

- La cobertura de esta matriz corresponde al diseño y a las tareas, no demuestra que el kit ya ejecute estas capacidades.
- Todas las 74 tareas permanecen pendientes. No se ejecutaron fixtures A-F, suites de negocio, piloto de roles o una prueba real con dos desarrolladores durante Propose.
- No se instaló PyYAML u otra dependencia, no se autenticó, no se verificaron permisos remotos ni se publicó Git/PR/ZIP.
- La comprobación estricta de la propuesta usa el CLI OpenSpec y es independiente de la validación Python del kit, que quedó limitada en Explore por la dependencia ausente.
- Compatible será una conclusión acotada al snapshot y cobertura observados. La carrera entre lectura y cambios posteriores de quality continúa siendo responsabilidad del proceso de revisión/integración del equipo.
- La nueva proyección, resolución de entorno y composición requieren pruebas negativas y consumidores coordinados antes de adoptarse. Sus tareas están identificadas; un estado de planificación completo no las da por realizadas.

## Siguiente fase

Los artefactos quedan listos para revisión. Una nueva solicitud de `$openspec-apply-change` o de aplicar este cambio autoriza iniciar su implementación. Archivo, commit/push, creación de PR e integración conservan sus confirmaciones y límites vigentes.
