from kmap.env import load_dotenv_file, parse_dotenv_line


def test_parse_dotenv_line_handles_comments_quotes_and_empty_lines():
    assert parse_dotenv_line("# comment") == ("", "")
    assert parse_dotenv_line("") == ("", "")
    assert parse_dotenv_line("KMAP_ENV=prod") == ("KMAP_ENV", "prod")
    assert parse_dotenv_line("GITLAB_TOKEN='secret value'") == ("GITLAB_TOKEN", "secret value")
    assert parse_dotenv_line('KMAP_PRODUCT="demo"') == ("KMAP_PRODUCT", "demo")


def test_load_dotenv_file_does_not_override_existing_environment(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KMAP_PRODUCT=from-file\nKMAP_ENV=prod\nKMAP_PROJECT=\n", encoding="utf-8")
    monkeypatch.setenv("KMAP_PRODUCT", "from-env")
    monkeypatch.delenv("KMAP_ENV", raising=False)
    monkeypatch.delenv("KMAP_PROJECT", raising=False)

    load_dotenv_file(env_file)

    assert __import__("os").environ["KMAP_PRODUCT"] == "from-env"
    assert __import__("os").environ["KMAP_ENV"] == "prod"
    assert "KMAP_PROJECT" not in __import__("os").environ
