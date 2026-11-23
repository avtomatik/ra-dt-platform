"""Deployment mode contracts without a Docker daemon or external RA."""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "ops/lib/deployment-env.sh"


def _run(
    tmp_path: Path, *, mode: str, ra_url: str, host_ip: str | None
) -> subprocess.CompletedProcess[str]:
    (tmp_path / "docker-compose.yml").write_text("services: {}\n")
    (tmp_path / "docker-compose.production.yml").write_text("services: {}\n")
    (tmp_path / ".env").write_text(f"RADP_REMOTE_RA__BASE_URL={ra_url}\n")
    (tmp_path / ".env.compose").write_text(
        f"DEPLOY_ENVIRONMENT={mode}\n"
        + (f"DEPLOY_RA_HOST_IP={host_ip}\n" if host_ip is not None else "")
    )
    command = f'''source "{LOADER}"
radp_config_activate "$1" || exit 4
printf '%s\\n' "${{DEPLOY_RA_HOSTNAME:-<unset>}}" "${{RADP_COMPOSE_FILES[*]}}"'''
    return subprocess.run(
        ["bash", "-c", command, "_", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "DEPLOY_RA_HOSTNAME": ""},
    )


def test_test_mode_does_not_force_static_mapping(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        mode="test",
        ra_url="http://ra-emulator:9000/api/ra/",
        host_ip=None,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0] == "<unset>"
    assert "docker-compose.production.yml" not in result.stdout


def test_production_mapping_uses_hostname_from_base_url(
    tmp_path: Path,
) -> None:
    result = _run(
        tmp_path,
        mode="production",
        ra_url="http://ra-server-name/api/ra/",
        host_ip="127.1.1.1",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0] == "ra-server-name"
    assert "docker-compose.production.yml" in result.stdout
    production = (ROOT / "docker-compose.production.yml").read_text()
    assert "${DEPLOY_RA_HOSTNAME:" in production
    assert "${DEPLOY_RA_HOST_IP:" in production
    assert "extra_hosts:" not in (ROOT / "docker-compose.yml").read_text()


@pytest.mark.parametrize(
    "mode,ip,url",
    [
        ("production", None, "http://ra-server-name/api/ra/"),
        ("production", "not an ip !", "http://ra-server-name/api/ra/"),
        ("production", "256.0.0.10", "http://ra-server-name/api/ra/"),
        ("production", "127.1.1.1", "broken-url"),
        ("unknown", "127.1.1.1", "http://ra-server-name/api/ra/"),
    ],
)
def test_invalid_configuration_fails_early(
    tmp_path: Path, mode: str, ip: str | None, url: str
) -> None:
    result = _run(tmp_path, mode=mode, ra_url=url, host_ip=ip)
    assert result.returncode != 0
    assert "[radp-config][ERROR]" in result.stderr


def test_environment_file_is_not_executed(tmp_path: Path) -> None:
    marker = tmp_path / "unexpected-shell-execution"
    (tmp_path / "docker-compose.yml").write_text("services: {}\n")
    (tmp_path / ".env").write_text(
        f"RADP_REMOTE_RA__BASE_URL=$(touch {marker})\n"
    )
    (tmp_path / ".env.compose").write_text("DEPLOY_ENVIRONMENT=test\n")
    result = subprocess.run(
        [
            "bash",
            "-c",
            f'source "{LOADER}"; radp_config_activate "$1"',
            "_",
            str(tmp_path),
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0
    assert not marker.exists()


def test_legacy_compose_syntax_is_preserved() -> None:
    # Legacy docker-compose 1.29.2 accepts the version 2.4 schema and the
    # completed-init dependency; it does not support pull_policy.
    for name in ("docker-compose.yml", "docker-compose.production.yml"):
        compose = (ROOT / name).read_text()
        assert compose.startswith(('version: "2.4"', "#"))
        assert 'version: "2.4"' in compose
        assert "pull_policy:" not in compose
    base = (ROOT / "docker-compose.yml").read_text()
    assert "condition: service_completed_successfully" in base
    assert "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}" in base
