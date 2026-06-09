from kmap.command import render_buckets
from kmap.inventory import buckets


def test_render_buckets_reexports_inventory_bucket_api():
    exported_names = set(render_buckets.__all__)

    assert exported_names == {
        "DEFAULT_BUCKET_REPORTS_DIR",
        "BucketUsageRow",
        "bucket_rows_for_report",
        "collect_bucket_usage_rows",
        "collect_bucket_usage_rows_from_reports",
        "render_buckets_html",
        "workload_bucket_rows",
        "write_bucket_report",
    }
    for name in exported_names:
        assert getattr(render_buckets, name) is getattr(buckets, name)
