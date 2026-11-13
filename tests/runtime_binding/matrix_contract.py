"""Reviewed offline collection contract; a test harness, not a neutral profile.

Counts include every parametrized node. Intentional corpus changes update this
table and its substantive anchors together. R01 here covers existing scope/error
privacy; full redacted receipt construction is T011. P01 is never an offline claim.
"""
ROOTS = ("tests/runtime_binding", "tests/factory_binding/test_binding.py",
         "tests/factory_binding/test_owner_integration.py")

MODULE_COUNTS = {
    "tests/runtime_binding/test_conformance.py": 50,
    "tests/runtime_binding/test_authenticated_loaders.py": 5,
    "tests/runtime_binding/test_config.py": 158,
    "tests/runtime_binding/test_custody.py": 59,
    "tests/runtime_binding/test_https.py": 15,
    "tests/runtime_binding/test_issuer.py": 71,
    "tests/runtime_binding/test_issuer_edges.py": 27,
    "tests/runtime_binding/test_lifecycle.py": 46,
    "tests/runtime_binding/test_lifecycle_process.py": 8,
    "tests/runtime_binding/test_loaders.py": 42,
    "tests/runtime_binding/test_runtime.py": 47,
    "tests/runtime_binding/test_state.py": 53,
    "tests/runtime_binding/test_supervisor.py": 45,
    "tests/runtime_binding/test_supervisor_access.py": 12,
    "tests/factory_binding/test_binding.py": 147,
    "tests/factory_binding/test_owner_integration.py": 7,
}


def _nodes(module, *functions):
    return tuple("tests/runtime_binding/" + module + ".py::test_" + name for name in functions)


CASES = {
    "I01": _nodes("test_issuer", "real_signature_and_cache", "x5t_is_metadata_and_backdated_nbf_is_allowed",
                  "64_external_keys_project_into_unchanged_core_limit"),
    "I02": _nodes("test_https", "actual_tls_requires_chain_and_hostname",
                  "actual_transport_rejects_malformed_or_oversized_response", "actual_transport_does_not_follow_redirect")
           + _nodes("test_issuer", "bad_documents_refuse", "key_set_ambiguity_or_incompatible_rsa_refuses"),
    "I03": _nodes("test_issuer", "unknown_key_rotates_once_and_removed_key_never_returns",
                  "failed_refresh_has_no_stale_fallback_or_error_payload",
                  "concurrent_initial_verification_coalesces_one_refresh")
           + _nodes("test_issuer_edges", "removed_snapshot_cannot_return_after_concurrent_rotation"),
    "I04": _nodes("test_config", "each_signed_launch_claim_must_match_approved_selection",
                  "changed_measured_source_refuses", "each_changed_protection_setting_refuses"),
    "I05": _nodes("test_issuer", "token_time_rules_survive_adapter", "expiry_during_fetch_is_checked_before_signer",
                  "clock_regression_refuses_without_using_cached_keys")
           + _nodes("test_issuer_edges", "token_expiry_during_crypto_is_not_returned"),
    "G01": _nodes("test_loaders", "current_records_and_challenge_feed_existing_gate",
                  "current_policy_cannot_be_replaced_or_revoked", "current_challenge_is_bound_to_service_subject_request_and_time")
           + _nodes("test_authenticated_loaders", "matching_metadata_cannot_replace_actual_client_authentication"),
    "G02": _nodes("test_supervisor", "controlled_live_launch_yields_existing_observation_and_one_proof",
                  "actual_worker_configuration_binding_cannot_be_self_reported", "owning_proof_verifier_accepts_measured_supervised_result")
           + _nodes("test_supervisor_access", "worker_valid_observation_request_is_denied",
                    "denial_probe_detects_excess_worker_permission", "outage_does_not_count_as_worker_denial"),
    "G03": _nodes("test_custody", "owning_proof_worker_valid_preimage_denial_and_cleanup",
                  "excess_worker_permission_mutation_breaks_denial_probe", "custody_outage_does_not_pass_worker_denial_probe")
           + ("tests/factory_binding/test_owner_integration.py::test_owning_custody_and_cleanup",),
    "S01": _nodes("test_state", "runtime_never_creates_missing_store", "runtime_never_recreates_removed_database",
                  "ambiguous_custody_failure_stays_consumed_after_restart", "concurrent_reservations_have_exactly_one_winner",
                  "process_exit_after_commit_is_consumed_on_restart", "owning_proof_accepts_initialized_state_and_restart_refuses_reuse"),
    "L01": _nodes("test_lifecycle_process", "real_owning_proof_cleanup_and_retained_state",
                  "independent_expiry_cleanup_survives_runner_hard_exit", "missing_independent_reader_cannot_qualify_cleanup",
                  "success_acknowledgement_without_actual_file_removal_fails_independent_audit",
                  "actual_replacement_generation_is_preserved_and_fails_cleanup"),
    "R01": _nodes("test_config", "sensitive_readback_exception_is_redacted")
           + _nodes("test_issuer_edges", "transport_binding_error_payload_is_also_sanitized")
           + _nodes("test_loaders", "service_outage_exposes_only_fixed_error")
           + _nodes("test_lifecycle", "failure_and_cancellation_finalize_before_propagation"),
}
