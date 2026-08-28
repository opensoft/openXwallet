# openxwallet-agent-profile Specification (delta)

## MODIFIED Requirements

### Requirement: A composition change revokes the agent's grants immediately

openXwallet SHALL treat any change in an agent's declared composition as the
end of that agent's certified identity: its outstanding grants are revoked at
once through the core's revocation-propagation rule, with no tolerance band
and no grace period, and resuming requires re-issuance against the changed
composition. This generalizes to AUTHORITY an invalidation the family already
applies to OUTPUTS — a prompt-contract version bump invalidated every prior
classification, because a judgment by prompt-v1 is not the same classifier's
judgment.

The revocation a composition change causes SHALL carry reason class DRIFT,
and SHALL cascade through derivation under the core's rule exactly as a
CAUSE-class revocation does. Derived authority never survives an unattested
drift: an agent whose composition moved cannot leave behind a narrower
derived grant that keeps acting on the strength of the identity that ended.

A declared change is a DECLARATION and SHALL NOT stand in place of the
revocation itself. The holder's outstanding grant records MUST carry the
revoked state, each with a revocation naming the composition event that
caused it; a composition record that declares the change while any grant to
that wallet remains active is a validation failure. A composition record
being consistent with itself is not evidence that authority actually ended.

Resuming authority SHALL require an EXPLICIT, HUMAN-RATIFIED issuance act
against the changed composition. No automatic reissue, and no standing
reissue policy that acts on its own, may restore authority: the act is
performed afresh each time, by a named human, against the composition then
declared.

A declared model component SHALL name an EXACT version. A model family, an
alias, or any other moving reference is not a pin and is a validation
failure, because a reference that resolves differently over time defeats the
hash it is declared into.

#### Scenario: a changed agent is a different agent

- WHEN an attested composition hash differs from the declared hash
- THEN the agent's outstanding grants are revoked at that moment
- AND an exercise attempt against any of them is refused

#### Scenario: declared change is not a percentage

- WHEN any single component of the declared set changes
- THEN the change alone is sufficient to revoke
- AND no threshold, score, or tolerance band is consulted

#### Scenario: drift cascades to derived grants

- WHEN a composition change revokes an agent's grant with reason class DRIFT
- THEN every grant derived from it is revoked at the same moment
- AND no derived grant survives on the grounds that the revocation was drift rather than cause

#### Scenario: declaring the change is not performing it

- WHEN a composition record declares that a change revoked the holder's grants
- THEN every outstanding grant to that wallet carries the revoked state with a revocation naming the composition event
- AND a declaration standing alongside an active grant to that wallet is a validation failure

#### Scenario: resumption is a ratified act, never a policy

- WHEN authority is to resume after a composition change
- THEN a named human ratifies an issuance act against the changed composition
- AND an automatic or standing reissue that restores authority without that act is refused

#### Scenario: a model family is not a pin

- WHEN a declared model component names a family or an alias rather than an exact version
- THEN the declaration is a validation failure
- AND no resolution of that family at declaration time is accepted in place of the exact version
