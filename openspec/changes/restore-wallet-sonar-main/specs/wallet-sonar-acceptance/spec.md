## ADDED Requirements

### Requirement: Complete source acceptance
The maintenance analysis SHALL retain its complete source scope, all six existing Sonar way conditions, existing runtime matrix and real executed-test coverage. No rule suppression, threshold reduction, false coverage, billing change or operational activation is permitted.

#### Scenario: Published main acceptance
- **WHEN** the repair is merged
- **THEN** the recorded main revision SHALL have a completed analysis with the justified retained baseline, evaluated coverage, and unchanged gate conditions.

### Requirement: Owned and reproducible repairs
Shared files SHALL be fixed at their owners, consumed through coherent immutable pins and verified provenance, and original findings SHALL close through source analysis.

#### Scenario: Consumer propagation
- **WHEN** provider repairs are accepted
- **THEN** the consumer SHALL verify compatible pins, actual provider bytes and the eight original finding keys.

### Requirement: Preservation
The repair SHALL preserve active sessions, unrelated worktrees, historical commits, immutable tags, example identities and refusal semantics.

#### Scenario: Credential-shaped negative example
- **WHEN** current fixture bytes are replaced
- **THEN** deliberately invalid synthetic private material SHALL still trigger the existing refusal, while old history is retained without live credential use.
