## MODIFIED Requirements
### Requirement: A consumer runs provider-owned integrity-verified tooling
The consumer SHALL preserve provider byte identity and full artifact/closure
verification, and SHALL refuse untrusted executable, input and cache selection.

#### Scenario: A model chooses a forged pin
- **WHEN** a CLI operand differs from the independently configured pin authority
- **THEN** execution refuses before fetching or installing any package

#### Scenario: The fixed CLI validates the consumer corpus
- **WHEN** the pinned tool validates all items
- **THEN** every item runs with strict validation and existing failures stay visible
