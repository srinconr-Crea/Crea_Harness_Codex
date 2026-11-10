# Catalogo de skills

## 1. OpenSpec y coordinacion
crea-orquestador: .agents/skills/Crea/orquestador/SKILL.md.
Planner usa openspec-explore, openspec-propose, openspec-update-change.
Developer usa openspec-apply-change. Reviewer usa openspec-verify-change,
openspec-sync-specs y openspec-archive-change. Son siete snapshots generados por OpenSpec 1.13.2;
init/update desde la CLI instalada es la via de mantenimiento. No hay cambio de negocio incluido.

## 2. Databricks AI Tools portables — 28 skills
Revision y hashes: docs/skills-procedencia.json y resources/databricks-aitools/upstream-lock.json.
Una copia activa por nombre; seleccionar solo capacidades pertinentes a la HU.

| Skill | Cuando usarla |
| --- | --- |
| databricks-ai-functions | Use Databricks built-in AI Functions (ai_classify, ai_decide, ai_extract, ai_summarize, ai_mask, ai_translate, ai_fix_grammar, ai_gen, ai_analyze_sentiment, ai_similarity, ai_parse |
| databricks-aibi-dashboards | Create Databricks AI/BI dashboards. Must use when creating, updating, or deploying Lakeview dashboards as Databricks Dashboard have a unique json structure. CRITICAL: You MUST test |
| databricks-app-design | Design the UX of custom-code Databricks Apps (AppKit/React) data screens — KPI/overview pages, reports, charts, tables, and Genie/chat data assistants — mapped to concrete AppKit c |
| databricks-apps | Build apps on Databricks Apps platform. Use when asked to create data apps, analytics tools, or custom interactive visualizations. A plain "create a dashboard" request means a mana |
| databricks-apps-python | Python backend for Databricks Apps — FastAPI (default), Flask, Dash, Streamlit, Gradio, Reflex. **Default for a new Databricks App is `databricks-apps` (AppKit — Node/TypeScript/Re |
| databricks-core | Databricks CLI operations and the parent/entry-point skill for Databricks CLI use: authentication, profile selection, and bundles. Load this first for CLI, auth, profile, and bundl |
| databricks-dabs | Create, configure, validate, deploy, run, and manage Declarative Automation Bundles (DABs, formerly Databricks Asset Bundles). Use when working with Databricks resources via DABs i |
| databricks-data-discovery | Discover, explore, and query Databricks data via Genie — the CLI equivalent of the Genie One MCP. MUST be invoked whenever the user asks to find or locate data ('what tables are in |
| databricks-dbsql | Databricks SQL (DBSQL) advanced features and SQL warehouse capabilities. This skill MUST be invoked when the user mentions: "DBSQL", "Databricks SQL", "SQL warehouse", "SQL scripti |
| databricks-docs | Databricks documentation reference via llms.txt index. Use when other skills do not cover a topic, looking up unfamiliar Databricks features, or needing authoritative docs on APIs, |
| databricks-execution-compute | Execute code and manage compute on Databricks: run Python/Scala/SQL/R via serverless, classic, or interactive clusters, and create/resize/delete clusters and SQL warehouses. |
| databricks-genie-agents | Create, manage, and query Databricks Genie Agents (formerly Genie Spaces): curated agents over Unity Catalog tables, Metric Views, and documents in UC volumes. Use when building, m |
| databricks-jobs | Develop and deploy Lakeflow Jobs on Databricks via DABs, Python SDK, or the CLI. Use when creating data engineering jobs with notebooks, Python wheels, SQL, dbt, or pipelines. Invo |
| databricks-lakebase | Databricks Lakebase Postgres: projects, scaling, connectivity, Lakebase synced tables, and Data API. Use when asked about Lakebase databases, OLTP storage, or connecting apps to Po |
| databricks-lakeflow-connect | Build managed ingestion pipelines into Databricks using Lakeflow Connect. Use when ingesting from SaaS apps (Salesforce, Workday Reports, ServiceNow, Google Analytics 4, HubSpot, C |
| databricks-metric-views | Unity Catalog metric views: define, create, query, and manage governed business metrics in YAML. Use when building standardized KPIs, revenue metrics, order analytics, or any reusa |
| databricks-mlflow-evaluation | MLflow GenAI evaluation and agent improvement on Databricks. Use when running mlflow.genai.evaluate(), building scorers or datasets, aligning judges with MemAlign, optimizing promp |
| databricks-mlflow-tracing | MLflow tracing and observability on Databricks. Use when getting started with MLflow, instrumenting GenAI apps and agents, retrieving and analyzing traces, debugging chat sessions, |
| databricks-model-serving | Databricks Model Serving endpoint lifecycle and ops. Use when asked to: CRUD serving endpoints (CLI or MLflow Deployments client); configure traffic routing for A/B / canary deploy |
| databricks-pipelines | Develop Lakeflow Spark Declarative Pipelines (formerly Delta Live Tables) on Databricks. Use when building batch or streaming data pipelines with Python or SQL, including Auto CDC  |
| databricks-python-sdk | Databricks development guidance including Python SDK, Databricks Connect, CLI, and REST API. Use when working with databricks-sdk, databricks-connect, or Databricks APIs. |
| databricks-sandbox | Databricks Sandbox: on-demand serverless compute for running untrusted or agent-generated code and background tasks. Create/start/stop/delete sandboxes, run commands (synchronous e |
| databricks-serverless | Serverless compute for Databricks jobs, Lakeflow pipelines and Declarative Automation Bundles (DABs), with STANDARD or PERFORMANCE_OPTIMIZED and classic only where serverless canno |
| databricks-spark-structured-streaming | Comprehensive guide to Spark Structured Streaming for production workloads. Use when building streaming pipelines, working with Kafka ingestion, implementing Real-Time Mode (RTM),  |
| databricks-synthetic-data-gen | Generate realistic synthetic data using Spark + Faker (strongly recommended). Supports serverless execution, multiple output formats (Parquet/JSON/CSV/Delta), and scales from thous |
| databricks-unity-catalog | Unity Catalog governance, access control, and observability. Use to grant or revoke access (GRANT/REVOKE), reason about the privilege model and ownership, set up row-level security |
| databricks-unity-gateway | Use when querying or calling pay-per-token foundation models, or when creating, updating, listing, or querying Unity Gateway (also called Unity AI Gateway) services, including mode |
| databricks-vector-search | Databricks AI Search (formerly Vector Search) endpoints and indexes for RAG and semantic search. Use when asked to: create Standard or Storage-Optimized endpoints and Delta Sync or |

## 3. Complementos incluidos
| Skill | Justificacion |
| --- | --- |
| databricks-jobs | Workflows y tareas de ingenieria de datos. |
| databricks-pipelines | Pipelines declarativos. |
| databricks-python-sdk | Automatizacion con SDK Python. |
| databricks-synthetic-data-gen | Fixtures sinteticos para desarrollo. |
| databricks-mlflow-evaluation | Evaluacion ML/GenAI cuando aplique. |
| databricks-docs | Consulta de documentacion especializada. |
| databricks-data-discovery | Descubrir/consultar datos con Genie; requiere CLI/capacidad compatibles. |
| databricks-apps | Apps AppKit/TypeScript; complementa apps-python. |
| databricks-app-design | Diseno de las Apps; referencias completas. |

Las seis primeras provienen del snapshot ya guardado por el harness; las tres ultimas
del paquete Codex upstream fijado por commit en skills-procedencia.json. Se corrige un unico enlace relativo roto de apps, documentado en patches; las instrucciones se conservan.
La skill propia creating-databricks-agents esta en Crea/creating-databricks-agents y sirve
para Apps que hospedan agentes; no configura los subagentes locales del kit.

## 4. Dependencias opcionales y compatibilidad
Se copian todas las referencias/scripts/assets de cada skill seleccionada. Las menciones a
otras especialidades no incluidas (por ejemplo Lakebase, entrenamiento ML, Vector Search o
dashboards) son rutas opcionales: instalarlas antes de seguir esos flujos, no fingir su presencia.
Las skills tienen versiones/minimos distintos. databricks-data-discovery menciona CLI >=1.9.0
para genie ask; si tu CLI no lo ofrece, seguir su comprobacion/fallback documentados. No asumir
que instalar la ultima CLI garantiza que tu workspace tenga todas las capacidades.

## 5. Configuracion y extensiones
Mantener upstream intacto; registrar overrides en Project y contexto. Para quitar una skill,
revisar dependencias y workflow.skills_by_role. Las skills globales instaladas con igual name
pueden aparecer duplicadas: elegir una fuente o desactivar la global en la configuracion personal.
No introducir datos propios de un cliente en las skills comunes ni en licencias.

## 6. Pruebas deterministas 0.1.4

crea-pruebas: .agents/skills/Crea/crea-pruebas/SKILL.md. Paquete completo 0.1.0
integrado con metadata UI, referencias, assets y helper; adaptaciones en
docs/pruebas/INTEGRACION.json. Planner planifica, Developer implementa tests,
Tester ejecuta y Reviewer evalua cobertura/recibos. No instalacion global.
Resolver nombres registrados en extensions.skills antes de convencion upstream.

## 7. Azure DevOps CLI
crea-azure-devops-cli: Crea/azure-devops-cli/SKILL.md. Planner/Reviewer leen HU/comentarios con solicitud y evidencia; principal mantiene entrega anterior. Ayuda disponible no habilita pipelines o escrituras futuras de work items. Ver azure-devops-cli.md.

## Preparación local de desarrollador
crea-preparar-desarrollador: `.agents/skills/Crea/preparar-desarrollador/SKILL.md`.
Usar para sección C o segunda máquina; no onboarding, actualización del kit o HU.
