# Spec Delta

## Purpose

Asistente y plantillas de configuración con descubrimiento, revisión y aplicación explícita. Permite desarrollo supervisado y verificable desde Codex Desktop manteniendo separadas configuración, permisos y evidencia de cada cliente.

## ADDED Requirements

### Requirement: Interview or configuration file

El asistente SHALL aceptar plantilla o entrevista, descubrir hechos locales y preguntar solo decisiones faltantes con procedencia. MUST NOT inventar permisos, perfiles, hosts o reglas de negocio.

#### Scenario: Complete template
- **WHEN** el usuario aporta campos suficientes validados
- **THEN** presenta un preview sin repetir preguntas contestadas

#### Scenario: Ambiguous target
- **WHEN** no se identifica checkout cliente de forma única
- **THEN** pide selección y no aplica cambios

### Requirement: Separate portable and local configuration

El producto SHALL conservar descriptor/política/binding v1 y validar contratos adicionales para contexto/roles/validación y conexiones locales sin secretos.

#### Scenario: New selections
- **WHEN** se seleccionan rol y validación para el cliente
- **THEN** los guarda en contrato separado y conserva v1

#### Scenario: Credential input
- **WHEN** una respuesta contiene token o password
- **THEN** rechaza/redacta la entrada sin persistir secreto

### Requirement: Staged preparation and certification

El asistente SHALL orquestar preparación e integración mediante plan explícito y registrar etapas, recuperación y estado preparado/certificado/remoto pendiente. SHALL conservar el contrato init v1 y usar preparación compuesta separada cuando instrucciones personalizadas impidan reutilizarlo.

#### Scenario: Successful local stages
- **WHEN** preparación e integración terminan y falta acceso remoto
- **THEN** informa prepared y remote_not_checked sin afirmar conectividad

#### Scenario: Interrupted integration
- **WHEN** falla integración después de preparar archivos
- **THEN** conserva journal por etapa y propone recuperación sin rollback total ficticio

#### Scenario: Custom AGENTS preserved
- **WHEN** init v1 rechaza instrucciones existentes personalizadas
- **THEN** conserva ese rechazo y presenta un plan compuesto nuevo que preserva dichas instrucciones y revisa cualquier integración, sin aplicar el plan v1 conflictivo

### Requirement: Side effect free preview

El producto SHALL ofrecer preview sin editar target, estado, configuración global ni sistemas remotos. Exportación explícita SHALL crear solo el plan externo solicitado mediante creación exclusiva.

#### Scenario: Preview snapshot
- **WHEN** se solicita preview sin exportación
- **THEN** conserva snapshots y no ejecuta escritura o autenticación

#### Scenario: Existing export destination
- **WHEN** el destino de exportación existe o está enlazado
- **THEN** rechaza sin sobrescribir o redirigir archivos
