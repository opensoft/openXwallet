# Tasks: split-openwallet-neutral-core

Lane: openXwallet-2

OpenSpec ratifies the boundary; Speckit builds it. Each group from §2 on is
realized as its own Speckit feature in `design.md`'s migration order, and
nothing from §2 on is legal before §1.2 is ticked.

**Tags.** Untagged = openXwallet. The openWallet PROJECT is three repositories
(RULED Q3): `[openWallet-root]` = `opensoft/openWallet`, the assembly root;
`[openWallet-spec]` = `opensoft/openWallet-spec`; `[openWallet-code]` =
`opensoft/openWallet-code`; `[openWallet]` = all three. `[openxFactory]`,
`[LedgerxWallet]`, `[LedgerxFactory]`, `[codexFactory]`, `[xFactory]` = that
repository. `[OPERATOR]` = only Brett can perform it — a ratification, a
repository creation, a scaffold into `opensoft`, a ruleset, a tag.
`[GOVERNANCE]` = it needs a ruling first.

## 1. Governance

- [x] 1.1 Author this packet. `python3 scripts/validate-openspec-cli-pin.py --all
      --no-cache --tarball tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz`
      clean at `--strict` for every change and spec.
- [x] 1.2 **[OPERATOR] [GOVERNANCE]** Ratify or return this proposal. The prefix
      ("keep the prefix"), Q1–Q7 and the spec leg's gate (3.6) are already
      RULED and are not re-asked.
      **RATIFIED** — Brett Heap, operator authority, 2026-10-08T17:10:47Z,
      verbatim: "ratify 26 and merge" (head
      `2ae4eee1885536297e5653e64b6abb1b85cc8e9e`).
      See `proposal.md` "## Status". Ruling:
      https://github.com/opensoft/openXwallet/pull/26#issuecomment-6065121015
- [x] 1.3 Q1–Q6 RULED by Brett Heap in session on 2026-10-08, by multiple
      choice — recorded at 2026-10-08T16:30:50Z; taken in session minutes
      earlier by multiple choice — and encoded beside their questions in
      `proposal.md`, in `design.md` D4–D7, and in `.openspec.yaml`
      `origin.rulings`. Q3 overrode its recommendation; the packet was reworked
      to the three-leg shape, and the pinned CLI gate re-run clean.
- [x] 1.3a Q7 and the spec leg's OpenSpec-gate question (3.6), both raised by
      Q3's ruling, RULED by Brett Heap in session on 2026-10-08, by multiple
      choice — recorded at 2026-10-08T17:01:43Z; taken in session minutes
      earlier by multiple choice:
      - Q7 "Code leg, declared override (Recommended)": contracts, corpus and
        validator stay together in `opensoft/openWallet-code` at today's
        relative paths, and the override of openRepoShape's `spec-governance`
        default is declared in the carve manifest (2.5);
      - 3.6 "Vendor the tarball (Recommended)".

      Both are encoded in `proposal.md`, `design.md` D7 and `.openspec.yaml`
      `origin.rulings`.
- [x] 1.4 On ratification: `Status: ratified`, the `Ratified:` line with the word
      verbatim, and `.openspec.yaml` `approved_by` / `approved_on` filled. Every
      question is already ruled and encoded beside itself.
      **DONE 2026-10-08**, performed by the ratification itself (1.2) and
      landed with PR #26 at merge `bf2dd4db88edbb873d067425b16dacd3784fbaf5`
      (its head, the commit recording the ratification, is
      `fe0e8505f8a0678f5dd6b419c0f78b3c51ace8d6`).
      - `proposal.md` "## Status" reads `Status: ratified` and **Ratified by
        Brett Heap (openXwallet operator authority), in session,
        2026-10-08T17:10:47Z, verbatim: "ratify 26 and merge"**, the change as
        authored at head `2ae4eee1885536297e5653e64b6abb1b85cc8e9e`.
      - `.openspec.yaml` carries `approved_by: Brett Heap (openXwallet
        operator authority)` and `approved_on: 2026-10-08`.

## 2. Before the carve — this repository

- [x] 2.1 Archive `add-multi-key-wallets` with the pinned CLI (its realization
      evidence is in its own `tasks.md`), so its four MODIFIED requirements are
      promoted text before they travel.
      **DONE 2026-10-08** —
      `openspec/changes/archive/2026-10-08-add-multi-key-wallets/`, archived
      with the pinned @fission-ai/openspec@1.12.0 via
      scripts/install-pinned-openspec-cli.py (`~ 4 modified` to `openxwallet`,
      as D0 measured). Archive-time evidence and the full gate bar are recorded
      in that directory's `tasks.md`. Measured there: the pinned gate reads
      5 passed, 1 failed — `add-composition-drift-cascade`'s MODIFIED
      *Revocation propagates through the chain* omits the promoted scenario
      "retiring one key does not revoke the wallet", the collision D0 recorded;
      its cure is 8.1's rebase, not this task's.
- [x] 2.2 Reflow the wrapped scenario-bullet lines in the promoted
      `openxwallet` and `openxwallet-agent-profile` specs onto their bullets — an
      editorial, content-preserving commit ratified by this change, as
      `add-multi-key-wallets` task 6.4 ratified its own `## Purpose` edit.
      MEASURED on 1.12.0 (`design.md` D0): seven such lines after 2.1, and this
      change's archive cannot retire the capabilities while they stand.
      **DONE 2026-10-08**, landed by the reflow PR. Seven joins, all in
      `openxwallet` (line numbers as at `c1c97e5`; continuation joined onto
      its bullet with one space): 41+42 "record of another holder's key",
      56+57 "before sets were expressible", 130+131 "failure", 138+139
      "custody, never about adding a stronger key beside it", 168+169 "than
      passed over", 170+171 "keys signed", 222+223 "constraint named".
      `openxwallet-agent-profile` has none, by the same measurement. The
      whitespace-insensitive diff of the spec before and after is EMPTY. In a
      scratch copy on the pinned 1.12.0, `archive split-openwallet-neutral-core
      --yes` WITHOUT the reflow still refuses ("'openxwallet' declares
      retire_capabilities, but the spec holds content the merge cannot safely
      account for …", aborted), and WITH it reads `Totals: + 5, ~ 0, - 11`,
      both capability specs retired and `openxwallet-factory-binding`
      created, as D0 measured. Not archived in this tree.
- [x] 2.3 Name the CARVE COMMIT: an openXwallet `main` commit after 2.2, never
      HEAD.
      **DONE 2026-10-08** — `CARVE_COMMIT =
      90111df262d6f54f7e82651d860adc12345f83f4`, `main` at the merge of PR #28,
      after 2.1 and 2.2. Named by Brett Heap, operator authority, in session,
      2026-10-08T18:07:19Z, verbatim: "name 90111df as the carve commit, do 2.4
      and 2.5"; recorded on issue #25
      (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6066081858).
      Written into `design.md` D7 and the Migration plan, and into
      `proposal.md`'s `code_surface`.
- [x] 2.4 Re-measure every line range in `design.md` D3 at that commit; a range
      that moved is corrected in the plan, never assumed.
      **DONE 2026-10-08** — at `90111df`, every range D3 cites was re-read with
      `grep -n` for its anchor and `sed -n` for its first and last line. Covered:
      the constants, `ENVELOPE_SCHEMA_PATH`, rule (t)'s constants and check, the
      (f)/(h) literals, the requirement rows, the self-test blocks, the register
      block, `sweep_candidates`, `repo_scan` with its `check_register` call, and
      `main()`'s envelope exit, vocabulary read and note. Also re-read:
      `contracts/manifest.yaml:69-70`. Every range is unchanged, and the
      validator is the same blob as at `b7c6e0b` (`08a4b5c7`). So no range was
      corrected. One imprecision, not a move, is recorded in D3: the `:337`
      pointer's path literal sits on `:338`.
- [x] 2.5 Author `docs/openwallet-carve-manifest.yaml` at the carve commit, in
      openDox's grammar plus `retained_here` (`design.md` D7): one row per
      tracked path, `destination_path` equal to `source_path` on every moved
      row; a tracked path in no row or in two rows REFUSES. Every row whose leg
      departs from openRepoShape's `path-classification.yaml` default carries
      the rule it overrides and its authority: the 73 contract rows to the code
      leg under RULED Q7, and the 9 release-identity rows to the root as
      PROPOSED (`design.md` D7).
      **DONE 2026-10-08** under the same ruling as 2.3 —
      `docs/openwallet-carve-manifest.yaml`, `carve_commit` `90111df`,
      `phase: carve`. Checked by `scripts/validate-carve-manifest.py` (it
      mirrors openxFactory's checker, adapted to this grammar), which
      `tests/carve_manifest/test_carve_manifest.py` drives in `pytest-suite`.
      - Rows: 232, one per tracked path.
      - Dispositions: 120 `moved_verbatim`, 8 `moved_with_declared_edit`,
        104 `not_moved`.
      - Legs: 80 `openwallet_code`, 38 `openwallet_spec`, 10
        `openwallet_root`.
      - `retained_here`: 124 `kept`, 106 `shed`, 2 `retired_by_archive`.
      - Overrides: openRepoShape's classifier at `7f84ca4` was run over all
        232 paths. Exactly 82 moved rows depart from its default, all from
        `spec-governance`: 73 under RULED Q7 and 9 PROPOSED. D7's 73 and 9
        held.
      - Declared edits: 1,884 lines on the 8 edited rows, in D7's five
        classes.
      - Checker verdict at `90111df`: `OK … 128 digest(s) recomputed …
        232 tracked path(s) at the carve commit, each in exactly one row`.
      - CI: the new `.github/workflows/carve-manifest.yml` (job
        `carve-manifest`, `fetch-depth: 0`) runs the checker and the test.
        `pytest-suite`, which is depth 1 and a carved row, is not edited; there
        the real-repository test skips loudly, naming `90111df` and that
        workflow. Making `carve-manifest` REQUIRED is Brett's console act.

## 3. openWallet's birth — three public repositories `[openWallet]`

- [x] 3.1 **[OPERATOR]** The name check for `openWallet`, `openWallet-spec` and
      `openWallet-code` — case variants in the organisation and an unscoped fork
      search — recorded BEFORE creation. On any hit, stop.
      **DONE 2026-10-08**, before creation, on Brett Heap's word in session,
      verbatim: "start group 3". `gh repo view` for `opensoft/openWallet`,
      `opensoft/openWallet-spec`, `opensoft/openWallet-code` and the case
      variants `openwallet`, `openwallet-spec`, `openwallet-code` and
      `OpenWallet`: none resolved. `gh search repos openwallet --owner
      opensoft`: no hit. The unscoped search found three unrelated third-party
      repositories named openwallet or OpenWallet under other owners
      (blocktree, Abhimanyu121, kyai), none a fork and none in the
      organisation. No hit, so no stop. Recorded on issue #25
      (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6067172637).
- [x] 3.2 **[OPERATOR]** The scaffold, from a pinned openRepoShape commit:
      `scaffold-project.py --org opensoft --project openWallet --visibility
      public --elected-by "Brett Heap" --elected-on 2026-10-08`, or the guided
      `setup.sh` with the same flags. The guided front door refuses `--org
      opensoft` without `--allow-upstream-org`, which is Brett's to pass and
      never an agent's.
      **DONE 2026-10-08** on Brett Heap's word in session, verbatim: "start
      group 3". Run from openRepoShape `main` at
      `7f84ca42ca86a8902928345109d2bf6bad87bd91` (tree `3be52767e727…`),
      after a `--dry-run` that matched `design.md` D7 line for line, with
      exactly the flags above. Created and pushed, all PUBLIC, topic
      `xf-project-openwallet`, default branch `main`:
      - assembly `opensoft/openWallet` at `84a0569e3b81`;
      - spec leg `opensoft/openWallet-spec` at `72eca87cedbf` (tree
        `b341b347574f…`);
      - code leg `opensoft/openWallet-code` at `9cabda85f8c5` (tree
        `b7eba3104569…`).

      `scaffold-project.py` carries no upstream-org guard, so no flag was
      passed; this is recorded as the operator's act, on his word.
- [x] 3.3 Verify the scaffold's `project.yaml` against `design.md` D7:
      - `elected_by: "Brett Heap"`, `elected_on: 2026-10-08`;
      - `topic: xf-project-openwallet`, `visibility: public`, `tracking_branch: main`;
      - `shape:` pinning openRepoShape by commit and `sorted-ls-tree-r-v1` tree
        digest, equal to `contracts/shape-pin.yaml`;
      - `neutral_product_pins: []`;
      - the three legs with their `naming:` records.

      Then check GitHub: `gh repo view` reads PUBLIC for all three, and each
      repository carries the topic.

      **DONE 2026-10-08**, on the three repositories as created.
      - In the assembly root, `make bootstrap` reads `bootstrap ok`: the legs
        on `main` at their pins; `manifest ok: openWallet (openwallet), 3
        legs`; both gitlinks equal `contracts/{spec,code}-pin.yaml`, the tree
        digests recomputing; the 11 copied shape files match
        `contracts/shape-pin.yaml`.
      - `project.yaml` reads `elected_by: "Brett Heap"`, `elected_on:
        2026-10-08`, `topic: xf-project-openwallet`, `visibility: public` and
        `tracking_branch: main`; `shape:` pins openRepoShape at commit
        `7f84ca42…` with `sorted-ls-tree-r-v1` tree digest `3be52767e727…`,
        equal to the shape pin; `neutral_product_pins: []`; three legs with
        `naming:` records (assembly `neutral-product`, legs `project-leg`).
      - GitHub: `gh repo view` reads PUBLIC for all three, each carrying the
        topic.
- [x] 3.4 `[openWallet-root]` The cutover runbook, authored BEFORE the carve, a
      rollback per phase written before the phase; `.specify/` bootstrapped at
      the root.
      **DONE 2026-10-08** on Brett Heap's words in session, verbatim: "start
      group 3" and "land them when green". Landed in opensoft/openWallet#1 at
      merge `2b8e223454044ba33cf371637ed536635d7f4fcf` (head `cefb918c`);
      check `validate` completed success.
      - `docs/openwallet-cutover-runbook.md`: phases 0–6, each with its
        rollback written before it. Every command was rehearsed in scratch
        clones: the carve layers of 80 (code), 38 (spec) and 10 (root) rows
        blob- and mode-identical with full history; the spec gate `3 passed`
        with the subject lines applied; a root commit passing `make
        validate`; and the three negatives OBSERVED — `pin-gitlink-mismatch`,
        an undeclared line or file refused, a mutated blob `MISMATCH`.
      - `.specify/` bootstrapped at the root: 47 files, the
        `setup-openspeckit` three-leg output, no active feature, `memory/`
        omitted as the root tracks none.
      - The leg gitlinks and `contracts/{code,spec}-pin.yaml` are untouched.
- [x] 3.5 `[openWallet]` Each repository's `README.md`, `AGENTS.md`, `CLAUDE.md`
      and `.github/CODEOWNERS`. The root's `AGENTS.md` points, beside
      `AGENTS-shape.md`, to the carve manifest's declared Q7 override.
      **DONE 2026-10-08** on Brett Heap's words in session, verbatim: "start
      group 3" and "land them when green". Landed across the three pull
      requests:
      - opensoft/openWallet#1 → `2b8e223454044ba33cf371637ed536635d7f4fcf`;
      - opensoft/openWallet-spec#1 →
        `cfd0a69cfbb78832195fd0acae4e7f4558855648`;
      - opensoft/openWallet-code#1 →
        `51b8e9c3b7beb9ecbed83529700948055e5872d7`.

      Each repository carries `README.md`, `AGENTS.md`, `CLAUDE.md` and
      `.github/CODEOWNERS`. The root's `AGENTS.md` points, beside
      `AGENTS-shape.md`, to the carve manifest's declared Q7 override at
      `docs/openwallet-carve-manifest.yaml` in openXwallet. Two declared
      exceptions were flagged on the root pull request:
      - two illustrative workspace-root example paths inside the vendored
        `.specify` overlay, which is content-addressed, so the fix is
        upstream;
      - the shape-pinned root `.gitignore` cannot take `/worktrees/`, so the
        workaround is `.git/info/exclude`.
- [x] 3.6 `[openWallet-spec]` The leg's own OpenSpec gate — RULED 2026-10-08,
      "Vendor the tarball (Recommended)" (recorded at 2026-10-08T17:01:43Z).
      - The leg commits the content-addressed `@fission-ai/openspec@1.12.0`
        tarball at
        `tools/openspec-cli-pin/fission-ai-openspec-1.12.0-c844543999f673cdd72445879b86a4abea4c07ef.tgz`,
        beside `contracts/openspec-cli-pin.yaml`,
        `scripts/install-pinned-openspec-cli.py`,
        `scripts/validate-openspec-cli-pin.py` and the drift-check document.
      - Its `.github/workflows/openspec-cli-pin-gate.yml` mirrors this
        repository's: vendored from openxFactory at a named commit, byte-identical
        except ONE declared divergence, the final `run:` line passing `--no-cache
        --tarball` at the committed path, so the gate installs OFFLINE.
      - The leg's `AGENTS.md` records the ruling as its own offline-gate rule —
        the same per-repository pattern as this repository's rule 4 and its
        2026-09-07 ruling.
      - Vendored fresh, NOT carved (`design.md` D7).
      - The gate is OBSERVED refusing a mutated tarball before it is trusted,
        and is green over the leg's `openspec/` at `--strict`.

      **DONE 2026-10-08** on Brett Heap's words in session, verbatim: "start
      group 3" and "land them when green". Landed in
      opensoft/openWallet-spec#1 at merge
      `cfd0a69cfbb78832195fd0acae4e7f4558855648` (head `9152cf11`); check
      `openspec-cli-pin-gate` completed success.
      - Committed: the tarball at the path above,
        `contracts/openspec-cli-pin.yaml`,
        `scripts/install-pinned-openspec-cli.py`,
        `scripts/validate-openspec-cli-pin.py` and
        `docs/openspec-cli-pin.md`.
      - `.github/workflows/openspec-cli-pin-gate.yml` vendored from
        openxFactory `44d8fbaf7d977668973dcd116040c9405416c2ea`,
        byte-identical except the one declared `run:` line (`--no-cache
        --tarball` at the committed path).
      - The leg's `AGENTS.md` rule 3 records the ruling as its own
        offline-gate rule.
      - `openspec/config.yaml` (`schema: spec-driven`) and nothing else under
        `openspec/`. MEASURED on 1.12.0: no `openspec/` reads
        `pin-no-target`, an empty directory `pin-report-unreadable`, and the
        config alone `Totals: 0 passed, 0 failed`. So green today is the
        empty total, not a content pass.
      - OBSERVED refusing a mutated tarball: `REFUSE pin-integrity-mismatch …
        INTEGRITY DRIFT`, exit 2.
      - `LICENSE` is not yet in the legs: it is a declared addition at 4.4.

## 4. The carve, the path-mapping proof, the first release `[openWallet]`

- [x] 4.1 The CONTROL: the eight recorded sha256s recomputed at the carve
      commit, 8/8, before anything is carved.
      - **DONE 2026-10-08**, before anything was carved. `bin/control.py` (phase
        0 of `docs/openwallet-cutover-runbook.md` in opensoft/openWallet), run
        against a fresh `--mirror --no-local` clone of opensoft/openXwallet at
        the carve commit `90111df262d6f54f7e82651d860adc12345f83f4`, printed
        `control: 8/8 owned digest(s) recomputed equal`. Re-run the same day
        with the same result.
- [x] 4.2 `[openWallet-code]` Carve the carve manifest's `openwallet_code` rows:
      `git filter-repo` from a fresh clone, one exact `--path` per row, no globs,
      no `--path-rename`, full history. Merge into the seeded leg with
      `--allow-unrelated-histories`. Blob and mode identity 100% at the carve
      layer; both `examples/` prefixes preserved.
      - **LANDED 2026-10-08** in opensoft/openWallet-code#2 at merge
        `72313daab1f229c049cb90998931564c1904dbbc` (a merge commit; parents
        `51b8e9c3` the scaffold `main` and commit B,
        `75b990dc7ea99823626c18816b37d971f46e341b`). Commit A, the pure carve
        layer, is `32c933551b92d83122a45847215d5ebe92ae6740`. Checks
        `wallet-validation` and `pytest-suite` completed success on head
        `75b990dc`.
- [x] 4.3 `[openWallet-spec]` The same for the `openwallet_spec` rows.
      - **LANDED 2026-10-08** in opensoft/openWallet-spec#2 at merge
        `15c15bbd451a803f0acdb24e5234836db829a2d3` (a merge commit; parents
        `cfd0a69c` the scaffold `main` and
        `5ea9539428eae850ba71e6f0ba8a38db061e809a` commit B). Commit A, the pure
        carve layer, is `c788cba28a81b0dc17da4cea5db1e57eceb3a193`.
- [x] 4.4 The declared-edit layer per leg, one auditable diff each.
      - Code leg: validator hunks (a)–(e); the corpus binding added (Q6); the
        `tests/nested_repo_prune/` split; `wallet-validation`'s envelope-verify
        step removed; `LICENSE` added.
      - Amended 2026-10-08, on Brett Heap's ruling "Amend the manifest: 8
        declared lines (Recommended)" (#25). The code leg's test split also
        takes `tests/multi_key_wallets/test_declared_key_sets.py` :108-111 and
        :117-118, which drop the `_grant` fixture's posture, and
        `tests/nested_repo_prune/test_prune_and_register_note.py` :47-48, the
        corpus note 21/42/11. Measured: 37 passed, 1 skipped.
      - Spec leg: the eleven subject lines; the three `openXwallet` occurrences in
        `add-composition-drift-cascade`'s deltas; `LICENSE` added.
      - **LANDED 2026-10-08**, both legs' commit B inside the merges at 4.2 and
        4.3, one auditable diff each (`git diff A B` per leg). Code leg
        measured 37 passed, 1 skipped; the spec leg's own vendored OpenSpec
        gate green. Codex did not review these pull requests: its connector
        was at its usage limit.
- [x] 4.5 `[openWallet-root]` Carve the `openwallet_root` rows and apply the
      manifest's declared field edits:
      - `carved_from:`;
      - each owned row's `path:` gaining `code/`;
      - `source_path:`;
      - the consumed hermes row removed.

      Do it in ONE root commit that also moves both gitlinks and
      `contracts/{code,spec}-pin.yaml` in lockstep. The shape's `validate` is
      green.
      - **LANDED 2026-10-08** in opensoft/openWallet#2 at merge
        `1c68717f1ae4ae132d6942f8c7f533baf292d0b6` (a merge commit). The
        lockstep commit is `b48bcb20b31dece4d582444cf01f617a799d297d`
        (parents: root `main` `2b8e2234`, the pure carve layer `3c44089c`):
        ten `openwallet_root` rows carved from the carve commit;
        `contracts/manifest.yaml` changed on its 67 declared lines only
        (`carved_from:`, eight `path:`/`source_path:` pairs now
        `code/contracts/…` and `openWallet-code/contracts/…`, the consumed
        hermes row removed); both gitlinks and `contracts/{spec,code}-pin.yaml`
        moved to spec `15c15bbd451a803f0acdb24e5234836db829a2d3` and code
        `72313daab1f229c049cb90998931564c1904dbbc`. Followed by `a51f05b6`
        (runbook helper 3 `--diff-algorithm=histogram`, helper 5
        `declared-lines-exact.py`) and `e4a7a6a9` (post-carve status in
        AGENTS.md and README). `validate` completed success on head
        `e4a7a6a9` with the real lockstep-pins step: `pins ok`. Helper 3 and
        helper 5: 0 refusals; three-way 8/8; control 8/8. Codex did not
        review: its connector was at its limit.
- [x] 4.6 `[openWallet-root]` The proof, `docs/byte-identity-<first tag>.md`,
      parts zero to five of `design.md` D7 — the DECLARED PATH MAPPING — each
      able to fail. A validator line in no declared hunk, or a path in no
      declared class, REFUSES it. Part three runs from the code leg's own root.
      - **RULED 2026-10-08**, Brett Heap, label verbatim
        "wallet-v1.6 (Recommended)" for the first root tag name, so the proof
        is `docs/byte-identity-wallet-v1.6.md`; and
        "Start now, neutrality half later (Recommended)": parts zero, one, two,
        four and five authored now by lane openXwallet-2; part three's
        composed-adapter half is filled when group 5's composed validator
        exists (lane openXwallet-3). Landed; see below.
      - **PENDING**, part three's second half: the neutrality gate over the
        composed adapter. It WAS measured, at the head `a02c6c74` of lane
        openXwallet-3's branch `rebuild/adapter-group-5` of opensoft/openXwallet
        (see the LANDED bullet below); the pinned root cited below, `1c68717f`,
        was the development pin, and the final root is `52d75736`. The shape,
        as that lane gave it: from an openXwallet checkout at that branch,
        with openWallet pinned at the root merge
        `1c68717f1ae4ae132d6942f8c7f533baf292d0b6` (its `code` gitlink
        `72313daab1f229c049cb90998931564c1904dbbc`), run
        `git submodule update --init openWallet` and
        `git -C openWallet submodule update --init code`; the composed
        validator then runs as `python3 scripts/validate-openxwallet.py <tree>
        [--strict]` (needs pyyaml, jsonschema and rfc3339-validator). The gate:
        the carve-commit validator (`scripts/validate-openxwallet.py` at
        openXwallet `90111df`) and the composed adapter print byte-identical
        output and the same exit code, plain and `--strict`, over the same
        tree, for each of this tree, the openxFactory governance export, and
        every test-suite fixture tree.
      - Superseded 2026-10-09: the final root is opensoft/openWallet#7's merge
        `b0af7c2c`, per the rulings recorded at 4.9.
      - **LANDED 2026-10-09** in opensoft/openWallet#3 at merge
        `52d75736156550b48992e39f7a69fb680c611287` (a merge commit; head
        `6b25be50`; commits `624e196` the proof, `b86c6a5` root docs status,
        `c644bf7` the adapter-half fill, `6b25be5` the runbook 3c snippet's
        exit code). `docs/byte-identity-wallet-v1.6.md`: parts zero, one (a),
        one (b), two (a), two (b), three (both halves), four and five
        RUN-GREEN; D5's neutrality gate EMPTY plain and `--strict` over
        openXwallet's tree at `a02c6c74`, the openxFactory `governance/`
        export at `c8dde131`, and all 110 suite-built trees; consumer depth 2
        88/88; consumer depth 3 PENDING group 6; the adapter-half head is
        re-confirmed when group 5 lands; the from-text re-run finished clean
        (`runner exit=0`) and is being closed by a follow-up doc commit.
        Finding 4 (the code leg's checkout scanned in place differs by one
        `repo scan` summary line because `repo_scan` skips the validator's own
        packaged registry by resolved path) ruled "Qualify D5's sentence; gate
        stays GREEN (Recommended)" (design D5 amendment in flight). Landed on
        the word "land the proof PR when green" and the ruling "Land it now
        (Recommended)". `validate` completed success with the lockstep-pins
        step. Codex did not review.
- [x] 4.7 **[OPERATOR]** Three rulesets, each EVALUATE → one trivial pull request
      so its checks report → ACTIVE. Each is an org-admin act in `opensoft`.
      - root: `validate`;
      - spec leg: its OpenSpec gate;
      - code leg: `wallet-validation` and `pytest-suite`.
      - **DONE 2026-10-09** on Brett Heap's word "run both steps and tick 4.7"
        (an org-admin act, performed by lane openXwallet-2 under the operator's
        account). Three repository rulesets, each created in EVALUATE and
        promoted to ACTIVE once its checks had reported on real pull requests,
        read back from `repos/opensoft/<repo>/rules/branches/main`:
        opensoft/openWallet ruleset `24763933` ("openWallet root gate (require
        validate)"), main requires `validate`; opensoft/openWallet-spec ruleset
        `24763934` ("openWallet-spec gate (require openspec-cli-pin)"), main
        requires `openspec-cli-pin`; opensoft/openWallet-code ruleset `24763935`
        ("openWallet-code gate (require wallet-validation + pytest-suite)"),
        main requires `wallet-validation` and `pytest-suite`. Each targets
        `~DEFAULT_BRANCH`, strict mode off, bypass OrganizationAdmin always (the
        shape of openXwallet's own ruleset `21607344`). Rollback: enforcement
        back to `evaluate`, or delete; no commit touched. No trivial pull
        request was needed: every context had already reported (root `validate`
        on every PR since the scaffold; `openspec-cli-pin` on
        openWallet-spec#2–#4; `wallet-validation` and `pytest-suite` on
        openWallet-code#2).
- [x] 4.8 `[openWallet-spec]` openWallet's birth change in the leg's own
      OpenSpec instance, after 4.3 lands. It MODIFIES *Agent authority is grant
      scope, not a parallel vocabulary* to the text drafted in `design.md` D8.
      - **LANDED 2026-10-09** by lane openXwallet-1 in
        opensoft/openWallet-spec#3 at merge
        `1506bbdb4194a779bef63d8c4e5eecc7eac0bd68` (a merge commit; head
        `5f95efdd38bb177c1a8ccd94da1a1c9ef45faf3b`, two commits on the carve
        merge `15c15bb`), on Brett Heap's word in session, verbatim: "land it
        when the fixes are in and the review is clean". Claimed on #25
        2026-10-08
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6069656258).
        Gated on the leg's named run `openspec-cli-pin` completed success for
        the exact head; an independent Opus review of `5f95efdd` read CLEAN
        after its five findings on `1cc53ce` were applied; Codex reviewed
        `1cc53ce` (no major issues) and hit its usage limit on the second
        pass. Administrator merge, author cannot self-approve.
      - The change is `openspec/changes/bind-approval-posture-vocabulary/` in
        that leg (`.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`,
        one delta), `Status: proposed`: its ratification and archive in the
        leg are the operator's acts (its tasks 1.2 and 3.1). The delta is ONE
        `## MODIFIED Requirements` block on `openxwallet-agent-profile`, the
        requirement titled character-for-character, its statement D8's two
        sentences verbatim (compared by script), three scenarios: *authority
        is carried by a grant* unchanged; *the approval vocabulary is reused,
        not duplicated* re-bulleted onto the declared binding; *no binding is
        declared, so a posture is refused rather than admitted because nothing
        forbade it* new.
      - Measured on the pinned 1.12.0: the leg's gate
        `Totals: 4 passed, 0 failed`, `OK openspec-cli-pin`; dry archive in a
        scratch copy `Totals: + 0, ~ 1, - 0, → 0` on
        `openxwallet-agent-profile` only, archiving in either order with
        `add-composition-drift-cascade` to byte-identical specs.
      - **RULED** — Brett Heap, 2026-10-09, in session, by multiple choice,
        label verbatim "Keep the promoted title, MODIFIED block
        (Recommended)": scenario two keeps the promoted title "the approval
        vocabulary is reused, not duplicated" (D8 listed it as "the bound
        vocabulary is reused, not duplicated") because 1.12.0 refuses a
        MODIFIED block that drops a scenario name the promoted spec still has;
        the one route to D8's name (RENAMED to a placeholder, REMOVED, ADDED
        under the original title, in one delta; archive `+ 1, ~ 0, - 1, → 1`)
        breaks D8's form "MODIFIES exactly one requirement" and was not taken.
        First ruled the same day as "Keep the promoted title (Recommended)" on
        the change's incomplete premise, re-presented with the measured route
        and re-ruled. Recorded on #25 and in the change's `.openspec.yaml`
        `rulings`. D8's text is not amended.
      - Observed in the code leg and not taken on (recorded in the change's
        `design.md`; carried on the code-leg follow-up list by lane
        openXwallet-2): rule (g)'s refusal message at `72313da` still names
        "the neutral job envelope" though D4 says it stops; behaviour correct
        (no binding → every posture refused, `legal terms: []`), wording
        stale.
- [x] 4.9 **[OPERATOR]** `[openWallet-root]` First release — five coordinated
      values — on the ROOT:
      - the annotated `wallet-v*` tag on the root commit that pins both legs;
      - `contracts/manifest.yaml`, `contracts/CHANGELOG.md` and
        `contracts/releases/` at the root;
      - no leg tag;
      - the tag only after 4.6 is green;
      - the number allocated here, not before.
      - The tag NAME `wallet-v1.6` was allocated 2026-10-08 on the ruling at
        4.6. The tag itself is cut only after 4.6 is green and 4.7's rulesets
        are ACTIVE.
      - **RULED** 2026-10-09, labels verbatim "The root commit carrying the
        completed proof (Recommended)" and "Wait for the full proof
        (Recommended)": `wallet-v1.6` goes on root `main` `52d75736` (spec
        `1924500`, code `72313daa`) once 4.7's rulesets are ACTIVE. The
        root's spec pin was moved by two lockstep pull requests, on the
        rulings "Re-pin spec to 1506bbdb before the tag (Recommended)"
        (opensoft/openWallet#4 → `5a444cf2`) and "Re-pin to the archive merge
        before the tag (Recommended)" (opensoft/openWallet#5 → `bead4bd8`),
        so the first release carries 4.8 in its archived form.
      - **RULED again** 2026-10-09, in two later acts that moved the tag's
        commit:
        - Brett Heap's word, verbatim, 2026-10-09T02:19:53Z: "tag goes on the
          #6 merge, send it to lane 3". It names the merge commit of
          opensoft/openWallet#6, root `main`
          `b4580d1655a9f0df9bb94f35299163d7470609f4`, in place of `52d75736`.
          Recorded at
          https://github.com/opensoft/openXwallet/issues/25#issuecomment-6072926959.
        - After 4.7's rulesets were ACTIVE, his word "cut the wallet-v1.6 tag
          on b4580d16" (2026-10-09T02:37:39Z) met the root's rule that a
          release is five coordinated values in one root commit (AGENTS.md
          rule 5 at the root, and the runbook's Phase 6), while `b4580d16`
          still declared `contract_bundle_version: wallet-v1.5` and carried
          no v1.6 record or CHANGELOG entry. RULED by multiple choice, label
          verbatim: "Release commit on b4580d16, tag its merge (Recommended)"
          (2026-10-09T02:40Z;
          https://github.com/opensoft/openXwallet/issues/25#issuecomment-6073154682).
          The release commit is opensoft/openWallet#7, one commit
          `88345cc8db2860edfde018739f4c71d8a18d75bd` on `b4580d16`:
          `contract_bundle_version: wallet-v1.6`,
          `contracts/releases/wallet-v1.6.digests.yaml` cut by recomputation
          (8 of 8), and the CHANGELOG entry; no gitlink or pin moves. The tag
          goes on that pull request's merge commit; the tick follows when the
          merge and the tag exist.
      - **DONE 2026-10-09** on Brett Heap's word in session, by multiple
        choice, label verbatim "Land 7 and cut the tag (Recommended)"
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6086448281).
        - opensoft/openWallet#7 landed at merge
          `b0af7c2ce53d63786a08a20aa3602a6f90345606` on 2026-10-09T17:43:03Z,
          a merge commit with parents `b4580d16` and the release commit
          `88345cc8`. It was gated on `validate` completed success for head
          `88345cc8`, with the lockstep-pins step (`pins ok`).
        - The annotated tag `wallet-v1.6`, tag object
          `3acfa611b69503e809043faff5f3622cc008a3eb`, message "openWallet
          wallet-v1.6: the first release on the root, pinning both legs",
          resolves to that merge, `b0af7c2c`. At the tag the root's gitlinks
          read spec `1924500354f472a6298c02db44a3ae2b21b8908e` and code
          `72313daab1f229c049cb90998931564c1904dbbc`. Neither leg carries a
          tag.
        - The five coordinated values, in or pinned by that one root commit:
          - per-file `contract_schema_version`, inside each artifact's bytes
            in the code leg the root pins, unchanged from wallet-v1.5 (the
            release record lists 2 for `openxwallet-record` and 1 for the
            other seven);
          - `contract_bundle_version: wallet-v1.6` in
            `contracts/manifest.yaml`;
          - the annotated `wallet-v1.6` tag, on the merge;
          - the release commit with per-file digests,
            `contracts/releases/wallet-v1.6.digests.yaml` (8 of 8, cut by
            recomputation);
          - the `contracts/CHANGELOG.md` entry.
        - The tag came after 4.6 was green and after 4.7's rulesets were
          ACTIVE, both ticked above.

## 5. The adapter rebuild — this repository, one pull request

- [ ] 5.1 The gitlink `openWallet/`, mounting the openWallet ROOT, and
      `contracts/openwallet-pin.yaml` in the same commit. The pin holds:
      - the root `commit:`;
      - `legs.code`, as a lockstep mirror;
      - `files:` at `code/contracts/…`;
      - `pinned_by_commit_only:` at `code/…`.

      `scripts/verify-openwallet-pin.py` fails closed. It is OBSERVED refusing an
      uninitialized `openWallet/`, an uninitialized `openWallet/code/`, a
      gitlink ≠ pin, a checkout ≠ pin, a leg-lockstep mismatch (the root's `code`
      gitlink vs its `contracts/code-pin.yaml` vs `legs.code.commit`, read from
      git objects) and a mutated digest.
      - Group 5 is opensoft/openXwallet#40, authored by lane openXwallet-3
        (claimed on #25, 2026-10-08), on branch `rebuild/adapter-group-5-r2`.
        The review-fixed history took a sibling name because the ruleset
        forbids force-push (organisation ruleset `8981805` carries
        `non_fast_forward` on every branch); `rebuild/adapter-group-5`, at
        `a02c6c7487171c110490b234643a7e586ed47153`, the head the proof
        measured, stays on origin as that record. The FINAL root to pin is the
        merge commit of opensoft/openWallet#7,
        `b0af7c2ce53d63786a08a20aa3602a6f90345606`, the wallet-v1.6 release,
        per the ruling recorded at 4.9; lane openXwallet-3 re-pins to it in
        one commit, with `contract_bundle_tag: wallet-v1.6`, before #40 lands.
- [ ] 5.2 `scripts/validate-openxwallet.py` recomposed per `design.md` D5:
      - the pinned core loaded in process from
        `openWallet/code/scripts/validate-openxwallet.py`;
      - rule (t) and the register reader registered at their present positions;
      - the hermes binding unconditional.
- [ ] 5.3 `scripts/wallet-yaml-syntax-gate.py` kept as an entrypoint, one
      implementation.
- [ ] 5.4 THE NEUTRALITY GATE: the carve-commit validator and the composed
      adapter over this tree, an export of openxFactory's live `governance/`
      tree, and every test-suite fixture tree — `diff` EMPTY, plain and
      `--strict`, the same exit code. This tree's one new prune note is declared.
- [ ] 5.5 Shed exactly the carve manifest's `retained_here: shed` rows —
      `add-composition-drift-cascade` among them. Leave the `kept` rows (the three
      adapter negatives at their path, every archive record unedited) and the
      `retired_by_archive` rows (the two promoted specs, which this change's
      archive retires).
- [ ] 5.6 Manifest (nothing of openWallet's registered as owned), CHANGELOG,
      README (the adapter role, PUBLIC, the Speckit list, the capability count),
      AGENTS.md (the one-paragraph identity and rule 3), CODEOWNERS.
      `wallet-validation` runs in this order: `git submodule update --init
      openWallet`, then `git -C openWallet submodule update --init code`, then
      the two verifiers, then the gates.
- [ ] 5.7 The full gate bar (AGENTS.md rule 5) and the pinned CLI gate, green.
- [ ] 5.8 **[OPERATOR]** The adapter's first release in Q4's series, five
      values, tagged at the merge commit.

## 6. openxFactory — one pull request `[openxFactory]`

**AMENDED 2026-10-09 by measurement**, on Brett Heap's rulings (operator
authority), in session, by multiple choice, labels verbatim: "Amend 6.x and
7.x by measurement (Recommended)" and "Name it a successor (Recommended)"
(https://github.com/opensoft/openXwallet/issues/25#issuecomment-6086531327).
Tasks 6.1–6.6 name too little. Each keeps its text, save the one literal in
6.5 that is now false, and a dated note under it gives what was measured. The
measure is a scratch dry run of this group against openxFactory `main`
`93d13d6c8e14008c0b66adea65756d106fef6227`, with the openXwallet gitlink at
`df7f82aa0f10e3c134602049c6b1b8b7e0f0c24f` (the head of
opensoft/openXwallet#40 when measured), the openWallet root at `1c68717f` and
its code leg at `72313daa`; nothing was pushed.

**Citations unchanged.** At `93d13d6c`: the workflow's `:99` (the step is
`:98-99`); `SCOPED_INIT_RUN` at `:47`; the verifier's remediation trailer at
`:80-89` (`REMEDIATION` itself is `:85-89`); `OPENXWALLET_REGISTRY_PATH` at
`:348-350`; and the refusal test's `:199` (the assertion is `:199-200`).

**Surfaces the tasks did not name.** Eight in all, each measured at
`93d13d6c`: the three workflows noted under 6.2, and the five below.

**The signed-chain reader.** `scripts/validate-signed-execution-chain.py`
`PINNED_WALLET_DIR` (`:158`) is re-pathed, because the old path,
`openXwallet/contracts/openxwallet`, loses its schemas at the adapter head (at
`df7f82aa` it holds only the three `grant-review-*` negatives); with it, its
test `tests/signed_execution_chain/test_chain_reader.py` (`:523`).

**The doc-health pin shapes.** `scripts/doc_health/pin_shapes.py`: its
machine-checked citations into `scripts/verify-openxwallet-pin.py` move
(`194`, `219`, `227`, `392` with `396`, and `443` at `93d13d6c`; re-measured
at authoring). With only the verifier moved, two tests fail, both in
`tests/doc-health/test_pin_shape_adapter.py`:
`test_guard_leg_every_cited_line_still_reads_the_member_it_was_measured_from[openxwallet]`
and `test_guard_leg_the_two_citation_route_entries_still_hold_their_refusal`.
Prose cites into the verifier sit beside them in comments and fail nothing
(`test_pin_shape_adapter.py:202` and `:501`;
`test_modified_block_currency_self_gate.py:1257` and `:1266`); they move with
them.

**A blocker, handed off.** The adapter at `df7f82aa` did not re-export
`decode_public_key_multibase` and `fingerprint_of_public_key`, which
openxFactory's factory-identity and clearing-dispatch gates import
(`scripts/validate-factory-identity.py:217`,
`scripts/validate-clearing-dispatch.py:352`), and lane openXwallet-3 confirmed
it and folds the fix into #40 before it lands. The fix landed on #40's branch
as commit `6ca9acd0097bc255c0c65e1b8c3ffe170b643011`, and #40's final head is
`36c365dab5ca7c9db036cb413963d7cabb804375`, which re-pins the root to
`b0af7c2c`. Lane openXwallet-1's independent review of the fix is CLEAR
(https://github.com/opensoft/openXwallet/pull/40#issuecomment-6087335229).

**A named successor (ruling 2).** openxFactory's promoted spec
`openspec/specs/document-lifecycle/spec.md:316-344` cites
`scripts/verify-openxwallet-pin.py:194,219,227,392-397,443-448` and
`contracts/openxwallet-pin.yaml:70,80-95,104-110`. This group makes those
cites stale, and its pull request leaves that spec alone: the stale cites are
a named successor for openxFactory's own OpenSpec flow (8.3).

- [ ] 6.1 `contracts/openxwallet-pin.yaml`:
      - `files:` re-pathed to `openWallet/code/contracts/…`;
      - `pinned_by_commit_only:` keeps `scripts/validate-openxwallet.py` and
        `scripts/wallet-yaml-syntax-gate.py`, re-paths the corpora and READMEs to
        `openWallet/code/contracts/…`, and adds
        `openWallet/code/scripts/validate-openxwallet.py` and
        `openWallet/code/scripts/wallet-yaml-syntax-gate.py`;
      - `commit:` and `contract_bundle_tag:` bumped;
      - the eight digests re-verified by recomputation (values unchanged);
      - no openWallet commit recorded (ONE chain).

      **AMENDED 2026-10-09 by measurement**, at `93d13d6c`:
      - the pin's `digest_source` re-points from `contracts/manifest.yaml` to
        the openWallet root manifest, `openWallet/contracts/manifest.yaml`
        under the openXwallet checkout;
      - the path-only members go from 6 to 8, the two added being
        `openWallet/code/scripts/…`;
      - the eight digests, recomputed over
        `openXwallet/openWallet/code/contracts/…` at the code leg `72313daa`,
        equal the pin's and `wallet-v1.5`'s, 8 of 8;
      - `commit:` and `contract_bundle_tag:` take the adapter's first release,
        RULED `xwallet-v1.0` (5.8), label verbatim "Adapter series
        `xwallet-v*`, first `xwallet-v1.0` (Recommended)"
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6072312849).
- [ ] 6.2 `.github/workflows/openxwallet-consumer-gate.yml` (`:99`): the scoped
      init extended to three named levels — `openXwallet`, then
      `openXwallet/openWallet`, then its `code` leg — never `--recursive`. In the
      same commit: `tests/openxwallet_consumer_gate/test_gate_invocation.py`
      (its `SCOPED_INIT_RUN`, `:47`), and `scripts/verify-openxwallet-pin.py`'s
      remediation trailer (`:80-89`, FR-004).
      - **AMENDED 2026-10-09 by measurement**: two more workflows verify the
        pin after a one-level init, and each gains the two nested init steps,
        `clearing-dispatch-gate.yml` (init `:95`, verify `:106`) and
        `signed-execution-chain-gate.yml` (init `:106`, verify `:118`).
        `pytest-suite.yml` (its init at `:430`) gains the two nested init
        lines, `git -C openXwallet submodule update --init openWallet` and
        `git -C openXwallet/openWallet submodule update --init code`; without
        them 95 tests fail, 7 in `tests/openxwallet_pin`, 87 in
        `tests/trust-anchor` and 1 in `tests/signed_execution_chain`.
- [ ] 6.3 `scripts/verify-openxwallet-pin.py`: nested-checkout parity through BOTH
      levels, observed refusing at each.
      - **AMENDED 2026-10-09 by measurement**, as the dry run did it, recorded
        as the approach measured and not as a new requirement: the nested
        refusals reuse the verifier's six ratified refusal codes
        (`REFUSAL_CODES`, `:101-108`) and add none, and the chain is a
        verifier constant, `NESTED_CHAIN = ("openWallet", "code")`, not a pin
        field. `main`'s verifier passed both stale nested checkouts, which is
        the gap this task closes: over the openWallet root at `b48bcb20` and
        its code leg at `75b990dc`, neither the commit the level above
        records, it exited 0 with `8 digest(s) recomputed`, where the dry
        run's verifier refused `pin-checkout-mismatch` at each level. The test
        fixture, `tests/openxwallet_pin/test_verify_pin.py`'s scratch wallet,
        becomes a chain of three repositories, and a new test covers an
        uninitialized code leg.
- [ ] 6.4 `scripts/validate-trust-anchor.py` `OPENXWALLET_REGISTRY_PATH`
      (`:348-350`) becomes `ROOT / "openXwallet" / "openWallet" / "code" /
      "contracts" / "openxwallet" / "openxwallet-custody.registry.yaml"`, with
      `tests/trust-anchor/test_openxwallet_pin_refusal.py` (`:199`) in the same
      commit.
      - **AMENDED 2026-10-09 by measurement**: the held-equal copy of the
        remediation trailer, `OPENXWALLET_REMEDIATION_FALLBACK`
        (`scripts/validate-trust-anchor.py:2605`, held byte-identical to the
        verifier's literal by
        `tests/trust-anchor/test_openxwallet_pin_refusal.py` `:302`), moves
        with that literal.
- [ ] 6.5 The gate's LITERAL assertions do not move and are green — `9 of 9`,
      the five-key wallet note, the six-key wallet note, `repo scan:`.
      - **AMENDED 2026-10-09 by measurement**: this task first read "The
        gate's LITERAL assertions do not move and are green — `8 of 8`, the
        five-key wallet note, `repo scan:`." The literal `8 of 8` no longer
        exists as an assertion. Since 2026-09-12 it reads `9 of 9` (workflow
        `:181`, test `:285`), and `8 of 8` survives only in comments (`:156`,
        `:175`). The task also missed a second counted wallet note,
        `wal-agent-grc-0001` with 6 keys (workflow `:218`, test `:356-357`).
        As measured at `93d13d6c`, in
        `.github/workflows/openxwallet-consumer-gate.yml` and
        `tests/openxwallet_consumer_gate/test_gate_invocation.py`, the
        literals are `9 of 9`, the five-key note (`wal-agent-mrc-0001`,
        workflow `:204`), the six-key note, and `repo scan:` (workflow
        `:143`). None of them moves in this group.
- [ ] 6.6 `doc-health-reusable.yml`'s nested init — only if a leg reads wallet
      content; checked, not assumed.
      - **AMENDED 2026-10-09 by measurement**, checked: it applies to the
        prepare job only. `doc-health-reusable.yml` inits at `:464` (prepare),
        and the parity step (`:510-560`) runs `verify()` first. With main's
        init block it refused `pin-submodule-uninitialized` (rc=2), and with
        the nested init it passed. The finalize job (`:1598`) runs no verifier
        and reads no wallet bytes, and is unchanged. `doc-health-py314.yml`
        (init at `:81`) was checked and is not needed: `tests/doc-health`
        passed 2157 of 2157 with the chain absent and present.

## 7. Consumer notices and verifications

- [ ] 7.1 `[LedgerxWallet]` Nothing on day one. At its next pin bump, the
      nested init of `openXwallet/openWallet` and its `code` leg. One direct
      upstream per Q2.
      - **AMENDED 2026-10-09 by measurement**, on Brett Heap's ruling "Amend
        6.x and 7.x by measurement (Recommended)"
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6086531327):
        LedgerxWallet (`opensoft/LedgerxWallet`, `main` `0a0141ca`)
        initializes with `git submodule update --init --recursive openXwallet`
        (`.github/workflows/pin-validation.yml:82`; the same command is built
        at `tests/validate_pin.py:62`). At its next pin bump
        `openXwallet/openWallet` and its legs therefore initialize with no
        textual change, so "the nested init" above is already satisfied.
        Notice: its `tests/validate_pin.py` check 4 inspects only the
        top-level `openXwallet` (`:347`, `:384`, `:400`). Its cleanliness read
        at `:400` shows a nested checkout that is edited or off its recorded
        commit as ` M openWallet`, which it refuses as dirty; an UNINITIALIZED
        `openWallet` or `openWallet/code` shows nothing, and would surface
        only through the adapter's own refusal.
- [ ] 7.2 `[LedgerxFactory]` Its estate run initializes two levels deeper, to
      `LedgerxWallet/openXwallet/openWallet/code`. Its `--strict` run and its
      `repo scan:` parse stay green.
      - **AMENDED 2026-10-09 by measurement**, on Brett Heap's ruling "Amend
        6.x and 7.x by measurement (Recommended)"
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6086531327):
        this task first read "Its estate run initializes two levels deeper, to
        `openxFactory/openXwallet/openWallet/code`." LedgerxFactory
        (`ledgerXfactory/LedgerxFactory`, `main` `ba86f758`) does not
        initialize openxFactory's submodules. Its gitlinks are `LedgerxAvatar`
        and `LedgerxWallet`, and its estate run initializes `LedgerxWallet`
        with `--init --recursive` (`.github/workflows/validate.yml:176-178`),
        so the real chain is `LedgerxWallet/openXwallet/openWallet/code`,
        reached with no textual change.
      - Measured with the adapter at `df7f82aa` nested there (root `1c68717f`,
        code leg `72313daa`), its `--strict` run (`validate.yml:188-191`)
        exits 0, and its `repo scan:` parse
        (`tests/validate_wallet_estate.py:906`, a floor of at least 5 at
        `:909`) reads `repo scan: 5 …`, identical to today's pinned
        `wallet-v1.1`. That leaves zero headroom on the floor.
      - With the code leg uninitialized the run exits 2 and prints a `REFUSE
        pin-leg-uninitialized` refusal on stderr and nothing on stdout
        (`REFUSE core-unloadable` where the leg's checkout exists but the core
        file is not in it), which LedgerxFactory reports as `no output`
        (`tests/validate_wallet_estate.py:905`).
      - Its `stack.yaml` `openxwallet.contract_ref` must equal LedgerxWallet's
        gitlink at bump time (`tests/validate_wallet_estate.py:884-891`).
- [ ] 7.3 `[codexFactory]` Confirm `openxfactory_floor.py` still floors the
      `openXwallet` gitlink and that Q2 adds no second wallet gitlink; record it.
      - **PRE-CHECKED 2026-10-09**, read-only, and not ticked: it is
        re-confirmed when group 6 lands. codexFactory
        (`codeXfactory/codexFactory` at `2bc5015d`)
        `scripts/merge_master/openxfactory_floor.py:285-292`
        `PROTECTED_ROOT_FILES` includes `"openXwallet"` (`:289`), and
        `floor/openxfactory-review-authority-floor.yaml:114-121`
        `never_clearable_paths` lists `contracts/openxwallet-pin.yaml`
        (`:117`) and `openXwallet` (`:121`). openxFactory at `93d13d6c`
        carries the gitlinks `installs/omnigent-install`, `openDox`,
        `openXdox` and `openXwallet`, with no `openWallet`, and nothing in
        codexFactory names `openWallet`, so Q2 adds no second wallet gitlink.
        Group 6.1 touches two never-clearable paths, the pin file and the
        `openXwallet` gitlink, so its pull request is the operator's to clear.
- [ ] 7.4 `[xFactory]` No root `openWallet` gitlink under Q2; if one is ever
      added, root-gitlink parity against openXwallet's pin.
      - **PRE-CHECKED 2026-10-09**, read-only, and not ticked: it is
        re-confirmed when group 6 lands. xFactory (`opensoft/xFactory`, `main`
        `39b66b6c`) has no `openWallet` gitlink. Its root `openXwallet`
        gitlink (`f3eb929b`) is held equal to openxFactory's nested
        `openXwallet` by `tests/test_openxwallet_gitlink_parity.py` (D11,
        assertion `:103`). When xFactory's `openxFactory` pointer moves to
        group 6's merge, its root `openXwallet` must move to the same commit
        in the same sync commit.

## 8. Travels with openWallet — named, not this change's gate

- [x] 8.1 `[openWallet-spec]` Rebase `add-composition-drift-cascade`'s MODIFIED
      *Revocation propagates through the chain* onto the text multi-key's
      archive promoted, before that change archives.
      **Pre-performed here 2026-10-08**, in openXwallet PR #27 under Brett
      Heap's ruling on it ("Rebase drift-cascade now, then land
      (Recommended)"): the block carries the promoted sentence and scenario
      verbatim, so the change travels to openWallet already rebased and only
      the subject rewrite (4.4) remains for it there.
      **DONE 2026-10-09**, verified in opensoft/openWallet-spec `main`
      `1924500354f472a6298c02db44a3ae2b21b8908e`, the change still active
      there (not archived):
      - `openspec/changes/add-composition-drift-cascade/` is present, with
        `proposal.md`, `design.md`, `tasks.md` and deltas under `specs/` for
        `openxwallet` and `openxwallet-agent-profile`.
      - Its `specs/openxwallet/spec.md` MODIFIED block *Revocation propagates
        through the chain* opens with the promoted requirement paragraph
        verbatim, including "Retiring one DECLARED KEY of a wallet SHALL stop
        that key presenting the wallet's authority …", and carries the
        scenario "retiring one key does not revoke the wallet" with its three
        bullets, byte for byte, compared by script against the promoted
        requirement at `openspec/specs/openxwallet/spec.md`; all three of the
        promoted scenarios are in the block.
      - 4.4's subject rewrite is applied there: a recursive `diff` of the
        change directory at the carve commit `90111df` against the leg's
        shows exactly three differing lines, each `openXwallet` read as
        `openWallet` — `specs/openxwallet/spec.md` :7 and :36 and
        `specs/openxwallet-agent-profile/spec.md` :7 — and the deltas hold no
        `openXwallet`.
      - The leg's own pinned gate on that tree reads `Totals: 3 passed, 0
        failed`, `OK openspec-cli-pin`.
- [ ] 8.2 `[openWallet]` After the carve, never in it: the root manifest's stale
      corpus counts, and the code leg validator's `:337` pointer.
      - **RULED 2026-10-09**, Brett Heap, in session, by multiple choice,
        label verbatim "Root now, code leg batched (Recommended)"
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6086531327).
        The task's two parts no longer travel together. It is not ticked: its
        code-leg part waits for the next code-leg release.
      - The root part is DONE: opensoft/openWallet#8, merged 2026-10-09 at
        `2d7968fec334a21f311a2f4cc7e18eae108b9f0a` (a merge commit; parents
        `b0af7c2c` and `cbab447a`), one small root pull request that moved no
        pin (the `code` and `spec` gitlinks are `72313daa` and `1924500`
        before and after it). It fixed the manifest comment's corpus counts,
        "16 valid + 33 intended-invalid" (`contracts/manifest.yaml:71-72` at
        root `b0af7c2`), to the 21 positives and 42 negatives the code leg
        holds at `72313daa` (its validator reads `corpus: 21 positive
        example(s), 42 negative confirmation(s) across 11/11 requirements`);
        "nine members" (`:83`), to eight; and the bare `contracts/…` /
        `scripts/…` paths in the same comments, to `code/…` and `spec/…`. The
        comment on the consumed member now says none is consumed. It also
        fixed root `README.md` and `AGENTS.md` prose the release had made
        stale.
      - The code-leg part is batched into the next code-leg release after
        group 6, so downstream re-pins once. It is two things. First, the
        validator's rfc3339 pointer (D3's `:337`/`:338` at the carve commit;
        `scripts/validate-openxwallet.py:309-310` at `72313daa`), which names
        `requirements/hermes-runtime-contracts.in`, a path the code leg does
        not have; it is an error message printed to stderr, with exit 2, at
        import when `rfc3339-validator` is missing. Second, the
        `.gitattributes` rule `* text=auto eol=lf` that the root carries and
        the code leg lacks, found by lane openXwallet-1.
- [ ] 8.3 Named successors: the neutral-prefix MAJOR (deferred by ruling), rule
      (h)'s neutral re-expression, and the grant schema's envelope prose at the
      next digest-moving release.
      - **RULED 2026-10-09**, Brett Heap, in session, by multiple choice,
        label verbatim "Name it a successor (Recommended)"
        (https://github.com/opensoft/openXwallet/issues/25#issuecomment-6086531327),
        adds to the named successors: the stale cites in openxFactory's
        promoted `document-lifecycle` spec
        (`openspec/specs/document-lifecycle/spec.md:316-344`, into
        `scripts/verify-openxwallet-pin.py` and
        `contracts/openxwallet-pin.yaml`) that group 6 makes stale and its
        pull request leaves, for openxFactory's own OpenSpec flow.

## 9. Archive gate

- [ ] 9.1 `code_surface` is not `none`, so per `release-realization` this change
      archives only on MERGED, GREEN realization evidence: §2–§6 merged and
      green, the neutrality gate empty, §7 recorded.
- [ ] 9.2 `add-composition-drift-cascade` has LEFT this repository first — a
      MODIFIED delta against a retired spec aborts on 1.12.0 (measured,
      `design.md` D0) — and `retire_capabilities: true` is still declared.
- [ ] 9.3 The full gate bar re-run at archive.
