import os

from src import config


def test_load_environment_refreshes_changed_env_file(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("SUPABASE_URL=https://first.example\n", encoding="utf-8")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setattr(config, "_ENV_STATE", None)
    monkeypatch.setattr(config, "_ENV_LOADED_KEYS", set())

    config.load_environment(env_path)

    assert os.environ["SUPABASE_URL"] == "https://first.example"

    env_path.write_text(
        "\n".join(
            [
                "SUPABASE_URL=https://second.example",
                "SUPABASE_SERVICE_ROLE_KEY=service-role-key",
            ]
        ),
        encoding="utf-8",
    )

    config.load_environment(env_path)

    assert os.environ["SUPABASE_URL"] == "https://second.example"
    assert os.environ["SUPABASE_SERVICE_ROLE_KEY"] == "service-role-key"


def test_load_environment_preserves_external_environment(tmp_path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("SUPABASE_URL=https://from-file.example\n", encoding="utf-8")
    monkeypatch.setenv("SUPABASE_URL", "https://from-shell.example")
    monkeypatch.setattr(config, "_ENV_STATE", None)
    monkeypatch.setattr(config, "_ENV_LOADED_KEYS", set())

    config.load_environment(env_path)

    assert os.environ["SUPABASE_URL"] == "https://from-shell.example"
