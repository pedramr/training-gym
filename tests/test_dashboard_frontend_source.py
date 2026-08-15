from __future__ import annotations

import pytest

from modal_training_gym import _dashboard


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv(_dashboard.REPO_URL_ENV, raising=False)
    monkeypatch.delenv(_dashboard.REPO_REF_ENV, raising=False)


def test_defaults_to_upstream_main():
    assert _dashboard._frontend_source() == (
        _dashboard.DEFAULT_REPO_URL,
        _dashboard.DEFAULT_REPO_REF,
    )


@pytest.mark.parametrize(
    "ref",
    [
        "main",
        "v1.2.3",
        "release/2026-08",
        "a64d966f771e5c5139b6cba1dd743a215010c7ba",  # exact commit
    ],
)
def test_accepts_branches_tags_and_commit_shas(monkeypatch, ref):
    monkeypatch.setenv(_dashboard.REPO_REF_ENV, ref)

    assert _dashboard._frontend_source()[1] == ref


def test_accepts_a_fork_url(monkeypatch):
    monkeypatch.setenv(
        _dashboard.REPO_URL_ENV, "https://github.com/someone/training-gym.git"
    )
    monkeypatch.setenv(_dashboard.REPO_REF_ENV, "my-branch")

    assert _dashboard._frontend_source() == (
        "https://github.com/someone/training-gym.git",
        "my-branch",
    )


@pytest.mark.parametrize(
    ("env", "value", "why"),
    [
        ("REPO_REF_ENV", "-o=x", "leading dash reads as a git option"),
        ("REPO_REF_ENV", "main; rm -rf /", "shell metacharacters"),
        ("REPO_REF_ENV", "main$(id)", "command substitution"),
        ("REPO_REF_ENV", "a b", "whitespace"),
        ("REPO_URL_ENV", "--upload-pack=x", "leading dash reads as a git option"),
        ("REPO_URL_ENV", "https://x.example/r.git`id`", "backticks"),
    ],
)
def test_rejects_values_that_could_reach_the_shell(monkeypatch, env, value, why):
    monkeypatch.setenv(getattr(_dashboard, env), value)

    with pytest.raises(ValueError, match="not a valid git repo/ref"):
        _dashboard._frontend_source()
