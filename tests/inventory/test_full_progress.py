from kmap.inventory.full_progress import (
    NamespaceInspectionMetrics,
    NamespaceInspectionTimings,
    bucket_candidate_count,
    namespace_timing_summary,
)


def test_bucket_candidate_count_sums_present_candidate_lists():
    assert (
        bucket_candidate_count(
            {
                "workloads": [
                    {"bucket_candidates": [{"bucket": "reports"}, {"bucket": "archive"}]},
                    {"bucket_candidates": []},
                    {"service_name": "worker"},
                    {"bucket_candidates": None},
                ]
            }
        )
        == 2
    )


def test_namespace_timing_summary_formats_metrics_and_bucket_count():
    timings = NamespaceInspectionTimings(workloads=1.24, configmaps=0.02, secrets=0.0, pods=0.4, total=1.7)
    metrics = NamespaceInspectionMetrics(runtime={"vault_exec_seconds": 0.3, "vault_execs": 2}, workloads=3)

    assert namespace_timing_summary(
        "api-prod",
        {"workloads": [{"bucket_candidates": [{"bucket": "reports"}]}, {"bucket_candidates": [{"bucket": "logs"}]}]},
        timings,
        metrics,
    ) == (
        "[kmap] inspected api-prod: total=1.7s workloads=1.2s configmaps=0.0s "
        "secrets=0.0s pods=0.4s vault_exec=0.3s execs=2 selected=3 buckets=2"
    )
