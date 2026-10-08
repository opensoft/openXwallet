# openxwallet-factory-binding

The openxFactory ADAPTER over a pinned neutral wallet standard. After
`split-openwallet-neutral-core`, `opensoft/openWallet` owns the standard and
needs no openxFactory input; openXwallet owns what binds that standard to
openxFactory — the pin of openWallet, the hermes approval-vocabulary binding,
the root-issuer operator anchor, and the composition that runs all of it, with
the register reader, inside the REQUIRED check of every repository that pins
openXwallet. The register reader keeps its own capability,
`review-authority-register-reader`, unchanged. This capability is NEW and every
requirement in it is ADDED.

## ADDED Requirements

### Requirement: openXwallet pins openWallet by commit and digest, declared twice, and composes its validator
openXwallet SHALL consume openWallet as a pinned neutral product, declared TWICE
in the same commit — a nested gitlink `openWallet/` mounting openWallet's
ASSEMBLY ROOT, and `contracts/openwallet-pin.yaml` recording the same 40-hex
root commit with `revision_kind: commit`, the commit of the code leg that root
pins held in lockstep with the root's own gitlink and leg pin, a per-file sha256
for each of the eight digested artifacts under that code leg, and
`pinned_by_commit_only:` for every other member it reads — and SHALL keep no
copy of any openWallet contract. Its entrypoint `scripts/validate-openxwallet.py`
SHALL run the PINNED openWallet validator, from the code leg of the pinned root,
in process over ONE scan context, with the adapter's rules registered at declared
extension points and never by editing, suppressing or reordering a core
finding, so that the composed run emits the same finding codes, notes and
summary line the pre-split validator emitted on the same tree. The entrypoint's
path, its single positional scan target, `--strict`, and the `wallet-validation`
check token SHALL survive the split unchanged, because consumers pin each of them
by string.

#### Scenario: A consumer's required check runs as it did before the split
- **WHEN** a consumer runs `scripts/validate-openxwallet.py` from its pinned openXwallet checkout over its own root
- **THEN** the invocation, the notes, the finding codes and the summary line are those the pre-split validator produced on that tree
- **AND** a neutrality run of both validators over the same tree MUST produce an empty diff, plain and under `--strict`, before any consumer's pin advances

#### Scenario: The nested checkout is missing
- **WHEN** the `openWallet/` gitlink or the code leg it mounts is not initialized, or the core module cannot be loaded from it
- **THEN** the entrypoint exits with a harness error naming the missing checkout level and its remediation
- **AND** it MUST NOT fall back to a self-test or a partial run that could report green

#### Scenario: The gitlink and the pin file disagree
- **WHEN** the recorded gitlink, the checked-out revision and `contracts/openwallet-pin.yaml` do not name one root commit, the code leg that root records disagrees with the pin's code-leg commit or with its own checkout, or a digested artifact's sha256 does not recompute
- **THEN** the pin verifier refuses BEFORE the validator runs, and the required check is red

#### Scenario: A copy of an openWallet contract is proposed for this repository
- **WHEN** a change would add a copy of an openWallet schema, registry or corpus member to this repository
- **THEN** it is refused, because a copy is a second answer to which bytes are current and the pin already answers it

### Requirement: The approval vocabulary is bound to the neutral job envelope, read from the digest-verified vendored copy
openXwallet SHALL supply the pinned validator its ONE vocabulary binding: the
keys of the hermes job envelope's `approval_policy` properties, read at run time
from `contracts/schemas/hermes-job-envelope.schema.yaml` only after
`scripts/verify-contract-pin.py` has verified that copy against
`contract_pin.yaml`. The binding SHALL be unconditional — no flag a caller can
omit — and the keys SHALL NOT be restated anywhere in this repository. A grant
whose approval posture names a key outside that set SHALL be refused under the
existing finding code `authority-vocabulary-parallel`, and an absent vendored
copy SHALL stop the run with a harness error rather than letting it proceed
unbound.

#### Scenario: A grant uses an envelope approval key
- **WHEN** a grant's `approval_posture` names only keys of the envelope's `approval_policy` properties
- **THEN** rule (g) admits the posture, and the run's vocabulary note names the vendored file and the keys read from it

#### Scenario: A grant invents an approval key
- **WHEN** a grant's `approval_posture` names a key the envelope does not declare
- **THEN** the grant is refused with `authority-vocabulary-parallel`, because a second authority vocabulary is what the requirement forbids

#### Scenario: The vendored envelope is mutated
- **WHEN** the vendored envelope's bytes no longer match `contract_pin.yaml`
- **THEN** the verify step fails before the validator reads the vocabulary, and the run is red

#### Scenario: The vendored envelope is absent
- **WHEN** `contracts/schemas/hermes-job-envelope.schema.yaml` does not exist
- **THEN** the entrypoint exits with a harness error, and MUST NOT run the pinned validator without a binding

### Requirement: The root-issuer operator anchor lives in the adapter, not in the neutral standard
openXwallet SHALL enforce, as an adapter rule over the grant records the pinned
validator adjudicates, openxFactory's `review-authority-intake` requirement that
every review-authority grant names its issuer and that a ROOT review-authority
grant's issuer is the anchored responsible operator, exact-match and never
normalized — rule (t), its constants, its self-test probes, and its three
standing negative fixtures attributed to `OXWR-R1` and `OXWR-R2` — and SHALL
carry the finding codes `issuer-unrecorded` and `root-issuer-unanchored`
unchanged. openWallet SHALL carry none of it, because an organisation's operator
identity is not a property of the neutral standard. The adapter's negatives SHALL
join the per-requirement coverage closure, so each of `OXWR-R1` and `OXWR-R2`
keeps a probe that fails on the violation it exists to catch.

#### Scenario: A review-class grant names no issuer
- **WHEN** a grant whose scope acts include the review act token carries no `issued_by`
- **THEN** the composed run refuses it with `issuer-unrecorded`

#### Scenario: A root review-class grant names a machine or the legacy organisation string
- **WHEN** a review-class grant with no `parent_grant_ref` names a machine-shaped issuer, the legacy organisation string, or any value other than the anchored operator
- **THEN** the composed run refuses it with `root-issuer-unanchored`, worded for the branch that fired

#### Scenario: The same grant is validated by openWallet standalone
- **WHEN** a review-class grant with no issuer is validated by the pinned openWallet validator with no adapter composed
- **THEN** openWallet raises no issuer finding, because the neutral standard imposes no operator anchor
- **AND** the anchor binds only where openXwallet composes it

#### Scenario: An anchor probe is deleted
- **WHEN** one of the three issuer-anchor negatives is removed or its detail pin stripped
- **THEN** the composed self-test reds, because each branch of the anchor keeps its own named, pinned probe

### Requirement: Record kinds, finding codes and schema identifiers are the pinned openWallet's, unchanged — the prefix is kept
openXwallet SHALL adjudicate exactly the record kinds, finding codes and schema
`$id`s of the openWallet commit it pins. The `xfactory_wallet_*` kind prefix,
every finding code, and the schema `$id` namespace under
`https://xforge.us/schemas/openxfactory/` SHALL be KEPT unchanged through the
split — RULED by Brett Heap, 2026-10-08, "keep the prefix" — and the adapter
SHALL NOT alias, translate, or add a second spelling of any of them. A rename to
a neutral prefix is a future wallet MAJOR and is out of this capability's scope.

#### Scenario: A consumer pins a kind and a finding code by name
- **WHEN** a consumer's records carry `kind: xfactory_wallet_grant` and its gate asserts on a finding code string
- **THEN** both are adjudicated and emitted exactly as before the split

#### Scenario: An alias for a kind or a code is proposed
- **WHEN** a change would admit a second spelling of a kind, a finding code or a schema `$id` in the adapter
- **THEN** it is refused, because two spellings of one machine key is a rename by other means and the prefix is ruled kept

#### Scenario: The adapter's own codes
- **WHEN** the adapter emits a rule (t) or register-reader finding
- **THEN** its code is the string it carried before the split, because the adapter moved no code

### Requirement: A consumer reaches openWallet through openXwallet's declared pin, and a direct pin suffices standalone
A repository that consumes the wallet through openXwallet SHALL reach openWallet's
commits — its assembly root's and, through that root, its code leg's — ONLY
through openXwallet's declared pin, which is the transitive commit
and is DERIVED rather than declared a second time; a `<Domainx>Wallet` SHALL
classify as a domain descendant where its declared neutral-product pins REACH
`openWallet` through such a chain, as the 2026-09-05 pin-chain ruling recorded in
openxFactory `docs/project-repo-schema.md` provides. A repository that consumes
openWallet standalone, with no factory, SHALL pin openWallet's assembly root
directly and SHALL
inherit no rule this capability or `review-authority-register-reader` adds. A
repository that declares openWallet's commit both directly and through
openXwallet SHALL hold the two equal by a running check, because two unreconciled
answers to which bytes are pinned is no answer.

#### Scenario: openxFactory asks which openWallet bytes it runs
- **WHEN** openxFactory resolves the core validator and the eight digested artifacts
- **THEN** it reads them inside that root's code leg, under its pinned openXwallet checkout at `openXwallet/openWallet/code/`, at the commits openXwallet's own pin records, and declares no openWallet commit of its own, root or leg

#### Scenario: A domain wallet pins the adapter
- **WHEN** a `<Domainx>Wallet` declares a pin on openXwallet and openXwallet's pin declares openWallet
- **THEN** it classifies as a descendant through that chain, and its tuned behaviour is the pin it chose, never a fork

#### Scenario: A standalone product pins openWallet
- **WHEN** a product outside the factory pins openWallet directly
- **THEN** it runs the neutral standard with no register reader, no operator anchor and no hermes binding, and declares its own vocabulary binding if it uses approval postures

#### Scenario: One repository declares the commit twice
- **WHEN** a repository pins openWallet directly AND reaches it through openXwallet
- **THEN** a running check holds the two commits equal, and the repository's required check is red the moment they disagree
