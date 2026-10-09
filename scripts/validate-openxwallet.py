#!/usr/bin/env python3
"""Validate the openxWallet contract families: openXwallet's ADAPTER over the
pinned neutral core (split-openwallet-neutral-core, design.md D5).

The neutral standard's validator, its two contract families and its packaged
corpus are openWallet's. This file runs them IN PROCESS from the pinned
checkout, `openWallet/code/scripts/validate-openxwallet.py`, path-loaded with
`importlib` (the pattern scripts/wallet-yaml-syntax-gate.py has always used),
so the core's own ROOT resolves to `openWallet/code/` and its corpus, schemas,
custody registry and corpus binding resolve inside the pinned code leg with no
path edit (RULED Q1, "In-process, extension points"; RULED Q7). The invocation
does not move:

    python3 scripts/validate-openxwallet.py [REPO_PATH] [--strict]

What openXwallet adds is registered at the core's declared EXTENSION POINTS
before the core's main() runs, and nothing else is touched:

  GRANT_RULES           rule (t), inside check_grant after the tier lookup and
                        before rule (e), where it always ran
  REQUIREMENTS          the OXWR-R1 / OXWR-R2 rows rule (t)'s negatives probe
  SELF_TEST_HOOKS       rule (t)'s three negatives, which stay HERE at
                        contracts/openxwallet/examples/negative/grant-review-*,
                        adjudicated and joined to the corpus count and the
                        per-requirement closure; then the boundary guard, the
                        anchor probes and the S2 named probes
  SELF_TEST_TAIL_HOOKS  the S4 register-reader self-test, after the corpus note
  TREE_CHECKS           check_register, rule (u), at the end of a directory
                        sweep, over the scan's own context

The core never imports this file, and this file never suppresses, rewrites or
reorders a core finding. What that buys is NEUTRALITY BY CONSTRUCTION, over
three kinds of tree (design.md D5, as amended 2026-10-09): over this
repository's own tree, an export of openxFactory's live `governance/` tree and
every fixture tree the test suites build, this run's output is byte-identical
to the pre-split validator's at the carve commit
90111df262d6f54f7e82651d860adc12345f83f4. The composed corpus note reads
21 / 45 / 13 of 13, where the core alone reads 21 / 42 / 11 of 11.

THE VOCABULARY BINDING IS UNCONDITIONAL. Rule (g) admits as approval-posture
terms exactly the keys of ONE DECLARED BINDING (RULED Q6, "Document plus
pointer, fail closed"). This entrypoint binds the canonical job envelope,
`contracts/schemas/hermes-job-envelope.schema.yaml` at
`properties.job.properties.approval_policy.properties`, with no flag a caller
can omit. The envelope is vendored at a digest pin (contract_pin.yaml, checked
by scripts/verify-contract-pin.py before this runs), and its absence is the
hard exit it always was.

FAIL CLOSED FIRST. An uninitialized `openWallet/`, an uninitialized
`openWallet/code/`, or a core that does not load (or loads without the names
this file composes against) is exit 2 under a named refusal, with that level's
remediation, before anything is adjudicated. A self-test-only green from a
validator that could not find its core would be the vacuous pass this family
exists to refuse. WHICH commit is checked out is
scripts/verify-openwallet-pin.py's question, and the gate asks it first.

The rules openXwallet carries, which the neutral standard does not:

  (t) THE ISSUER IS RECORDED AND ROOTS ARE ANCHORED. A REVIEW-class grant —
      membership decided by scope content alone: the canonical review act
      token appearing in scope.acts — names issued_by, and a ROOT such grant
      (no parent_grant_ref) names no issuer but the responsible operator,
      exact-match, no normalization. A root issuer's authority to issue cannot
      be conferred by the register the grant writes into; it is standing under
      the Human Escalation Contract, which the anchor constant cites rather
      than restates. Machine-named issuers are refused with their own wording,
      and the legacy org string every pre-S2 example carries does NOT
      grandfather into the anchor (review-authority intake).

  (u) THE REGISTER AND ITS READER RATIFY TOGETHER, AND A GRANT WITHOUT AN
      ACTIVE ROW CONFERS NOTHING. When the scanned tree carries an intake
      register (`governance/review-authority/register.yaml`), every row must
      resolve: its wallet live and active, its grant indexed, matching in
      audience/act/tier/expiry, and NOT expired by COMPUTED time — the stored
      `state` field is never truth about expiry. An `act`-tier row is valid
      only with a parseable custody attestation naming that wallet; an
      unparseable attestation refuses loudly rather than silently degrading
      to the unattested cap. Inversely, an active REVIEW-class grant with no
      backing active row is refused: authority claimed outside the register
      the capability ratified is authority this validator does not honour
      (review-authority intake; design D4/D11 — the register's shape is
      enforced here, no contract schema authored for it).
      THE WHOLE TOP LEVEL IS READ, and every key it recognizes is
      adjudicated: `revocation_staleness_bound` must be a well-formed non-zero
      duration of weeks/days/hours/minutes/seconds, and an unrecognized
      top-level key is refused outright. A governed declaration that this
      required check parses and never adjudicates is a vacuous pass and
      confers nothing — the defect that kept the four minted council seat keys
      out of the register in the first place.
      PER-SEAT SIGNING KEYS are recorded beside the rows and ENFORCED: each
      entry's field set is exact, its fingerprint RECOMPUTES from its own
      public key, the pair (council_id, seat_id) is unique while key_id and
      key_fingerprint are unique GLOBALLY, its authorizing row resolves ACTIVE
      and unexpired by computed time, and its council is the holder that row
      commissions. NEITHER SURFACE IS BOUNDED BY A COUNT (wallet-v1.5): the
      register carries one AUTHORITY ROW per commissioned body and the reader
      bounds its breadth by three invariants instead — every row resolves end
      to end, every seat entry attaches to a row that commissions its body, and
      the seat pair is unique (review-authority-register-reader).

Exit codes: 0 ok, 1 findings, 2 harness error or a refusal to compose.
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ENVELOPE_SCHEMA_PATH = ROOT / "contracts" / "schemas" / "hermes-job-envelope.schema.yaml"
CORE_PATH = ROOT / "openWallet" / "code" / "scripts" / "validate-openxwallet.py"
# Rule (t)'s three negatives stay at their path here (design.md D6): history
# unbroken, nothing renamed, and the core's examples-prefix exclusion already
# keeps them out of every live scan.
ADAPTER_NEGATIVE_DIR = ROOT / "contracts" / "openxwallet" / "examples" / "negative"
ADAPTER_NEGATIVE_GLOB = "grant-review-*.yaml"


# --------------------------- composition: fail closed first ---------------------------

class CompositionRefusal(Exception):
    """A named refusal to compose: exit 2, printed as one `REFUSE` line and
    the remediation for its level on the next (design.md D5)."""

    def __init__(self, code: str, detail: str, remediation: str) -> None:
        self.code = code
        self.detail = detail
        self.remediation = remediation
        super().__init__(code, detail)

    def __str__(self) -> str:
        return f"REFUSE {self.code}: {self.detail}\n{self.remediation}"


# The remediations, one per level (design.md D5, "the remediation for THAT
# level"). Scoped, never --recursive: the spec leg carries nothing this file
# reads. Each ends at the pin verifier, which asks WHICH commit is checked out.
ROOT_INIT = "git submodule update --init openWallet"
LEG_INIT = "git -C openWallet submodule update --init code"
VERIFY_PIN = "python3 scripts/verify-openwallet-pin.py"
ROOT_REMEDIATION = (f"Remediation: run `{ROOT_INIT}`, then `{LEG_INIT}` "
                    f"(scoped, never --recursive), then `{VERIFY_PIN}`.")
LEG_REMEDIATION = (f"Remediation: run `{LEG_INIT}` (scoped, never "
                   f"--recursive), then `{VERIFY_PIN}`.")
CORE_REMEDIATION = (f"Remediation: run `{VERIFY_PIN}`, which names what is "
                    f"wrong with the pinned checkout; restore it with "
                    f"`{ROOT_INIT}`, then `{LEG_INIT}` (scoped, never "
                    f"--recursive).")

# Each level of the mount, the code scripts/verify-openwallet-pin.py gives the
# same fact (one fact, one name), and that level's remediation.
MOUNT_LEVELS = (
    ("openWallet", "pin-submodule-uninitialized", ROOT_REMEDIATION),
    ("openWallet/code", "pin-leg-uninitialized", LEG_REMEDIATION),
)

# The names this file registers into, or reads through, the loaded core. A core
# without one of them is not the core this adapter composes against.
CORE_CONTRACT = (
    "main", "VOCABULARY_BINDING", "REQUIREMENTS", "GRANT_RULES",
    "SELF_TEST_HOOKS", "SELF_TEST_TAIL_HOOKS", "TREE_CHECKS",
    "Findings", "Context", "validate_record", "expected_failure", "codes_of",
    "lines_for", "load_yaml", "_mapping", "_hashable_set",
    "fingerprint_of_public_key", "yaml",
)


def load_core() -> ModuleType:
    """The pinned core, loaded in process, or a CompositionRefusal."""
    for level, code, remediation in MOUNT_LEVELS:
        if not (ROOT / level / ".git").exists():
            raise CompositionRefusal(
                code,
                f"{level}/.git does not exist: {level} is not initialized, so "
                f"the validator this entrypoint runs is not present",
                remediation)
    shown = CORE_PATH.relative_to(ROOT)
    spec = importlib.util.spec_from_file_location(
        "openwallet_validate_openxwallet", CORE_PATH)
    if spec is None or spec.loader is None:
        raise CompositionRefusal("core-unloadable",
                                 f"{shown}: no importable module spec",
                                 CORE_REMEDIATION)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except SystemExit as exc:
        # An exiting core is a core that did not load: a tampered one that
        # exits 0 at import would otherwise end this entrypoint green with
        # nothing adjudicated. Say so, then leave through the SAME exception
        # with the refusal's exit code. KeyboardInterrupt is not caught.
        print(CompositionRefusal(
            "core-unloadable",
            f"{shown} exits while loading (SystemExit: exit code "
            f"{exc.code!r})", CORE_REMEDIATION), file=sys.stderr)
        exc.code = 2
        raise
    except Exception as exc:  # noqa: BLE001 - any failure to load is a refusal
        raise CompositionRefusal(
            "core-unloadable",
            f"{shown} does not load ({type(exc).__name__}: {exc})",
            CORE_REMEDIATION) from exc
    missing = [name for name in CORE_CONTRACT if not hasattr(module, name)]
    if missing:
        raise CompositionRefusal(
            "core-unloadable",
            f"{shown} loads but does not expose {missing}, which this adapter "
            f"registers into or reads through; it is not the core this "
            f"entrypoint composes against",
            CORE_REMEDIATION)
    return module


def _core_or_refuse() -> ModuleType:
    try:
        return load_core()
    except CompositionRefusal as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from None


core = _core_or_refuse()

# The core's own names, read through the loaded module and never copied, so the
# blocks below read exactly as they did when the validator was one file.
Findings = core.Findings
Context = core.Context
validate_record = core.validate_record
expected_failure = core.expected_failure
codes_of = core.codes_of
lines_for = core.lines_for
load_yaml = core.load_yaml
_mapping = core._mapping
_hashable_set = core._hashable_set
yaml = core.yaml

# Rule (t). The review-authority intake composes this capability rather than
# extending it, so its two restrictions live HERE as named constants instead of
# in any schema. The class marker is the canonical review act token from
# review-authority-intake requirement 1 ("scope.acts names the review act");
# membership in a grant's scope.acts is what makes the grant REVIEW-class, and
# nothing else can trigger the class. The anchor token is the responsible
# operator's identity, ruled exact-match by the convener (2026-08-23); its
# AUTHORITY is not asserted here but cited — the operator's standing to issue
# root review-authority grants is recorded under the Human Escalation
# Contract, and this code points at that standing record rather than
# duplicating or re-deriving it.
# Contract note: the anchor token is the operator's email address. The grant
# schema's original identifier grammar could not carry one (no `@`), which the
# anchored-root self-test assertion caught before merge; the convener
# re-ruled 2026-08-24: token = Brett.Heap@opensoft.one AND a schema widening
# (issuer_identifier def) authorized for exactly this field. The initial
# display-name ruling `Brett Heap` is superseded.
REVIEW_ACT_TOKEN = "review"
ROOT_ISSUER_OPERATOR_TOKEN = "Brett.Heap@opensoft.one"
ISSUER_ANCHOR_AUTHORITY = "docs/roles-and-authority.md:103-140"
# Detail-pin classification ONLY: a machine-shaped issuer value gets the
# machine-named refusal wording. This regex never weakens the rule — every
# non-exact value is refused regardless of shape — it only says WHY the value
# cannot be the anchor. A bare prefix followed by a long hex blob is how the
# subject ids and key handles in this ecosystem name machines; a human name
# does not look like this, and the legacy org string does not either.
_MACHINE_ISSUER_RE = re.compile(r"^[a-z][a-z0-9]*-[0-9a-f]{8,}$", re.IGNORECASE)
_LEGACY_ORG_ISSUER = "opensoft"

# Registered into the core's REQUIREMENTS, after its own rows. The
# review-authority intake family (rule (t)): one capability, one prefix, one row
# per independently probed invariant, the pattern the core's profile prefix
# follows.
ADAPTER_REQUIREMENTS: dict[str, str] = {
    "OXWR-R1": "Every review-authority grant names its issuer",
    "OXWR-R2": ("A root review-authority grant's issuer is anchored outside "
                "the register"),
}


# --------------------------- rule (t): review-class grants ---------------------------

def _unanchored_issuer_reason(issued_by: Any, ctx: Context) -> str:
    """WHY a root REVIEW-class grant's issuer is not the anchor, in the wording
    each detail pin names. Classification only: every non-exact value is
    refused, whatever this returns.

    Schema-invalid values still reach the rules (findings accumulate;
    validation never stops), so every read here must tolerate a non-string
    issued_by: a list or mapping is unhashable, and `in` against a dict keyset
    would crash the whole run as a harness error instead of reporting the
    refusal. Non-strings simply take the generic branch — the schema finding is
    the precise report, this one refuses the anchor either way.
    """
    machine_named = (
        isinstance(issued_by, str)
        and (issued_by in ctx.wallets
             or bool(_MACHINE_ISSUER_RE.match(issued_by))))
    if machine_named:
        return (f"{issued_by!r}, a MACHINE-named issuer; a root "
                f"issuer cannot be an agent holder")
    if issued_by == _LEGACY_ORG_ISSUER:
        return (f"{issued_by!r}, the LEGACY org-level string; "
                f"pre-anchor issuance values do not grandfather "
                f"into the operator anchor")
    return (f"{issued_by!r}, which is not the anchored "
            f"responsible operator")


def check_review_issuer(f: Findings, label: str, doc: dict, ctx: Context) -> None:
    """Rule (t), a GRANT_RULES entry: inside check_grant, after the tier lookup
    and before rule (e), the position it held when it was written inline."""
    scope = _mapping(doc.get("scope"))

    # (t) the issuer is recorded, and roots are anchored. Class membership is
    # a scope-content fact and nothing else: the token's PRESENCE in acts
    # makes the grant review-class by design, so an unrelated grant must not
    # borrow the token casually. Absent issuer and unanchored root are
    # sequential, not nested: an absent value cannot be compared against an
    # anchor, so it reports its own code and stops there. The exact-match
    # comparison is deliberately un-normalized — identity strings do not get
    # fuzzy, so ` brett heap` is as refused as `opensoft`.
    if REVIEW_ACT_TOKEN in _hashable_set(scope.get("acts")):
        issued_by = doc.get("issued_by")
        if not issued_by:
            f.error("issuer-unrecorded",
                    f"{label}: REVIEW-class grant (scope acts include "
                    f"{REVIEW_ACT_TOKEN!r}) records no issued_by; every "
                    f"review-authority grant names its issuer")
        elif not doc.get("parent_grant_ref"):
            if issued_by != ROOT_ISSUER_OPERATOR_TOKEN:
                why = _unanchored_issuer_reason(issued_by, ctx)
                f.error("root-issuer-unanchored",
                        f"{label}: root REVIEW-class grant names its issuer "
                        f"as {why}. A root issuer's authority to issue is "
                        f"not conferred by the register the grant writes "
                        f"into; it is standing under the Human Escalation "
                        f"Contract ({ISSUER_ANCHOR_AUTHORITY}), and the only "
                        f"accepted root-issuer value here is "
                        f"{ROOT_ISSUER_OPERATOR_TOKEN!r}")


# --------------------------- layer 1: openXwallet's own probes ---------------------------

def adapter_negative_paths() -> list[Path]:
    """Rule (t)'s negatives, sorted. The glob is the adapter's declared fixture
    family; the S2 named-probe check below requires each of the three by name."""
    return sorted(ADAPTER_NEGATIVE_DIR.glob(ADAPTER_NEGATIVE_GLOB))


def _copy_context(ctx: Context) -> Context:
    """A context carrying `ctx`'s indexes by value, so a probe can index a
    record of its own without the packaged context ever seeing it."""
    copied = Context(ctx.registry, ctx.vocabulary)
    copied.wallets = dict(ctx.wallets)
    copied.grants = dict(ctx.grants)
    copied.constraints = dict(ctx.constraints)
    copied.wallets_by_key = {k: list(v) for k, v in ctx.wallets_by_key.items()}
    copied.duplicate_ids = set(ctx.duplicate_ids)
    return copied


def _adjudicate_negative(f: Findings, path: Path, docs: dict[str, dict],
                         ctx: Context, covered: dict[str, list[str]]) -> None:
    """One adapter negative, adjudicated as the core's corpus loop adjudicates
    its own: the requirement it claims must exist, and it must FAIL for its
    declared code (and detail pin) in the packaged context plus itself. The
    core's loop body is not a function this file can call, so its verdicts are
    restated here, word for word."""
    code, detail, requirement = expected_failure(path)
    label = f"negative/{path.name}"
    if requirement not in core.REQUIREMENTS:
        f.error("negative-requirement-unknown",
                f"{label}: declares requirement {requirement!r}, which is "
                f"not one of the capability's requirements")
    else:
        covered.setdefault(requirement, []).append(path.name)

    local = Findings()
    local_ctx = _copy_context(ctx)
    doc = load_yaml(path)
    if isinstance(doc, dict):
        local_ctx.index(doc)
    validate_record(local, label, doc, docs, local_ctx)

    if not local.errors:
        f.error("negative-should-fail",
                f"{label}: expected invalid, validated cleanly — the probe "
                f"proves nothing")
    elif code not in codes_of(local.errors):
        f.error("negative-wrong-reason",
                f"{label}: expected finding {code!r}, got "
                f"{sorted(codes_of(local.errors))}")
    elif detail and not any(detail in line for line in lines_for(local.errors, code)):
        f.error("negative-wrong-reason",
                f"{label}: finding {code!r} fired but not for {detail!r} — "
                f"the fixture no longer tests the invariant it is named "
                f"for: {lines_for(local.errors, code)}")


def self_test_review_authority(f: Findings, docs: dict[str, dict],
                               ctx: Context, negatives: list[Path],
                               covered: dict[str, list[str]]) -> None:
    """The SELF_TEST_HOOKS entry, after the core's corpus loop: where the S2
    block always ran, and before the multi-key named probes, the closure and the
    corpus note, so the note counts rule (t)'s negatives and the closure sees
    OXWR-R1 and OXWR-R2 covered."""
    for path in adapter_negative_paths():
        _adjudicate_negative(f, path, docs, ctx, covered)
        negatives.append(path)
    _probe_boundary_guard(f, docs, ctx)
    _probe_root_anchor(f, docs, ctx)
    _probe_child_exemption(f, docs, ctx)
    _require_s2_named_probes(f, negatives)


def _probe_boundary_guard(f: Findings, docs: dict[str, dict],
                          ctx: Context) -> None:
    # Boundary guard (US3): the widening must cost non-review grants nothing.
    # A schema-valid post_transaction-class ROOT grant with NO issued_by is
    # exactly what every packaged positive looked like before S2; validated
    # against the packaged context (audience resolves, ceiling admits its
    # tier), it must come back with ZERO findings. Any finding here means
    # class membership leaked past the scope-content test.
    boundary = {
        "schema_version": 1,
        "kind": "xfactory_wallet_grant",
        "grant_id": "grant-boundary-guard-non-review-0001",
        "audience": {"wallet_ref": "wal-agent-poster-0001",
                     "holder_ref": "agent:ledger-poster"},
        "scope": {
            "acts": ["create_transaction", "post_transaction"],
            "authority_tier": "act",
            "approval_posture": {
                "hermes_approval_required_before_apply": True,
                "authority_agents_may_approve": False,
                "human_escalation_required_for": [
                    "irreversible_external_effect"],
            },
        },
        "expires_at": "2027-12-31T23:59:59Z",
        "issued_at": "2026-08-24T00:00:00Z",
        "state": "active",
    }
    local = Findings()
    validate_record(local, "self-test/boundary-guard", boundary, docs, ctx)
    if local.errors:
        f.error("boundary-guard-failed",
                f"a non-review root grant without issued_by must validate "
                f"cleanly (US3); got {local.errors}")


def _probe_root_anchor(f: Findings, docs: dict[str, dict], ctx: Context) -> None:
    # S2 anchor assertions. The packaged specimens prove the corpus fails on
    # the violations; these synthetic probes pin the RULE's own edges so no
    # single edit or deleted fixture can silence an invariant while the
    # self-test stays green: the anchored-root positive, whitespace/case
    # drift refused without normalization, child grants exempt from the root
    # check, and both refusal wordings the detail pins name.
    def _anchor_probe(label, doc, expect_code=None, expect_sub=None):
        probe = Findings()
        validate_record(probe, label, doc, docs, ctx)
        errs = probe.errors
        if expect_code is None:
            if errs:
                f.error("anchor-assertion-failed",
                        f"{label}: expected clean, got {errs}")
            return
        if not any(expect_code in e for e in errs):
            f.error("anchor-assertion-failed",
                    f"{label}: expected {expect_code!r}, got "
                    f"{sorted(codes_of(errs))} {errs}")
        elif expect_sub and not any(
                expect_sub in e for e in errs if expect_code in e):
            f.error("anchor-assertion-failed",
                    f"{label}: {expect_code!r} fired but without the "
                    f"{expect_sub!r} wording")

    review_scope = {
        "acts": [REVIEW_ACT_TOKEN],
        "authority_tier": "act",
        "approval_posture": {
            "hermes_approval_required_before_apply": True,
            "authority_agents_may_approve": False,
            "human_escalation_required_for": ["irreversible_external_effect"],
        },
    }
    _anchor_probe("self-test/anchor-anchored-root", {
        "schema_version": 1, "kind": "xfactory_wallet_grant",
        "grant_id": "grant-anchor-assert-anchored-0001",
        "audience": {"wallet_ref": "wal-agent-poster-0001",
                     "holder_ref": "agent:ledger-poster"},
        "scope": dict(review_scope),
        "expires_at": "2027-12-31T23:59:59Z",
        "issued_at": "2026-08-24T00:00:00Z",
        "issued_by": ROOT_ISSUER_OPERATOR_TOKEN, "state": "active",
    })
    _anchor_probe("self-test/anchor-drift-not-normalized", {
        "schema_version": 1, "kind": "xfactory_wallet_grant",
        "grant_id": "grant-anchor-assert-drift-0001",
        "audience": {"wallet_ref": "wal-agent-poster-0001",
                     "holder_ref": "agent:ledger-poster"},
        "scope": dict(review_scope),
        "expires_at": "2027-12-31T23:59:59Z",
        "issued_at": "2026-08-24T00:00:00Z",
        "issued_by": " brett heap", "state": "active",
    }, expect_code="root-issuer-unanchored")
    _anchor_probe("self-test/anchor-machine-wording", {
        "schema_version": 1, "kind": "xfactory_wallet_grant",
        "grant_id": "grant-anchor-assert-machine-0001",
        "audience": {"wallet_ref": "wal-agent-poster-0001",
                     "holder_ref": "agent:ledger-poster"},
        "scope": dict(review_scope),
        "expires_at": "2027-12-31T23:59:59Z",
        "issued_at": "2026-08-24T00:00:00Z",
        "issued_by": "sub-deadbeefdeadbeef", "state": "active",
    }, expect_code="root-issuer-unanchored", expect_sub="MACHINE")
    _anchor_probe("self-test/anchor-legacy-wording", {
        "schema_version": 1, "kind": "xfactory_wallet_grant",
        "grant_id": "grant-anchor-assert-legacy-0001",
        "audience": {"wallet_ref": "wal-agent-poster-0001",
                     "holder_ref": "agent:ledger-poster"},
        "scope": dict(review_scope),
        "expires_at": "2027-12-31T23:59:59Z",
        "issued_at": "2026-08-24T00:00:00Z",
        "issued_by": _LEGACY_ORG_ISSUER, "state": "active",
    }, expect_code="root-issuer-unanchored", expect_sub="LEGACY")


def _probe_child_exemption(f: Findings, docs: dict[str, dict],
                           ctx: Context) -> None:
    # Child exemption needs a RESOLVING parent, which the packaged corpus
    # cannot supply without tripping attenuation (no packaged parent confers
    # the review act), so the parent is synthesized into a copied context.
    family_ctx = _copy_context(ctx)
    family_ctx.index({
        "schema_version": 1, "kind": "xfactory_wallet_grant",
        "grant_id": "grant-anchor-assert-parent-0001",
        "audience": {"wallet_ref": "wal-agent-poster-0001",
                     "holder_ref": "agent:ledger-poster"},
        "scope": {
            "acts": ["create_transaction", "post_transaction"],
            "authority_tier": "act",
            "approval_posture": {
                "hermes_approval_required_before_apply": True,
                "authority_agents_may_approve": False,
                "human_escalation_required_for": [
                    "irreversible_external_effect"],
            },
        },
        "expires_at": "2027-12-31T23:59:59Z",
        "issued_at": "2026-08-24T00:00:00Z",
        "state": "active",
    })
    child_doc = {
        "schema_version": 1, "kind": "xfactory_wallet_grant",
        "grant_id": "grant-anchor-assert-child-0001",
        "parent_grant_ref": "grant-anchor-assert-parent-0001",
        "audience": {"wallet_ref": "wal-agent-poster-0001",
                     "holder_ref": "agent:ledger-poster"},
        "scope": {
            "acts": ["post_transaction"], "authority_tier": "act",
            "approval_posture": {
                "hermes_approval_required_before_apply": True,
                "authority_agents_may_approve": False,
                "human_escalation_required_for": [
                    "irreversible_external_effect"],
            },
        },
        "expires_at": "2027-06-30T23:59:59Z",
        "issued_at": "2026-08-24T00:00:00Z",
        "issued_by": "sub-0123456789abcdef", "state": "active",
    }
    child_probe = Findings()
    validate_record(child_probe, "self-test/anchor-child-exempt",
                    child_doc, docs, family_ctx)
    if child_probe.errors:
        f.error("anchor-assertion-failed",
                f"self-test/anchor-child-exempt: a review-class CHILD with "
                f"a machine-shaped issuer inherits attenuation semantics, "
                f"not the root check; expected clean, got "
                f"{child_probe.errors}")


def _require_s2_named_probes(f: Findings, negatives: list[Path]) -> None:
    # The three S2 fixtures are named probes, not interchangeable coverage:
    # their absence or a stripped detail pin must be loud even though the
    # requirement rows would still look covered.
    by_name = {p.name: p for p in negatives}
    for name in ("grant-review-authority-omits-issued-by.yaml",
                 "grant-review-root-issuer-is-a-machine.yaml",
                 "grant-review-root-issuer-says-opensoft.yaml"):
        path = by_name.get(name)
        if path is None:
            f.error("examples-missing",
                    f"S2 named probe negative/{name} is absent from the "
                    f"packaged corpus; each branch of rule (t) keeps its own "
                    f"standing fixture")
            continue
        _, detail, _ = expected_failure(path)
        if name != "grant-review-authority-omits-issued-by.yaml" and not detail:
            f.error("negative-wrong-reason",
                    f"negative/{name}: S2 branch probes MUST carry an "
                    f"expected_failure_detail pin naming their branch; an "
                    f"unpinned probe can be mutated into testing nothing")


def self_test_register_reader(f: Findings, _docs: dict[str, dict],
                              ctx: Context) -> None:
    """The SELF_TEST_TAIL_HOOKS entry, after the corpus note: where the S4 block
    always ran. `_docs` is the hook contract's; the reader needs no schema."""
    # S4 register-reader assertions. Same discipline as the S2 anchor block:
    # the live register proves the happy path, and these synthetic probes pin
    # every refusal code the reader can emit so no edit or deleted fixture
    # silences an invariant while the self-test stays green. The register is
    # kindless BY RULING (D11), so file fixtures cannot be corpus negatives -
    # these synthesized trees ARE the negative coverage.
    import tempfile
    now = datetime(2026, 9, 1, tzinfo=timezone.utc)
    future = "2026-11-23T12:00:00Z"
    past = "2026-08-01T12:00:00Z"

    def _s4_ctx(*docs):
        c = Context(ctx.registry, ctx.vocabulary)
        for d in docs:
            c.index(d)
        return c

    s4_wallet = {
        "schema_version": 1, "kind": "xfactory_wallet_record",
        "wallet_id": "wal-s4-probe-0001",
        "holder": {"holder_id": "agent:s4-probe",
                   "holder_class": "agent"},
        "key_reference": {"did": "did:key:z6Mko2FefScUQg9opCriwQmjfcb3Qjnb5bN49hQsEVMo6gee",
                          "key_id": "key-s4-0001",
                          "signature_algorithm": "ed25519"},
        "custody": {"model": "holder_readable", "registry_version": 1},
        "state": "active",
    }
    s4_grant = {
        "schema_version": 1, "kind": "xfactory_wallet_grant",
        "grant_id": "grant-s4-probe-0001",
        "audience": {"wallet_ref": "wal-s4-probe-0001",
                     "holder_ref": "agent:s4-probe"},
        "scope": {"acts": [REVIEW_ACT_TOKEN], "authority_tier": "act",
                  "objects": ["opensoft/openxFactory"]},
        "expires_at": future, "state": "active",
        "issued_by": ROOT_ISSUER_OPERATOR_TOKEN,
    }
    s4_row = {
        "row_id": "row-s4-0001",
        "holder_ref": "agent:s4-probe",
        "wallet_ref": "wal-s4-probe-0001",
        "target_repo": "opensoft/openxFactory",
        "act": REVIEW_ACT_TOKEN, "authority_tier": "act",
        "grant_ref": "grant-s4-probe-0001", "expires_at": future,
        "state": "active",
    }
    s4_attest = {
        "attestation_id": "attest-custody-wal-s4-probe-0001",
        "subject_wallet_ref": "wal-s4-probe-0001",
        "custody_model_attested": "holder_readable",
        "verified_by": {"name": "Brett Heap", "role": "responsible operator",
                        "standing": "Human Escalation Contract"},
        "verified_at": "2026-08-24T12:00:00Z",
        "verified_against": {"method": "operator-minted ed25519 keypair",
                             "isolation_claimed": False},
    }

    def _s4_tree(register_rows, with_attest=True, grant=None, wallet=None,
                 top=None, also=(), also_attest=()):
        base = Path(tempfile.mkdtemp(prefix="s4-selftest-"))
        ra = base.joinpath(*REGISTER_DIR_PARTS, ATTESTATIONS_DIR)
        ra.mkdir(parents=True)
        # wallet-v1.2: the staleness bound is REQUIRED, so every probe tree
        # declares one. `top` overrides or extends the top level, which is how
        # the top-level probes below inject an unknown key or a bad bound
        # WITHOUT any probe having to hand-build a tree.
        doc = {"register_version": 1, "revocation_staleness_bound": "P7D",
               "rows": register_rows}
        if top is not None:
            doc.update(top)
            for k, v in list(top.items()):
                if v is _ABSENT:
                    doc.pop(k, None)
        (base.joinpath(*REGISTER_DIR_PARTS, REGISTER_FILE)).write_text(
            yaml.safe_dump(doc), encoding="utf-8")
        if with_attest:
            (ra / "custody-attest-wal-s4-probe-0001.yaml").write_text(
                yaml.safe_dump(s4_attest), encoding="utf-8")
        # wallet-v1.5: `also` indexes the SECOND commissioned body's records and
        # `also_attest` writes its custody attestation, so a multi-body probe
        # needs no hand-built tree either.
        for extra_attest in also_attest:
            (ra / f"custody-attest-{extra_attest['subject_wallet_ref']}.yaml"
             ).write_text(yaml.safe_dump(extra_attest), encoding="utf-8")
        return base, _s4_ctx(grant or s4_grant, wallet or s4_wallet, *also)

    def _register_probe(label, base, c, expect_codes):
        probe = Findings()
        check_register(probe, base, c, now=now)
        got = {e.split("]")[0].replace("ERROR [", "") for e in probe.errors}
        expected = set(expect_codes)
        missing = expected - got
        extra = got - expected
        if missing or extra:
            f.error("register-assertion-failed",
                    f"{label}: expected {sorted(expect_codes)}, got "
                    f"{sorted(got)}")

    # Positive: a fully resolving row is CLEAN.
    base, c = _s4_tree([s4_row])
    _register_probe("self-test/register-clean", base, c, set())

    # Computed expiry: past expires_at refuses as expired AND flags the stale
    # stored state AND leaves the grant without a backing active row.
    stale_row = dict(s4_row, expires_at=past)
    stale_grant = dict(s4_grant, expires_at=past)
    base, c = _s4_tree([stale_row], grant=stale_grant)
    _register_probe("self-test/register-computed-expiry", base, c,
                    {"register-row-expired", "grant-state-stale",
                     "register-no-active-row"})

    wrong_binding = dict(
        s4_grant,
        audience={"wallet_ref": "wal-s4-probe-0001",
                  "holder_ref": "agent:other-holder"},
        scope={"acts": [REVIEW_ACT_TOKEN], "authority_tier": "act",
               "objects": ["opensoft/other-repo"]},
    )
    base, c = _s4_tree([s4_row], grant=wrong_binding)
    _register_probe("self-test/register-grant-binding", base, c,
                    {"register-grant-mismatch"})

    naive_row = dict(s4_row, expires_at="2026-11-23T12:00:00")
    base, c = _s4_tree([naive_row])
    _register_probe("self-test/register-naive-timestamp", base, c,
                    {"register-row-malformed", "register-no-active-row"})

    # Grant without any backing row: the headline obligation.
    empty_reg = dict({"register_version": 1,
                      "revocation_staleness_bound": "P7D", "rows": []})
    base = Path(tempfile.mkdtemp(prefix="s4-selftest-"))
    ra = base.joinpath(*REGISTER_DIR_PARTS, ATTESTATIONS_DIR)
    ra.mkdir(parents=True)
    (base.joinpath(*REGISTER_DIR_PARTS, REGISTER_FILE)).write_text(
        yaml.safe_dump(empty_reg), encoding="utf-8")
    _register_probe("self-test/register-no-active-row", base,
                    _s4_ctx(s4_grant, s4_wallet),
                    {"register-row-malformed", "register-no-active-row"})

    # wallet-v1.4: A REVOKED REVIEW-CLASS GRANT OWES NO ROW. This is the
    # RE-ISSUANCE shape and nothing else: the predecessor was revoked, the
    # successor issued against it, and the one permitted row repointed. Before
    # wallet-v1.4 the closing loop read only `scope.acts` and demanded a
    # backing active row for the revoked predecessor too -- a row the row-count
    # cap of the day forbade (retired at wallet-v1.5) -- so no consumer could
    # represent a re-issuance at all. Three probes, because the fix has three halves: the shape is
    # CLEAN, the guard still fires on an ACTIVE grant with no row (the probe
    # above), and a row pointing AT a revoked grant is still refused.
    s4_revoked = dict(
        s4_grant, grant_id="grant-s4-probe-0000", state="revoked",
        revocation={"revoked_at": "2026-08-30T12:00:00Z",
                    "reason": "superseded by grant-s4-probe-0001 for drift; "
                              "the register act's shape"})
    base, c = _s4_tree([s4_row])
    c.index(s4_revoked)
    _register_probe("self-test/register-revoked-grant-exempt", base, c, set())

    # PROTECTION PRESERVED, the row->grant direction: a row that still points
    # at the revoked grant is refused. The exemption is only ever about a
    # revoked grant NO row names.
    base, c = _s4_tree([dict(s4_row, grant_ref="grant-s4-probe-0000")],
                       grant=s4_revoked)
    _register_probe("self-test/register-revoked-grant-still-mismatches",
                    base, c, {"register-grant-mismatch"})

    # The SAME exemption on the absent-register branch, which states the same
    # obligation for a tree that never cold-started: revoked-only is clean.
    probe = Findings()
    check_register(probe, Path(tempfile.mkdtemp(prefix="s4-selftest-")),
                   _s4_ctx(s4_revoked, s4_wallet), now=now)
    if probe.errors:
        f.error("register-assertion-failed",
                f"self-test/register-revoked-grant-absent-register: an absent "
                f"register with only REVOKED review-class grants must be "
                f"clean; got {probe.errors}")

    # act tier without a parseable attestation refuses loudly.
    base, c = _s4_tree([s4_row], with_attest=False)
    _register_probe("self-test/register-tier-act-unattested", base, c,
                    {"register-tier-act-unattested"})

    # THE ROW-COUNT PROBE IS RETIRED HERE (wallet-v1.5, design D4). It asserted
    # `register-minimal-shape-exceeded` on a second authority row; that refusal
    # is retired by name, and a probe expecting a refusal the reader can never
    # emit is a test of nothing. What replaces it is the multi-body block at the
    # end of this function -- a positive probe for two resolving bodies and a
    # negative for a second row that does NOT resolve, which is the invariant
    # the count was standing in for.

    # Unknown field on a row: strict, because this reader IS the shape.
    fat_row = dict(s4_row, extra_field="nope")
    base, c = _s4_tree([fat_row])
    _register_probe("self-test/register-row-malformed", base, c,
                    {"register-row-malformed"})

    # Absent register with no review grants: legitimate consumer posture.
    probe = Findings()
    check_register(probe, Path(tempfile.mkdtemp(prefix="s4-selftest-")),
                   Context(ctx.registry, ctx.vocabulary), now=now)
    if probe.errors:
        f.error("register-assertion-failed",
                f"absent register with no review grants must be clean; "
                f"got {probe.errors}")

    # ---------------- wallet-v1.2: the top level and the seat keys ----------
    #
    # add-per-seat-register-entries. Same discipline as the S4 block above: one
    # probe per refusal the reader can emit, plus a POSITIVE probe over the four
    # REAL public halves, so no edit silences an invariant while the self-test
    # stays green.

    def _seat(seat_id, public_key, fingerprint, row="row-s4-0001",
              council="agent:s4-probe", council_id=None, key_id=None):
        return {"seat_id": seat_id, "council_ref": council,
                "council_id": council_id if council_id is not None else
                council.split(":", 1)[-1].replace("-", "_"),
                "key_id": key_id or f"key-seat-{seat_id}-0001",
                "public_key": public_key, "key_fingerprint": fingerprint,
                "authorizing_row": row}

    real_seats = [_seat(s, k, fp) for s, k, fp in
                  SEAT_KEY_MINT_RECORD_2026_08_28]

    # The fingerprints in the mint record RECOMPUTE from the keys beside them.
    # Asserted here rather than trusted: this is the one property the reader
    # enforces that touches key material, and a stale constant would make every
    # negative below pass for the wrong reason.
    for seat_id, public_key, fingerprint in SEAT_KEY_MINT_RECORD_2026_08_28:
        raw = _decode_public_key(public_key)
        if raw is None or _fingerprint_of(raw) != fingerprint:
            f.error("register-assertion-failed",
                    f"self-test/seat-mint-record: the recorded public half for "
                    f"seat {seat_id!r} does not recompute to its recorded "
                    f"fingerprint; the 2026-08-28 mint record and this constant "
                    f"disagree")

    # THE LIVE PAIR, pinned as an assertion rather than left in a comment:
    # openxFactory's register spells the holder `agent:merge-readiness-council`
    # and hermes-install's projection spells the council
    # `merge_readiness_council`. If the reader's normalization ever stops
    # relating those two, the operator's projection step silently becomes a
    # TRANSLATION again and `review_authority.seat_unregistered` replaces the
    # refusal this arc is clearing.
    if "agent:merge-readiness-council" != (
            SEAT_COUNCIL_HOLDER_PREFIX
            + "merge_readiness_council".replace("_", "-")):  # pragma: no cover
        f.error("register-assertion-failed",
                "self-test/seat-council-live-pair: the reader no longer relates "
                "the register's holder spelling to the runtime's council id")

    # POSITIVE: one authority row, four per-seat keys, all resolving. This is
    # the shape openxFactory's register takes, and it is CLEAN.
    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: real_seats})
    _register_probe("self-test/seat-keys-clean", base, c, set())
    probe = Findings()
    check_register(probe, base, c, now=now)
    if not any("4 of 4 per-seat signing key(s) adjudicated and resolved"
               in n for n in probe.notes):
        f.error("register-assertion-failed",
                f"self-test/seat-keys-clean: the reader must NOTE how many seat "
                f"keys it resolved - a green check that proves nothing was read "
                f"is the vacuous pass this surface exists to close; got "
                f"{probe.notes}")

    # The absence NOTE (design D10): accepted, and VISIBLE.
    base, c = _s4_tree([s4_row])
    probe = Findings()
    check_register(probe, base, c, now=now)
    if probe.errors or not any(
            "no per-seat signing key is recorded" in n for n in probe.notes):
        f.error("register-assertion-failed",
                f"self-test/seat-keys-absent: an absent surface is accepted "
                f"with a note naming what is not recorded; got "
                f"{probe.errors} / {probe.notes}")

    # An unread top-level declaration is refused. THIS is the class: the
    # staleness bound sat in the live register unadjudicated because the reader
    # ignored what it did not read.
    base, c = _s4_tree([s4_row], top={"an_unread_declaration": "P1D"})
    _register_probe("self-test/register-top-level-unknown", base, c,
                    {"register-top-level-unknown"})

    base, c = _s4_tree([s4_row], top={STALENESS_BOUND_FIELD: _ABSENT})
    _register_probe("self-test/register-staleness-bound-missing", base, c,
                    {"register-staleness-bound-missing"})

    for bad in ("P1Y", "P1M", "7 days", "P", "PT", "P0D", "PT0S"):
        base, c = _s4_tree([s4_row], top={STALENESS_BOUND_FIELD: bad})
        _register_probe(f"self-test/register-staleness-bound-malformed[{bad}]",
                        base, c, {"register-staleness-bound-malformed"})

    for good in ("P7D", "P1D", "P1W", "PT12H", "P1DT6H30M"):
        base, c = _s4_tree([s4_row], top={STALENESS_BOUND_FIELD: good})
        _register_probe(f"self-test/register-staleness-bound-ok[{good}]",
                        base, c, set())

    # Malformed surfaces and entries.
    for shape in ([], "P7D", {}):
        base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: shape})
        _register_probe(f"self-test/seat-keys-malformed[{type(shape).__name__}]",
                        base, c, {"register-seat-keys-malformed"})

    fat = dict(real_seats[0], minted_at="2026-08-28T00:00:00Z")
    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [fat]})
    _register_probe("self-test/seat-entry-unknown-field", base, c,
                    {"register-seat-keys-malformed"})

    thin = {k: v for k, v in real_seats[0].items() if k != "key_id"}
    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [thin]})
    _register_probe("self-test/seat-entry-missing-field", base, c,
                    {"register-seat-keys-malformed"})

    # A 64-hex value is the encoding of a PRIVATE seed. Refused BY SHAPE inside
    # the required check (design R2) - the most plausible catastrophic paste.
    seed_shaped = dict(real_seats[0], public_key="a" * 64)
    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [seed_shaped]})
    _register_probe("self-test/seat-key-private-seed-shaped", base, c,
                    {"register-seat-key-malformed"})

    # Non-canonical base64url: 43 legal characters whose final sextet carries
    # trailing bits, so it decodes to a DIFFERENT key than it spells.
    noncanon = real_seats[0]["public_key"][:-1] + "P"
    if _decode_public_key(noncanon) is not None:  # pragma: no cover
        f.error("register-assertion-failed",
                "self-test/seat-key-noncanonical: the probe value is canonical; "
                "the non-canonical refusal is untested")
    base, c = _s4_tree([s4_row],
                       top={SEAT_KEYS_FIELD: [dict(real_seats[0],
                                                   public_key=noncanon)]})
    _register_probe("self-test/seat-key-noncanonical", base, c,
                    {"register-seat-key-malformed"})

    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [
        dict(real_seats[0], key_fingerprint="sha256:NOTHEX")]})
    _register_probe("self-test/seat-fingerprint-malformed", base, c,
                    {"register-seat-fingerprint-malformed"})

    # The fingerprint of ANOTHER real seat: legal shape, wrong key. The refusal
    # that makes the register a single source a projection can be derived from.
    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [
        dict(real_seats[0],
             key_fingerprint=SEAT_KEY_MINT_RECORD_2026_08_28[1][2])]})
    _register_probe("self-test/seat-fingerprint-mismatch", base, c,
                    {"register-seat-fingerprint-mismatch"})

    for field in ("seat_id", "key_id", "key_fingerprint"):
        clash = dict(real_seats[1])
        clash[field] = real_seats[0][field]
        # Copying seat 0's FINGERPRINT onto seat 1 also makes that entry
        # disagree with its own key, and both facts are reported: "no two
        # refusals share a reason" cuts the other way too - one entry can be
        # wrong in two ways and be told about both.
        expected = {"register-seat-duplicate"}
        if field == "key_fingerprint":
            expected.add("register-seat-fingerprint-mismatch")
        base, c = _s4_tree([s4_row],
                           top={SEAT_KEYS_FIELD: [real_seats[0], clash]})
        _register_probe(f"self-test/seat-duplicate[{field}]", base, c, expected)

    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [
        dict(real_seats[0], authorizing_row="row-nobody-0001")]})
    _register_probe("self-test/seat-row-unresolved", base, c,
                    {"register-seat-row-unresolved"})

    # An EXPIRED row is not an authority for a seat, whatever its stored state
    # says (N8) - and the row's own expiry findings stand beside it.
    base, c = _s4_tree([dict(s4_row, expires_at=past)],
                       grant=dict(s4_grant, expires_at=past),
                       top={SEAT_KEYS_FIELD: [real_seats[0]]})
    _register_probe("self-test/seat-row-expired", base, c,
                    {"register-seat-row-unresolved", "register-row-expired",
                     "grant-state-stale", "register-no-active-row"})

    # D8: an entry attached to a body this register does not commission. Both
    # spellings move together, so this probe isolates the ROW ATTACHMENT.
    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [
        _seat(*SEAT_KEY_MINT_RECORD_2026_08_28[0],
              council="agent:some-other-council")]})
    _register_probe("self-test/seat-council-mismatch", base, c,
                    {"register-seat-council-mismatch"})

    # ...and this one isolates the TWO SPELLINGS naming different bodies, which
    # is the defect that would make the operator's projection step a translation.
    base, c = _s4_tree([s4_row], top={SEAT_KEYS_FIELD: [
        dict(real_seats[0], council_id="some_other_council")]})
    _register_probe("self-test/seat-council-spelling", base, c,
                    {"register-seat-council-spelling"})

    # --------- wallet-v1.5: the SECOND commissioned body, and the pair -------
    #
    # widen-register-reader-for-a-second-council, design D4. NOTHING COUNTS ROWS
    # any more, so what keeps a WIDER register from being a LOOSER one is the
    # three invariants -- and these probes are what make an edit that silences
    # one of them red INSIDE the required check every consumer runs, rather than
    # only in this repository's tests/. The positive probes double as the
    # retirement assertion: `_register_probe` compares the code set EXACTLY, so
    # a reader that emitted `register-minimal-shape-exceeded` again would fail
    # them.
    #
    # THE SECOND BODY'S KEYS ARE DERIVED, NOT MINTED. sha256 over a probe label,
    # spelled the way the reader reads it. No key for a second council exists
    # yet -- minting one is an operator act in another repository -- and a
    # real-looking invented value in this file would be a key no ceremony
    # produced. The four REAL public halves above stay the positive probe for
    # the body that has them.
    def _s4_probe_key(label):
        raw = hashlib.sha256(label.encode("utf-8")).digest()
        return (base64.urlsafe_b64encode(raw).decode("ascii").rstrip("="),
                _fingerprint_of(raw))

    s4b_holder = "agent:s4-second-probe"
    s4b_wallet = dict(
        s4_wallet, wallet_id="wal-s4-probe-0002",
        holder={"holder_id": s4b_holder, "holder_class": "agent"},
        # A DISTINCT did and key_id: check_register reads neither, but a second
        # body that presented the first body's key identity would be a probe
        # asserting something this reader exists to refuse one layer up.
        key_reference={
            "did": "did:key:z6MkesFwon9Uucr7UuwNmnHg2ci5tXfk5yaJ1jVV33jBaXrd",
            "key_id": "key-s4-0002", "signature_algorithm": "ed25519"})
    s4b_grant = dict(
        s4_grant, grant_id="grant-s4-probe-0002",
        audience={"wallet_ref": "wal-s4-probe-0002", "holder_ref": s4b_holder})
    s4b_row = dict(s4_row, row_id="row-s4-0002", holder_ref=s4b_holder,
                   wallet_ref="wal-s4-probe-0002",
                   grant_ref="grant-s4-probe-0002")
    s4b_attest = dict(s4_attest,
                      attestation_id="attest-custody-wal-s4-probe-0002",
                      subject_wallet_ref="wal-s4-probe-0002")
    s4b_records = {"also": (s4b_grant, s4b_wallet),
                   "also_attest": (s4b_attest,)}

    # ONE SHARED SEAT NAME AND ONE OF ITS OWN. The shared one is the whole
    # defect: three of the four seats openxFactory's ratified act registers are
    # names the first body already records.
    s4b_seats = []
    for seat_id in ("lead-quality", "lead-second-only"):
        _pub, _fp = _s4_probe_key(f"self-test/{s4b_holder}/{seat_id}")
        s4b_seats.append(_seat(seat_id, _pub, _fp, row="row-s4-0002",
                               council=s4b_holder,
                               key_id=f"key-s4b-seat-{seat_id}-0001"))

    # INVARIANT (i) POSITIVE, and (iii) with it: two bodies, each resolving to
    # its OWN wallet, grant and custody attestation, with seats under both
    # councils -- one of the names shared. CLEAN, and the notes say so.
    base, c = _s4_tree([s4_row, s4b_row], **s4b_records,
                       top={SEAT_KEYS_FIELD: real_seats + s4b_seats})
    _register_probe("self-test/register-two-bodies-clean", base, c, set())
    probe = Findings()
    check_register(probe, base, c, now=now)
    if not any("(2 row(s))" in n for n in probe.notes) or not any(
            "6 of 6 per-seat signing key(s) adjudicated and resolved" in n
            for n in probe.notes):
        f.error("register-assertion-failed",
                f"self-test/register-two-bodies-clean: the reader must NOTE two "
                f"rows and six adjudicated seat keys - the consumer gate asserts "
                f"on these counts POSITIVELY, and a widened reader that admits a "
                f"second body without reading its seats is the vacuous pass this "
                f"surface exists to close; got {probe.notes}")

    # INVARIANT (iii) POSITIVE, ISOLATED: one seat NAME, two councils, each
    # entry attached to its own body's row. Two bodies commonly seat one ROLE,
    # and a register that cannot say so cannot represent a second body at all.
    base, c = _s4_tree([s4_row, s4b_row], **s4b_records,
                       top={SEAT_KEYS_FIELD: [real_seats[0], s4b_seats[0]]})
    _register_probe("self-test/register-two-councils-one-seat-name", base, c,
                    set())

    # INVARIANT (iii) NEGATIVE: the SAME seat twice under ONE council, in a
    # register that also commissions a second body -- still refused, and the
    # pair key is what tells this apart from the probe above. A DIFFERENT key,
    # so the collision under test is the seat and not the key material.
    _dup_pub, _dup_fp = _s4_probe_key(
        f"self-test/{s4b_holder}/lead-quality/second-answer")
    s4b_dup = dict(s4b_seats[0], public_key=_dup_pub, key_fingerprint=_dup_fp,
                   key_id="key-s4b-seat-lead-quality-0002")
    base, c = _s4_tree([s4_row, s4b_row], **s4b_records,
                       top={SEAT_KEYS_FIELD: [real_seats[0], s4b_seats[0],
                                              s4b_dup]})
    _register_probe("self-test/register-seat-duplicate-within-one-council",
                    base, c, {"register-seat-duplicate"})

    # INVARIANT (ii) NEGATIVE, in the shape only a MULTI-BODY register can
    # take: an entry attached to a row that commissions a DIFFERENT body. With
    # one row this was unreachable; with two it is the mistake a wider register
    # invites, and it is what stops the second body's seats from descending
    # from the first body's authority.
    base, c = _s4_tree([s4_row, s4b_row], **s4b_records,
                       top={SEAT_KEYS_FIELD: [
                           dict(s4b_seats[1], authorizing_row="row-s4-0001")]})
    _register_probe("self-test/register-seat-attached-to-another-bodys-row",
                    base, c, {"register-seat-council-mismatch"})

    # INVARIANT (i) NEGATIVE, and the probe that makes retiring the count safe:
    # a second row whose grant does not back it is refused on RESOLUTION. After
    # this release nothing counts rows, so THIS is what stands between a second
    # row and a register that commissions nothing.
    base, c = _s4_tree(
        [s4_row, s4b_row],
        also=(dict(s4b_grant, audience={"wallet_ref": "wal-s4-probe-0001",
                                        "holder_ref": s4b_holder}),
              s4b_wallet),
        also_attest=(s4b_attest,),
        top={SEAT_KEYS_FIELD: real_seats + s4b_seats})
    _register_probe("self-test/register-second-row-unresolved", base, c,
                    {"register-grant-mismatch"})

    # `key_id` AND `key_fingerprint` STAY GLOBAL, asserted ACROSS councils --
    # the uniqueness the pair key must not drag with it. A key is one key, and
    # two bodies presenting it are two claims on one identity, so a per-council
    # key namespace would let one private half sign for two bodies with no way
    # to attribute a seat return.
    for field in ("key_id", "key_fingerprint"):
        clash = dict(s4b_seats[1])
        clash[field] = real_seats[0][field]
        expected = {"register-seat-duplicate"}
        if field == "key_fingerprint":
            expected.add("register-seat-fingerprint-mismatch")
        base, c = _s4_tree([s4_row, s4b_row], **s4b_records,
                           top={SEAT_KEYS_FIELD: [real_seats[0], clash]})
        _register_probe(f"self-test/seat-duplicate-across-councils[{field}]",
                        base, c, expected)


# ------------------- register: the intake's row validator -------------------
#
# S4 of add-wallet-carried-review-authority (design D4/D11): the register and
# its reader land TOGETHER or the capability is not realized. The register's
# shape is deliberately NOT a contract schema — D11 rules its schema a
# declared successor until the rule-of-three fires — so THIS function is the
# shape: kindless YAML at a fixed path, parsed strictly, cross-resolved
# against the records repo_scan already indexed.

REGISTER_DIR_PARTS = ("governance", "review-authority")
REGISTER_FILE = "register.yaml"
ATTESTATIONS_DIR = "attestations"
REGISTER_ROW_FIELDS = {
    "row_id", "holder_ref", "wallet_ref", "target_repo", "act",
    "authority_tier", "grant_ref", "expires_at", "state",
}

# wallet-v1.5 (widen-register-reader-for-a-second-council, design D1/D3): THE
# ROW-COUNT CAP IS WITHDRAWN, and the refusal `register-minimal-shape-exceeded`
# is RETIRED BY NAME and re-pointed at nothing (Q-WRR-1, ruled 2026-09-06).
# `REGISTER_MVP_SINGLE_ROW = 1` stood here from wallet-v1.0 and was RE-GROUNDED
# at wallet-v1.2 to bound AUTHORITY ROWS; openxFactory's ratified
# `register-gate-rules-council-seats` commissions a SECOND body, which cannot
# descend from the first row, so the cap was the thing that made a second
# commissioned body unrepresentable. It is NOT raised to two: two is as
# arbitrary as one, buys exactly one body of headroom, and would have to be
# edited again by the third body while saying nothing true about why two was
# right.
#
# WHAT STANDS IN ITS PLACE -- the three invariants of openxFactory's Q-GRC-5
# ruling, each already carrying its OWN precise finding code, so NO NEW CODE is
# added here and no fact acquires a second name (design D5):
#
#   (i)   every AUTHORITY ROW RESOLVES END TO END -- its own scanned wallet, a
#         grant whose audience, acts, objects, tier and expiry match the row, a
#         custody attestation where the row stands at tier `act`, and a COMPUTED
#         expiry in the future. Enforced by check_register's row loop:
#         register-wallet-unresolved, register-wallet-inactive,
#         register-grant-unresolved, register-grant-mismatch,
#         register-tier-act-unattested, register-row-expired,
#         register-row-malformed.
#   (ii)  every per-seat entry ATTACHES TO A ROW THAT COMMISSIONS ITS BODY.
#         Enforced by _check_seat_keys: register-seat-row-unresolved and
#         register-seat-council-mismatch.
#   (iii) the pair (`council_id`, `seat_id`) is UNIQUE -- `key_id` and
#         `key_fingerprint` remaining unique GLOBALLY. Enforced by
#         _check_seat_keys' duplicate table: register-seat-duplicate.
#
# NO NUMERIC BOUND REPLACES THE CAP (Q-WRR-2), and the absence is a DECISION
# rather than an omission: the register is a permanently human-only surface
# where every row is one governed operator act, so its breadth is already
# bounded by what a human can stand behind -- and a number recorded in this
# reader would go stale on the day a body arrived while saying nothing true
# about why that number was right. The self-test block above carries a probe
# per invariant, so an edit that stops resolving one of them reds INSIDE the
# required check every consumer runs.

# wallet-v1.2, design D3: the top level is a CLOSED read set. Validating one
# field at a time closes today's vacuous pass and leaves tomorrow's open -- the
# next governed declaration added to the register would pass unread exactly as
# `revocation_staleness_bound` did (measured: 0 errors, 0 warnings). Closure
# means the next addition CANNOT be made without a reader edit, which is the
# discipline REGISTER_ROW_FIELDS already imposes one level down. The register has
# no schema (design D11); the closure is this reader's job or it is nobody's.
SEAT_KEYS_FIELD = "seat_keys"
STALENESS_BOUND_FIELD = "revocation_staleness_bound"
REGISTER_TOP_LEVEL_FIELDS = {
    "register_version", STALENESS_BOUND_FIELD, "rows", SEAT_KEYS_FIELD,
}
REGISTER_TOP_LEVEL_REQUIRED = {
    "register_version", STALENESS_BOUND_FIELD, "rows",
}

# design D7: exactly seven fields, checked as exact set equality the way rows
# are. The set is chosen by a COMPLETENESS TEST, not by taste: register + wallet
# + grant must be sufficient to derive every required per-seat field of
# hermes-install's projection with nothing invented by the operator, because an
# operator who must invent a value is an operator whose projection can disagree
# with the register. `council_ref` is carried even though the row implies it,
# because it is what gives the unknown-seat refusal something to bite on (D8).
REGISTER_SEAT_FIELDS = {
    "seat_id", "council_ref", "council_id", "key_id", "public_key",
    "key_fingerprint", "authorizing_row",
}

# TWO SPELLINGS OF ONE BODY, both recorded on purpose (design D7).
#
# `council_ref` is the AUTHORITY ATTACHMENT: it must equal the `holder_ref` of
# the row the entry descends from, which the live register spells
# `agent:merge-readiness-council`. `council_id` is the RUNTIME NAME: it is
# carried verbatim into hermes-install's projection, which keys a seat lookup on
# the exact pair `(council_id, seat_id)` and whose fixtures spell the council
# `merge_readiness_council`. The two spellings are not interchangeable and
# neither is derivable from the other by a rule anyone declared, so recording
# only one would force the operator to INVENT the other at projection time --
# and an invented value is a projection that can disagree with the register,
# which is the drift the fingerprint recomputation exists to prevent.
#
# The relationship between them is OBSERVED, and pinned here as a check rather
# than assumed: strip `agent:`, swap `_` for `-`. If a future council's two
# spellings relate differently, THIS READER is the thing that changes, which is
# what it means for the reader to be the shape. Underscores are legal in the
# identifier grammar (`[A-Za-z0-9._:/-]` contains `_`), so neither spelling is
# forced by grammar -- they differ because two consumers named one body twice.
SEAT_COUNCIL_HOLDER_PREFIX = "agent:"

# design D4: the staleness bound's grammar is hermes-install's, deliberately.
# This value is projected VERBATIM into that runtime's projection as
# `projected_from.staleness_bound`, whose schema pins this shape and whose reader
# is a second gate on it. Accepting here what the runtime refuses downstream
# would let a governed value be committed that no projection can ever carry -- a
# refusal moved from where it is cheap to fix to where it parks a convening.
# YEARS AND MONTHS ARE ABSENT ON PURPOSE: a trust window whose width depends on
# the calendar is not a bound anybody declared.
STALENESS_BOUND_RE = re.compile(r"^P(\d+W|(\d+D)?(T(\d+H)?(\d+M)?(\d+S)?)?)$")

# 32 raw bytes of Ed25519 public key as unpadded base64url is exactly 43
# characters. The check is CANONICAL (re-encode and compare), not just a charset
# match, so trailing non-zero bits in the final sextet are refused rather than
# silently truncated into a different key.
#
# THIS LENGTH IS LOAD-BEARING BEYOND CORRECTNESS (design R2). The PRIVATE halves
# of these same keys are stored as 64 lowercase hex characters, so the most
# plausible catastrophic paste into this file -- a seed where a public half
# belongs -- is refused BY SHAPE inside the required check, before it can merge.
# Do not relax this to a laxer pattern.
PUBLIC_KEY_B64U_LEN = 43
FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

# A self-test sentinel meaning "remove this top-level key", so a probe can
# express ABSENCE of a required field without hand-building a register tree.
_ABSENT = object()

# THE FOUR REAL SEAT KEYS, copied verbatim from codexFactory
# `hermes/domain/review-councils/records/2026-08-28-seat-signing-keys-minted.md`
# (merged 78b8fa2). They are in the SELF-TEST, not just in tests/, for one
# reason: the positive probe is the same bytes openxFactory commits to its
# register, so a transcription slip fails inside the pinned validator's own
# self-test -- which every consumer runs -- rather than in the governed file on a
# human-only surface. Each fingerprint RECOMPUTES from the key beside it; that is
# asserted, not assumed.
SEAT_KEY_MINT_RECORD_2026_08_28 = (
    ("lead-quality",
     "bqJJdpCO4dx31e21t6UA4v7b0r0JaxaqmebrjvhK4OI",
     "sha256:a78d5d8fc075a0c771db521f6e4dd5ebec1ae9c76c5209a3bd54983fccb5e781"),
    ("lead-security",
     "pJn1q--LChggWG1x8j50r3yLzGhIvzaq7aWJB-RIc-U",
     "sha256:39f3088f6072d111cd64147cdd171c7efd75423e225c1d4b8c00445af21f878e"),
    ("lead-integration",
     "WBLjZ2fFHGTjw-2XKHFQxzACyuo4yDDOFbeHMfsZMNs",
     "sha256:4d40ee511f5ede92c3843d530eb9d46efa42dbdd22bce07961688ab14004d1f4"),
    ("company-policy-lead",
     "zwKZNuvovOXl_FpGW9Oxjs0IATnlzstlFdT1GlqSvpY",
     "sha256:0b6ad4ab29f2371cc635e392635c796f103a589dab7f5a3dd22b5ca44a504bbb"),
)


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.utcoffset() is not None else None


def _load_attestations(f: Findings, attest_dir: Path,
                       ctx: Context) -> dict[str, dict]:
    """Parse every custody-attestation row under attest_dir into
    wallet_ref -> attestation. Malformed rows are LOUD (error), never
    silently treated as absent: an unparseable attestation must refuse the
    act tier it was recorded to unlock, not degrade it to the cap in
    silence. Rows naming wallets absent from the scan are skipped with a
    note - they are context for holders this tree does not carry."""
    out: dict[str, dict] = {}
    if not attest_dir.is_dir():
        return out
    for path in sorted(attest_dir.glob("*.y*ml")):
        try:
            doc = load_yaml(path)
        except yaml.YAMLError as exc:
            f.error("attestation-unparseable",
                    f"{path}: parse failure: {exc}")
            continue
        ref = doc.get("subject_wallet_ref") if isinstance(doc, dict) else None
        if not isinstance(ref, str) or not ref:
            f.error("attestation-malformed",
                    f"{path}: carries no subject_wallet_ref")
            continue
        if ref not in ctx.wallets:
            f.note(f"attestation {path.name}: subject {ref!r} is not a "
                   f"wallet in this scan; skipped")
            continue
        problems = []
        by = doc.get("verified_by")
        if not isinstance(by, dict) or not all(
                isinstance(by.get(k), str) and by.get(k)
                for k in ("name", "role", "standing")):
            problems.append("verified_by must name name/role/standing")
        against = doc.get("verified_against")
        if not isinstance(against, dict) or not isinstance(
                against.get("method"), str) or not against.get("method"):
            problems.append("verified_against.method missing")
        if "isolation_claimed" not in (against or {}):
            problems.append("verified_against.isolation_claimed missing "
                            "(the honest posture field)")
        model = doc.get("custody_model_attested")
        if not isinstance(model, str) or model not in ctx.custody:
            problems.append(f"custody_model_attested {model!r} is not a "
                            f"closed-set member")
        when = _parse_dt(doc.get("verified_at"))
        if when is None:
            problems.append("verified_at is not an RFC3339 timestamp")
        if problems:
            f.error("attestation-malformed",
                    f"{path}: " + "; ".join(problems))
            continue
        out[ref] = doc
    return out


def _decode_public_key(value: Any) -> bytes | None:
    """32 raw bytes from CANONICAL unpadded base64url, or None.

    Canonical means the value re-encodes to itself: a 43-character string whose
    final sextet carries non-zero trailing bits decodes without complaint under
    the permissive decoder and names a DIFFERENT key than it appears to. Two
    spellings of one key are the defect this whole reader exists to refuse, so
    the round trip is the check rather than the charset.
    """
    if not isinstance(value, str) or len(value) != PUBLIC_KEY_B64U_LEN:
        return None
    try:
        raw = base64.urlsafe_b64decode(value + "=")
    except (ValueError, TypeError):
        return None
    if len(raw) != 32:
        return None
    if base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=") != value:
        return None
    return raw


# `key_fingerprint()`'s one spelling, as the mint record and the runtime both
# compute it: "sha256:" + sha256(raw 32-byte public key).hexdigest(). It is the
# core's function, read through the loaded module: the core computes the same
# value from the declared key set's other encoding, and one spelling has one
# implementation.
_fingerprint_of = core.fingerprint_of_public_key


def _check_staleness_bound(f: Findings, reg: dict, reg_path: Path) -> None:
    """`revocation_staleness_bound` enters the ENFORCED read set (design D4).

    Recorded history, because the class matters more than the field: the S5
    session that landed openxFactory task 7.3 added this governed declaration to
    the register, and the PINNED reader read only `register_version` and `rows`
    at the top level -- so the declaration passed silently, unadjudicated, inside
    a REQUIRED check. That is the vacuous-pass class, and it is the same class
    that kept the four minted council seat keys out of the register.
    """
    if STALENESS_BOUND_FIELD not in reg:
        f.error("register-staleness-bound-missing",
                f"{reg_path}: no {STALENESS_BOUND_FIELD}; a projection of this "
                f"register would have no declared window in which it may be "
                f"believed, and an undeclared window is an unbounded one")
        return
    value = reg[STALENESS_BOUND_FIELD]
    if not isinstance(value, str) or not STALENESS_BOUND_RE.match(value):
        f.error("register-staleness-bound-malformed",
                f"{reg_path}: {STALENESS_BOUND_FIELD} {value!r} is not a "
                f"weeks/days/hours/minutes/seconds ISO-8601 duration; years and "
                f"months are refused because a trust window whose width depends "
                f"on the calendar is not a bound anybody declared")
        return
    # A `T` with no components, and any zero-length window. Zero is not a
    # declaration that revocation is honoured instantly -- it is a declaration
    # that no projection may ever be read, which is a way of turning the gate
    # off that looks like tightening it.
    if value.endswith("T") or not any(
            int(n) for n in re.findall(r"(\d+)", value)):
        f.error("register-staleness-bound-malformed",
                f"{reg_path}: {STALENESS_BOUND_FIELD} {value!r} names a "
                f"zero-length or empty window; no projection could ever be read "
                f"inside it, which disables the gate rather than tightening it")


def _check_seat_keys(f: Findings, reg: dict, reg_path: Path,
                     rows: list, now: datetime) -> None:
    """The per-seat signing-key surface, READ AND ENFORCED (design D1/D2/D7/D8).

    Four Ed25519 keypairs were minted 2026-08-28, one per seat of codexFactory's
    `merge_readiness_council`, and the register had nowhere to put them: a key
    field on a row fails REGISTER_ROW_FIELDS' exact set equality, four per-seat
    rows failed the row-count cap this reader carried until wallet-v1.5, and a
    new top-level block would have passed only because this reader ignored what
    it did not read. This function is that third option done properly.

    SECOND BODY (wallet-v1.5, design D2). The cap is now withdrawn, so this
    surface can carry the seats of MORE THAN ONE commissioned body, and seat
    identity is the PAIR (council_id, seat_id): a seat name repeated under one
    council is still refused, and the same name under two councils is admitted,
    because two bodies commonly seat one ROLE. `key_id` and `key_fingerprint`
    stay unique across the whole file. Every entry still attaches to a row that
    commissions ITS body, which is what keeps a wider register from becoming a
    looser one.

    OPTIONAL BY DESIGN (D10), and the absence is a NOTE. If the surface were
    required, the ordering of three merges across two repositories would become
    load-bearing: any moment at which openxFactory's gitlink points at this
    reader while its register has not yet been edited would be a moment when a
    REQUIRED check refuses a governed file on a PERMANENTLY HUMAN-ONLY surface,
    and the only routine exit from a parked candidate under a sole code owner is
    `--admin` -- the ritual this arc exists to end. The note is what keeps that
    from being leniency: absence becomes VISIBLE in the gate log instead of
    indistinguishable from "read and fine", which is what lets the consumer
    gate's positive-proof step assert on the keys once they are recorded.
    """
    if SEAT_KEYS_FIELD not in reg:
        f.note(f"intake register: no per-seat signing key is recorded; a "
               f"runtime projection built from this register can authorize no "
               f"seat")
        return
    entries = reg[SEAT_KEYS_FIELD]
    if not isinstance(entries, list) or not entries:
        f.error("register-seat-keys-malformed",
                f"{reg_path}: {SEAT_KEYS_FIELD} must be a non-empty list when "
                f"present; an empty surface and an absent one are the same "
                f"declaration, and the absent one is said by omitting the key")
        return

    # Rows usable as an authority for a seat: indexed by row_id, ACTIVE, and
    # unexpired by COMPUTED time (N8 -- the stored `state` is never truth about
    # expiry). A row this reader has already refused is not promoted to an
    # authority here by being merely present.
    usable: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != REGISTER_ROW_FIELDS:
            continue  # a row this reader has already refused is not an authority
        if not isinstance(row.get("row_id"), str):
            continue
        expires = _parse_dt(row.get("expires_at"))
        if row.get("state") == "active" and expires is not None and expires > now:
            usable[row["row_id"]] = row

    # wallet-v1.5 (widen-register-reader-for-a-second-council, design D2): the
    # `seat_id` table is keyed on the PAIR (council_id, seat_id); `key_id` and
    # `key_fingerprint` stay keyed GLOBALLY, on the value alone.
    #
    # WHY THE PAIR, and it is not this reader's invention. hermes-install's
    # `derive_projection` -- the runtime that CONSUMES this register -- already
    # keys its own duplicate table on (council_id, seat_id) and refuses only
    # "the register projects <council>/<seat> more than once". Two bodies
    # commonly seat the same ROLE (`lead-security` is a role, not a person), and
    # with a global seat namespace WHICH of a body's seats resolve depends on
    # what a DIFFERENT body happens to call its own. The reader adopts the key
    # its consumer already uses, which removes a disagreement between two
    # programs reading one file rather than inventing a third opinion.
    #
    # WHY key_id AND key_fingerprint DO NOT MOVE WITH IT. A key is one key. Two
    # entries sharing a fingerprint are two claims on one identity, and if they
    # sit under DIFFERENT councils the claim is worse, not better: one private
    # half would sign for two bodies and a seat return could not be attributed.
    seen: dict[str, dict[Any, int]] = {"seat_id": {}, "key_id": {},
                                       "key_fingerprint": {}}
    read = 0
    for i, entry in enumerate(entries):
        label = f"{reg_path}:{SEAT_KEYS_FIELD}[{i}]"
        # `read` counts entries ADJUDICATED CLEAN, never entries PARSED. The
        # difference is the whole point of this surface: the note a consumer gate
        # asserts on must say how many keys the reader stood behind, because a
        # count of `len(entries)` would prove parsing and prove nothing else --
        # which is the vacuous pass that kept these keys out of the register.
        before = len(f.errors)
        if not isinstance(entry, dict):
            f.error("register-seat-keys-malformed", f"{label}: not a mapping")
            continue
        fields = set(entry)
        if fields != REGISTER_SEAT_FIELDS:
            missing = sorted(REGISTER_SEAT_FIELDS - fields)
            extra = sorted(fields - REGISTER_SEAT_FIELDS)
            f.error("register-seat-keys-malformed",
                    f"{label}: field set mismatch (missing={missing}, "
                    f"unknown={extra}); the register has no schema so THIS "
                    f"reader is the shape, and it is strict")
            continue
        if not all(isinstance(entry[k], str) and entry[k]
                   for k in REGISTER_SEAT_FIELDS):
            f.error("register-seat-keys-malformed",
                    f"{label}: every field is a non-empty string")
            continue
        seat = entry["seat_id"]

        # Duplicates are refused, never resolved by file order: a register
        # naming one seat twice has two answers to "which key is this seat's
        # root", and picking either is choosing which authority to believe.
        council_id = entry["council_id"]
        for field in seen:
            scoped = field == "seat_id"
            seen_key = (council_id, entry[field]) if scoped else entry[field]
            first = seen[field].get(seen_key)
            if first is not None:
                if scoped:
                    f.error("register-seat-duplicate",
                            f"{label} ({seat}): {field} {entry[field]!r} is "
                            f"already recorded under council {council_id!r} at "
                            f"{SEAT_KEYS_FIELD}[{first}]; a repeated {field} "
                            f"within ONE council is refused rather than resolved "
                            f"by file order, because that council then has two "
                            f"answers to which key is that seat's root. The same "
                            f"seat name under a DIFFERENT council is not a "
                            f"duplicate: two bodies commonly seat one role")
                else:
                    f.error("register-seat-duplicate",
                            f"{label} ({seat}): {field} {entry[field]!r} is "
                            f"already recorded at {SEAT_KEYS_FIELD}[{first}]; a "
                            f"repeated {field} is refused rather than resolved "
                            f"by file order, and this uniqueness is GLOBAL "
                            f"across the file whatever the councils -- a key is "
                            f"one key, and two bodies presenting it are two "
                            f"claims on one identity")
            else:
                seen[field][seen_key] = i

        raw = _decode_public_key(entry["public_key"])
        if raw is None:
            f.error("register-seat-key-malformed",
                    f"{label} ({seat}): public_key is not "
                    f"{PUBLIC_KEY_B64U_LEN} characters of CANONICAL unpadded "
                    f"base64url over 32 raw bytes; note that a 64-hex value is "
                    f"the encoding of a PRIVATE seed and is refused here by "
                    f"shape")
        if not FINGERPRINT_RE.match(entry["key_fingerprint"]):
            f.error("register-seat-fingerprint-malformed",
                    f"{label} ({seat}): key_fingerprint "
                    f"{entry['key_fingerprint']!r} is not "
                    f"sha256:<64 lowercase hex>")
        elif raw is not None and _fingerprint_of(raw) != entry["key_fingerprint"]:
            f.error("register-seat-fingerprint-mismatch",
                    f"{label} ({seat}): key_fingerprint does not recompute from "
                    f"public_key; two spellings of one key's identity mean one "
                    f"of them is wrong, and choosing either is choosing which "
                    f"authority to believe")

        # The two spellings must denote ONE body. Checked before the row
        # attachment so an operator who mistyped the runtime name is told that,
        # rather than being told the entry is attached to the wrong council.
        if entry["council_ref"] != (
                SEAT_COUNCIL_HOLDER_PREFIX
                + entry["council_id"].replace("_", "-")):
            f.error("register-seat-council-spelling",
                    f"{label} ({seat}): council_ref {entry['council_ref']!r} and "
                    f"council_id {entry['council_id']!r} do not denote one body "
                    f"(expected {SEAT_COUNCIL_HOLDER_PREFIX}"
                    f"{entry['council_id'].replace('_', '-')!r}); the register "
                    f"spelling anchors the authority and the runtime spelling is "
                    f"projected verbatim, so a disagreement between them is a "
                    f"projection that can name a body this row does not "
                    f"commission")

        row = usable.get(entry["authorizing_row"])
        if row is None:
            f.error("register-seat-row-unresolved",
                    f"{label} ({seat}): authorizing_row "
                    f"{entry['authorizing_row']!r} resolves to no ACTIVE, "
                    f"unexpired row in this register; a key descending from no "
                    f"live authority descends from nothing")
        elif row.get("holder_ref") != entry["council_ref"]:
            # D8: the enforceable meaning of "an unknown seat" at THIS altitude.
            # The council's seat roster is governed in codexFactory
            # (hermes/domain/review-councils/), a repository this validator has
            # no read path into and must not acquire one -- so the reader cannot
            # say "that seat does not exist". It CAN say "that entry is not
            # attached to a body this register commissions", which is the
            # failure the check is actually for. Resolving seat ids against the
            # roster is a named successor.
            f.error("register-seat-council-mismatch",
                    f"{label} ({seat}): council_ref {entry['council_ref']!r} is "
                    f"not the holder_ref {row.get('holder_ref')!r} that row "
                    f"{entry['authorizing_row']!r} commissions; this entry "
                    f"names a body the register does not seat")
        if len(f.errors) == before:
            read += 1

    # A NOTE, never a warning (design D5): LedgerxFactory runs this validator
    # with --strict, where report() reds a run on warnings, so a new warning
    # would red-line a required check in a repository that never asked for it.
    #
    # The count is the evidence a consumer gate asserts on POSITIVELY, and it is
    # the ADJUDICATED count: any entry the reader refused is excluded, so
    # `read < recorded` always travels with at least one error and a green run
    # carrying this note has stood behind every key it names.
    f.note(f"intake register: {read} of {len(entries)} per-seat signing key(s) "
           f"adjudicated and resolved")


def check_register(f: Findings, base_dir: Path, ctx: Context,
                   now: datetime | None = None) -> None:
    """The register reader. Obligations exactly as ratified: every active
    review-class grant in the scanned tree needs a backing ACTIVE row -- and
    "active" is READ, not assumed: a grant stamped `revoked` is terminal and
    owes no row (wallet-v1.4; see REVOKED IS EXEMPT at the closing loop);
    every row resolves end to end (wallet, grant, computed expiry, act-tier
    attestation); the stored `state` field is checked AGAINST computed time,
    never trusted (N8). Absent register + no review-class grants is the
    legitimate posture of every consumer repository that has not cold-started
    the arc.

    BREADTH IS NOT COUNTED (wallet-v1.5, design D1/D3). The register carries one
    AUTHORITY ROW per commissioned body and this reader bounds how many bodies
    it may commission by INVARIANTS rather than by a number: every row resolves
    end to end, every seat entry attaches to a row that commissions its body,
    and (council_id, seat_id) is unique. The withdrawn refusal
    `register-minimal-shape-exceeded` is retired by name and re-pointed at
    nothing; see the comment where REGISTER_MVP_SINGLE_ROW used to stand."""
    now = now or datetime.now(timezone.utc)
    reg_path = Path(base_dir).joinpath(*REGISTER_DIR_PARTS, REGISTER_FILE)
    if not reg_path.exists():
        # wallet-v1.4: `state == "revoked"` is exempt here for exactly the
        # reasons spelled out at the closing loop's REVOKED IS EXEMPT block --
        # this branch states the SAME obligation for the absent-register case,
        # and the two must agree or a consumer's finding would depend on
        # whether it has cold-started the register yet. A tree carrying only
        # revoked review-class grants and no register is the shape a consumer
        # has after revoking its way out of the arc, and it is legitimate.
        review_holders = [
            gid for gid, g in ctx.grants.items()
            if isinstance(g.get("scope"), dict)
            and REVIEW_ACT_TOKEN in _hashable_set(g["scope"].get("acts"))
            and g.get("state") != "revoked"
        ]
        if review_holders:
            f.error("register-no-active-row",
                    f"active REVIEW-class grants {sorted(review_holders)} "
                    f"exist but {reg_path} does not exist; authority claimed "
                    f"outside the ratified register confers nothing")
        else:
            f.note("no intake register at this tree; nothing to read")
        return

    try:
        reg = load_yaml(reg_path)
    except yaml.YAMLError as exc:
        f.error("register-unparseable", f"{reg_path}: parse failure: {exc}")
        return
    if not isinstance(reg, dict):
        f.error("register-unparseable", f"{reg_path}: not a mapping")
        return
    if reg.get("register_version") != 1:
        f.error("register-version-unknown",
                f"{reg_path}: register_version {reg.get('register_version')!r} "
                f"is not 1")
        return

    # wallet-v1.2, design D3: the top level is a CLOSED read set, checked BEFORE
    # anything is adjudicated. An unrecognized key is refused rather than ignored
    # -- the reader ignoring what it does not read is exactly why the four minted
    # seat keys could not be recorded, and why a governed staleness bound sat in
    # this file unadjudicated inside a REQUIRED check.
    unknown = sorted(set(reg) - REGISTER_TOP_LEVEL_FIELDS)
    if unknown:
        f.error("register-top-level-unknown",
                f"{reg_path}: unknown top-level key(s) {unknown}; the register "
                f"has no schema so THIS reader is the shape, and a declaration "
                f"it does not read confers nothing")
    _check_staleness_bound(f, reg, reg_path)

    rows = reg.get("rows")
    if not isinstance(rows, list):
        f.error("register-row-malformed",
                f"{reg_path}: `rows` must be a list")
        return
    if not rows:
        # NOT an early return: an empty register still owes the reader's
        # headline obligation - any active REVIEW-class grant in this tree is
        # then precisely "a convening admitting a holder with no active row".
        f.error("register-row-malformed",
                f"{reg_path}: `rows` must be a non-empty list")
        rows = []
    # wallet-v1.1 (P2b, design D3): the durable positive line. Before this the
    # reader was SILENT on success -- the only output naming the register was a
    # failure finding, and the absent-register note above names no path at all,
    # so "the register was read" could only be inferred from a conjunction of
    # absences. Emitted HERE, at the earliest point where both reported facts
    # are known, so it says "the register was read and its rows parsed" rather
    # than "the register was clean": an auditor most needs to know WHICH
    # register produced a row finding on exactly the runs that have one.
    #
    # A NOTE, never a warning: `report()` reds a `--strict` run on warnings and
    # LedgerxFactory runs `--strict`, so promoting this line for visibility
    # would red-line a required check in a repository that never asked for it.
    #
    # The path is RELATIVE to the scan root because the consumer gate's
    # positive-proof test asserts on this line, and an absolute path differs
    # between a developer's checkout and a runner's workspace.
    try:
        shown = reg_path.relative_to(Path(base_dir))
    except ValueError:  # pragma: no cover - reg_path is built from base_dir
        shown = reg_path
    f.note(f"intake register read: {shown} ({len(rows)} row(s))")

    # NO ROW-COUNT REFUSAL IS EMITTED HERE, and the absence is deliberate
    # (wallet-v1.5, design D1/D3; Q-WRR-1 and Q-WRR-2). `register-minimal-shape-
    # exceeded` was emitted at this point and is RETIRED BY NAME: the register
    # commissions one authority row per body, with no bound on how many bodies,
    # and what admits a row is what it RESOLVES TO rather than its ordinal
    # position in the file. The three invariants that replace the count are
    # enumerated where the constant used to stand, and every one of them is
    # enforced below or in _check_seat_keys with its own existing code.

    _check_seat_keys(f, reg, reg_path, rows, now)

    attestations = _load_attestations(f, Path(base_dir).joinpath(
        *REGISTER_DIR_PARTS, ATTESTATIONS_DIR), ctx)

    active_rows: set[str] = set()
    for i, row in enumerate(rows):
        label = f"{reg_path}:rows[{i}]"
        if not isinstance(row, dict):
            f.error("register-row-malformed", f"{label}: not a mapping")
            continue
        fields = set(row)
        if fields != REGISTER_ROW_FIELDS:
            missing = sorted(REGISTER_ROW_FIELDS - fields)
            extra = sorted(fields - REGISTER_ROW_FIELDS)
            f.error("register-row-malformed",
                    f"{label}: field set mismatch (missing={missing}, "
                    f"unknown={extra}); the register has no schema so THIS "
                    f"reader is the shape, and it is strict")
            continue
        row_id = row["row_id"]

        wallet = ctx.wallets.get(row["wallet_ref"])
        if wallet is None:
            f.error("register-wallet-unresolved",
                    f"{label} ({row_id}): wallet_ref {row['wallet_ref']!r} "
                    f"resolves to no scanned wallet record")
            continue
        if wallet.get("state") != "active":
            f.error("register-wallet-inactive",
                    f"{label} ({row_id}): audience wallet "
                    f"{row['wallet_ref']!r} is state {wallet.get('state')!r}")

        if row["act"] != REVIEW_ACT_TOKEN:
            f.error("register-act-not-review",
                    f"{label} ({row_id}): act {row['act']!r} is not the "
                    f"canonical review token")
        if row["authority_tier"] == "act_unsupervised":
            f.error("register-tier-refused",
                    f"{label} ({row_id}): act_unsupervised is refused for "
                    f"review authority outright")
        elif row["authority_tier"] not in ctx.tier_rank:
            f.error("register-tier-unknown",
                    f"{label} ({row_id}): authority_tier "
                    f"{row['authority_tier']!r} is outside the closed ladder")

        expires = _parse_dt(row["expires_at"])
        if expires is None:
            f.error("register-row-malformed",
                    f"{label} ({row_id}): expires_at is not RFC3339")
            continue
        if expires <= now:
            f.error("register-row-expired",
                    f"{label} ({row_id}): COMPUTED expiry "
                    f"{row['expires_at']} has passed; the stored state "
                    f"{row['state']!r} is not truth about expiry (N8)")
        elif row["state"] == "active":
            active_rows.add(row_id)

        grant = ctx.grants.get(row["grant_ref"])
        if grant is None:
            f.error("register-grant-unresolved",
                    f"{label} ({row_id}): grant_ref {row['grant_ref']!r} "
                    f"resolves to no scanned grant")
            continue
        g_scope = grant.get("scope") if isinstance(grant.get("scope"), dict) \
            else {}
        g_aud = grant.get("audience") if isinstance(
            grant.get("audience"), dict) else {}
        mismatches = []
        if g_aud.get("wallet_ref") != row["wallet_ref"]:
            mismatches.append("audience.wallet_ref")
        if g_aud.get("holder_ref") != row["holder_ref"]:
            mismatches.append("audience.holder_ref")
        if REVIEW_ACT_TOKEN not in _hashable_set(g_scope.get("acts")):
            mismatches.append("acts lacks the review token")
        if _hashable_set(g_scope.get("objects")) != {row["target_repo"]}:
            mismatches.append("objects differs from target_repo")
        if g_scope.get("authority_tier") != row["authority_tier"]:
            mismatches.append("authority_tier")
        g_exp = _parse_dt(grant.get("expires_at"))
        r_exp = _parse_dt(row["expires_at"])
        if g_exp is None or r_exp is None or g_exp != r_exp:
            mismatches.append("expires_at differs between row and grant")
        if grant.get("state") != "active":
            mismatches.append(f"grant state {grant.get('state')!r}")
        if g_exp is not None and g_exp <= now and grant.get("state") == \
                "active":
            f.error("grant-state-stale",
                    f"{row['grant_ref']!r}: stored state 'active' but "
                    f"COMPUTED expiry {grant.get('expires_at')} has passed "
                    f"(N8: stale state is a finding, not truth)")
        if mismatches:
            f.error("register-grant-mismatch",
                    f"{label} ({row_id}): grant {row['grant_ref']!r} does "
                    f"not back the row: " + "; ".join(mismatches))

        if row["authority_tier"] == "act" and row["wallet_ref"] not in \
                attestations:
            f.error("register-tier-act-unattested",
                    f"{label} ({row_id}): tier act requires a parseable "
                    f"custody attestation for wallet "
                    f"{row['wallet_ref']!r}; none resolved - the unattested "
                    f"cap applies and this row cannot stand at act")

    # The headline obligation, inverted for CI: an active REVIEW-class grant
    # whose holder carries no ACTIVE register row means a convening could
    # admit authority the register never granted.
    #
    # REVOKED IS EXEMPT (wallet-v1.4). Until this release the loop filtered on
    # the review token ALONE and never read the grant's own `state`, so it
    # demanded a backing active row for a grant it had itself been told was
    # revoked -- while the row-count cap this reader then carried
    # (`REGISTER_MVP_SINGLE_ROW`, RETIRED at wallet-v1.5) forbade the second row
    # such a demand would need. The reader could therefore not represent ANY
    # re-issuance: revoking a review-class grant and issuing its successor is
    # the runbook's §5.1 act, and every consumer that performed it went red on
    # a correct tree. openxFactory's S5 register act (2026-09-02, PR #583) is
    # the act that found it.
    #
    # WHY `== "revoked"` AND NOT `!= "active"`. The broader test would also
    # exempt a grant merely STAMPED `expired`, and this reader has no inverse
    # check for stored-expired-with-a-future `expires_at` -- N8 is that stored
    # state is checked AGAINST computed time and never trusted, so a state the
    # reader cannot contradict must not be allowed to switch an obligation off.
    # `revoked` is different in kind: it is the TERMINAL fact of the ratified
    # drift-cascade rule (a revoked grant never returns to active; authority
    # resumes only as a NEW grant), it is the exact state §5.1 re-issuance
    # produces, and it is backstopped -- `revocation-unrecorded` refuses a
    # grant stamped `revoked` that carries no `revocation` block recording when
    # and why.
    #
    # NEITHER VARIANT WEAKENS THE GUARD, because this loop is only the
    # grant->row direction. The row->grant direction still runs above and
    # appends `grant state ...` to `mismatches`, so a row pointing at a revoked
    # grant is still refused with `register-grant-mismatch`; and
    # `_revoked_ancestor` still refuses every exercise up a revoked chain. What
    # is exempted here is exactly a revoked grant that NO row points at -- a
    # historical record, which is what a superseded grant is supposed to be.
    for gid, g in sorted(ctx.grants.items()):
        scope = g.get("scope") if isinstance(g.get("scope"), dict) else {}
        if REVIEW_ACT_TOKEN not in _hashable_set(scope.get("acts")):
            continue
        if g.get("state") == "revoked":
            continue  # wallet-v1.4 -- see REVOKED IS EXEMPT below
        backed = any(
            isinstance(r, dict) and r.get("grant_ref") == gid
            and r.get("state") == "active"
            and (_parse_dt(r.get("expires_at")) or now) > now
            for r in rows if isinstance(r, dict))
        if not backed:
            f.error("register-no-active-row",
                    f"active REVIEW-class grant {gid!r} has no backing "
                    f"active register row; admitting a convening for this "
                    f"holder would confer authority the register never "
                    f"granted")


# --------------------------- composition ---------------------------

# Rule (g)'s binding for every repo scan through this entrypoint: the envelope
# node the pre-split validator read, at the path it read it from, and the label
# that makes the core's vocabulary note the line it always printed.
VOCABULARY_BINDING = {
    "document": ENVELOPE_SCHEMA_PATH,
    "pointer": ["properties", "job", "properties", "approval_policy",
                "properties"],
    "label": str(ENVELOPE_SCHEMA_PATH.relative_to(ROOT)),
}


def compose() -> None:
    """Bind the envelope and register this file's rules at the core's extension
    points. A requirement id the core already declares would REWRITE a core
    row, which this adapter never does, so it refuses instead.

    The core's `main()` builds its argparse description from its module
    `__doc__`, so this file's docstring replaces it: `--help` through this
    entrypoint describes what RUNS here (the adapter, rule (t), rule (u), the
    binding), not the core alone."""
    clash = sorted(set(ADAPTER_REQUIREMENTS) & set(core.REQUIREMENTS))
    if clash:
        raise CompositionRefusal(
            "core-unloadable",
            f"the pinned core already declares requirement(s) {clash}; this "
            f"adapter adds rows to the core's closure and never rewrites one",
            CORE_REMEDIATION)
    core.__doc__ = __doc__
    core.VOCABULARY_BINDING = VOCABULARY_BINDING
    core.REQUIREMENTS.update(ADAPTER_REQUIREMENTS)
    core.GRANT_RULES.append(check_review_issuer)
    core.SELF_TEST_HOOKS.append(self_test_review_authority)
    core.SELF_TEST_TAIL_HOOKS.append(self_test_register_reader)
    core.TREE_CHECKS.append(check_register)


def main() -> int:
    if not ENVELOPE_SCHEMA_PATH.is_file():
        print(f"ERROR {ENVELOPE_SCHEMA_PATH} not found; the approval-scope "
              f"vocabulary is read from the canonical job envelope",
              file=sys.stderr)
        return 2
    try:
        compose()
    except CompositionRefusal as exc:
        print(exc, file=sys.stderr)
        return 2
    return core.main()


if __name__ == "__main__":
    sys.exit(main())
