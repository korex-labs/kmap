from kmap.render.generated_files import remove_generated_file


def test_remove_generated_file_skips_non_utf8_stale_files(tmp_path):
    stale_file = tmp_path / "generated.dsl"
    stale_file.write_bytes(b"\xff\xfe\x00")

    remove_generated_file(stale_file)

    assert stale_file.exists()
