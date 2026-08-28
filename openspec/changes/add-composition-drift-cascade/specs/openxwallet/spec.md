# openxwallet Specification (delta)

## MODIFIED Requirements

### Requirement: Revocation propagates through the chain

openXwallet SHALL make revocation effective through derivation: revoking a
grant revokes everything derived from it, and revoking a holder's standing
revokes that holder's outstanding grants, in both cases without waiting for
expiry. A capability consuming grants SHALL check revocation at exercise
rather than trusting issuance.

Every revocation SHALL record a REASON CLASS, and the class is recorded but
NEVER consulted to narrow propagation: a revocation classed DRIFT — an
unattested change in what the holder is — propagates through derivation
exactly as one classed CAUSE does. The class is evidence about why authority
ended; it is never a gate on how far the ending reaches, so no derived
authority survives on the strength of its parent's reason.

Every propagated revocation SHALL record the edge it descends from, naming
the grant or the holder standing whose revocation reached it, so the chain is
inspectable from any point in it rather than inferred by re-walking
derivation.

A revoked grant SHALL NEVER return to the active state. Authority resumes
only as a NEW grant, which records the grant it supersedes and the holder
composition or standing it was issued against. A revocation is therefore a
terminal fact about that grant rather than a suspension of it.

A propagation that leaves a holder with NO active standing SHALL be surfaced
to the responsible human through the consuming capability's declared
escalation path, and SHALL NOT be discharged by a log line alone. openXwallet
states the obligation and names no mechanism: which packet, which channel and
which human are the consuming capability's to declare.

#### Scenario: revoking a parent kills the chain

- WHEN a grant is revoked
- THEN every grant derived from it is revoked at the same moment
- AND an exercise attempt against any of them is refused

#### Scenario: revocation is checked at use

- WHEN a grant is exercised after its holder's standing was revoked
- THEN the exercise is refused
- AND issuance-time validity is not accepted as evidence of current validity

#### Scenario: a drift revocation cascades exactly like a cause revocation

- WHEN a grant is revoked with reason class DRIFT
- THEN every grant derived from it is revoked at the same moment, exactly as for reason class CAUSE
- AND the reason class is recorded on each revocation but is never consulted to spare a derived grant

#### Scenario: a propagated revocation names its origin

- WHEN a revocation reaches a grant by propagation rather than by a direct act
- THEN that grant's revocation record names the grant or holder standing it descended from
- AND a propagated revocation carrying no origin is a validation failure

#### Scenario: a revoked grant is never reactivated

- WHEN authority is to resume for a holder whose grant was revoked
- THEN a new grant is issued recording the grant it supersedes and what it was issued against
- AND returning the revoked grant to the active state is refused

#### Scenario: a holder left with no active standing reaches a human

- WHEN propagation leaves a holder with no active grant and no active standing
- THEN the consuming capability raises it to the responsible human through its declared escalation path
- AND recording the event only in a log does not discharge the obligation
