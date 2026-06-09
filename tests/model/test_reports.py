import json

import pytest

from kmap.model.reports import load_workloads_from_reports


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
