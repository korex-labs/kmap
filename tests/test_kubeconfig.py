from pathlib import Path

from kmap.kubernetes.kubeconfig import default_kubeconfig_path


def test_default_kubeconfig_path_prefers_explicit_env(monkeypatch, tmp_path):
    monkeypatch.setenv("KUBECONFIG", "~/custom-kubeconfig")
    monkeypatch.setenv("HOME", str(tmp_path))

    assert default_kubeconfig_path() == str(Path.home() / "custom-kubeconfig")


def test_default_kubeconfig_path_uses_existing_default_location(monkeypatch, tmp_path):
    kubeconfig = tmp_path / ".kube" / "config"
    kubeconfig.parent.mkdir()
    kubeconfig.write_text("apiVersion: v1\n")
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert default_kubeconfig_path() == str(kubeconfig)


def test_default_kubeconfig_path_is_empty_when_no_config_exists(monkeypatch, tmp_path):
    monkeypatch.delenv("KUBECONFIG", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    assert default_kubeconfig_path() == ""
