# openxwallet Specification Delta

## MODIFIED Requirements

### Requirement: A wallet is a key, never a record of a key

openXwallet SHALL define a neutral wallet as a signing key — or a declared SET
of signing keys — anchored to decentralized identifiers and held by a HOLDER,
where a holder is any subject class the family recognises: a person, a
practitioner, an organisation, or an agent. The wallet is identified by the SET
of keys it declares, and every key in that set is one the HOLDER holds, so a
wallet declaring several keys is still never a record of SOMEONE ELSE'S key.
The wallet record carries the holder's identifier, a reference to each key it
declares, and each declared key's own custody model; it never carries key
material, and no capability may require key material to be disclosed to it. A
record declaring one key is a set of one and is conformant unchanged. A
declared key's declaration is APPEND-ONLY: retiring a key is a change to that
key's declared state, never a deletion of its declaration, because an act
already attributed to a key must remain readable after the key is retired.

#### Scenario: the record references, never contains

- WHEN a wallet record is validated
- THEN it carries a key reference and a declared custody model
- AND a record containing private key material is a validation failure

#### Scenario: holders are not restricted to one subject class

- WHEN a domain declares a wallet holder
- THEN the holder may be a person, practitioner, organisation, or agent
- AND no requirement in this capability assumes a particular class

#### Scenario: several keys present one authority

- WHEN a wallet declares more than one key
- THEN each declared key carries its own custody model and its own fingerprint
- AND the wallet's authority is unchanged by how many keys present it
- AND a key declared by that wallet is a key its own holder holds, never a
  record of another holder's key

#### Scenario: a retired key stays declared

- WHEN a declared key is retired
- THEN its declaration remains in the record with its state changed
- AND deleting the declaration is refused as a way to retire a key
- AND every act already attributed to that key remains resolvable

#### Scenario: a single-key record is a set of one

- WHEN a wallet record declares only its primary key reference
- THEN the record is conformant with no additional declaration
- AND its declared key set is that one key
- AND every rule keyed on the declared set resolves to the behaviour it had
  before sets were expressible

### Requirement: Custody is declared and bounds what a signature evidences

openXwallet SHALL require every wallet to declare a key-custody model from a
closed set FOR EVERY KEY IT DECLARES, SHALL state what each model evidences,
and SHALL cap the authority a wallet may hold by that model. A signature proves
only what the custody OF THE KEY THAT SIGNED permits: a key readable by the
holder's own execution context evidences that the ENVIRONMENT acted, and only
custody isolating the key from that context evidences that the HOLDER acted.
These SHALL NOT be presented as equivalent. Because a declared key PRESENTS the
wallet's authority and is never a source of more of it, no declared key's
custody ceiling may outrank the wallet's own.

#### Scenario: custody caps authority

- WHEN a wallet requests authority beyond what its custody model evidences
- THEN the request is refused with the custody ceiling named
- AND raising authority requires changing custody, not asserting trust

#### Scenario: the audit says what was evidenced

- WHEN an act is audited
- THEN the record carries the custody model in force at the time
- AND a reader can tell whether the holder or its environment was evidenced

#### Scenario: the presenting key's custody is the model in force

- WHEN an exercise records a custody model in force
- THEN that model is the one declared for the key that presented the grant
- AND a model belonging to another of the same wallet's keys is a validation
  failure
- AND an act may not claim evidence the presenting key's custody cannot supply

#### Scenario: a declared key never raises the wallet's cap

- WHEN a wallet declares a key whose custody ceiling outranks the wallet's own
- THEN the record is refused with both ceilings named
- AND raising the wallet's authority remains a question about the wallet's
  custody, never about adding a stronger key beside it

### Requirement: Every exercise is key-attributed

openXwallet SHALL record, for every exercise of a grant, the key that presented
it alongside the grant and the act, so attribution is cryptographic rather than
inferred from a shared account. An act attributable only to a shared credential
SHALL be recorded as unattributed rather than assigned to a holder. The
presenting key SHALL be one of the keys the audience wallet DECLARES — its
declared key SET, not its primary key alone — and a wallet SHALL NOT declare one
key identifier twice, because a duplicated identifier makes the key an exercise
resolves to depend on which declaration is read last.

#### Scenario: shared credentials do not launder attribution

- WHEN an act reaches an external platform through a shared service credential
- THEN the presenting wallet key is recorded as the actor
- AND the shared credential is recorded as transport, never as the actor

#### Scenario: an unattributable act says so

- WHEN no wallet key can be established for an act
- THEN the act is recorded as unattributed
- AND it is not assigned to a holder on the strength of the credential used

#### Scenario: the presenting key is in the declared set

- WHEN a verified exercise names the key that presented its grant
- THEN that key is one of the keys the audience wallet declares
- AND a presenting key outside every wallet's declared set is refused rather
  than passed over
- AND the act is attributed to the wallet declaring that key, whichever of its
  keys signed

#### Scenario: a key identifier is declared once per wallet

- WHEN a wallet declares the same key identifier more than once
- THEN the record is refused naming the repeated identifier
- AND the duplicate is not resolved by declaration order

### Requirement: Revocation propagates through the chain

openXwallet SHALL make revocation effective through derivation: revoking a
grant revokes everything derived from it, and revoking a holder's standing
revokes that holder's outstanding grants, in both cases without waiting for
expiry. A capability consuming grants SHALL check revocation at exercise
rather than trusting issuance. Retiring one DECLARED KEY of a wallet SHALL
stop that key presenting the wallet's authority without revoking the wallet
itself or the authority its other declared keys still present, and that
retirement SHALL be checked at exercise for the same reason every other
revocation is.

#### Scenario: revoking a parent kills the chain

- WHEN a grant is revoked
- THEN every grant derived from it is revoked at the same moment
- AND an exercise attempt against any of them is refused

#### Scenario: revocation is checked at use

- WHEN a grant is exercised after its holder's standing was revoked
- THEN the exercise is refused
- AND issuance-time validity is not accepted as evidence of current validity

#### Scenario: retiring one key does not revoke the wallet

- WHEN one declared key of a wallet is retired
- THEN an exercise permitted under that key is refused
- AND the wallet's other declared keys continue to present its authority
- AND the wallet's own standing is unchanged by the retirement
