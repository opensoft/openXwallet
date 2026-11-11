# Candidate data model

Internal adapter projection; no published neutral schema.

| Entity | Trusted owner and checks |
| --- | --- |
| Policy | Operator: revision/lifetime, exact workload claims, wallet/key/custody/revision/public-key digest, grant, composition and supervisor key |
| Wallet/grants | Existing record kinds; active agent/audience and bounded ancestor chain |
| Issuer key snapshot | Operator: issuer, freshness, unique RS256 kid; no token-selected resolution |
| Request | Trusted act, object, run/attempt; digest binds policy, wallet/key/grant/composition |
| Challenge | Trusted owning loader: active issuer/ID/subject, request and canonical digest |
| Observation | Independent supervisor: canonical signed token/challenge/request/composition/policy/run binding, max 60 seconds |
| Reservation | Unique issuer-token and issuer-challenge hashes committed before custody |

Grant traversal is leaf-to-root, bounded to 16, cycle/missing-parent refusing.
All nodes address this wallet/holder, use `act`, explicit acts/objects and
conservative approval posture. Child scope/expiry may only narrow; issue time
cannot precede its parent. Expired/revoked ancestors refuse at exercise.

Reservation: absent -> permanently reserved -> sign attempted. Failure does not
free it. No domain-effect idempotency, signing retry, issuance or ledger pruning.

Unsupported grant constraints (including distinct-holder references) and unknown authority fields refuse. The selected wallet public-key material must match the current registry; the observer launches the selected reference worker and hashes its source/configuration independently. No hostile OS-isolation claim is made.
