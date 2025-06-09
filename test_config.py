import os
from config import load_config

def test_env_overrides(tmp_path, monkeypatch):
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("model_name: a\nollama_url: http://x")
    monkeypatch.setenv("PCRC_CONFIG", str(cfg_file))
    monkeypatch.setenv("PCRC_MODEL", "b")
    monkeypatch.setenv("PCRC_OLLAMA_URL", "http://y")
    cfg = load_config()
    assert cfg.model_name == "b"
    assert cfg.ollama_url == "http://y"
