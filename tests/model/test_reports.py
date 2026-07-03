import json

import pytest

from kmap.model.reports import load_workloads_from_reports, workloads_from_report


def test_load_workloads_from_reports_merges_report_discovery(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "app.report.json").write_text(
        json.dumps(
            {
                "discovery": {"context": "demo"},
                "workloads": [
                    {
                        "service_name": "api",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    files, workloads = load_workloads_from_reports(reports_dir)

    assert [path.name for path in files] == ["app.report.json"]
    assert workloads == [{"service_name": "api", "discovery": {"context": "demo"}}]


def test_load_workloads_from_reports_requires_reports(tmp_path):
    with pytest.raises(SystemExit, match=r"No \*.report.json found"):
        load_workloads_from_reports(tmp_path)


def test_workloads_from_report_rejects_malformed_workload_payloads():
    with pytest.raises(SystemExit, match="Invalid report workloads"):
        workloads_from_report({"workloads": "bad"})

    with pytest.raises(SystemExit, match="Invalid report workload"):
        workloads_from_report({"workloads": ["bad"]})
