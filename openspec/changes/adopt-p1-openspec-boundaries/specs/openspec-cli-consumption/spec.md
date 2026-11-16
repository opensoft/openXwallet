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

### Requirement: Reproduce source validation on published main

The consumer SHALL expose the existing source validation job for a manual
refs/heads/main run and SHALL refuse every other manual ref before checkout
or private dependency access. It SHALL retain the existing PR eligibility,
immutable dependencies and complete source/conformance checks.

#### Scenario: A published-main verification is requested
- WHEN a manual source run selects refs/heads/main
- THEN the existing source validation job qualifies that exact main commit.

#### Scenario: A manual caller selects another ref
- WHEN the selected ref is another branch, a tag or empty
- THEN the first guard fails before dependency access.

#### Scenario: The original PR route is used
- WHEN the original PR trigger matches
- THEN its existing selectors and fork refusals remain effective.
