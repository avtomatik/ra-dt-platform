"""Regression checks for root-invocable operational shell scripts.

No Docker daemon or external service is needed: command-line tools are replaced
by small test doubles and operations run against a disposable project directory.
"""

import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "ops" / "scripts"


@pytest.mark.parametrize(
    "name",
    [
        "showcase.sh",
        "rebuild-service.sh",
        "rebuild-stack.sh",
        "status.sh",
        "update-cert-thumbprint.sh",
    ],
)
def test_scripts_are_executable(name: str):
    assert os.access(SCRIPTS / name, os.X_OK)


@pytest.mark.parametrize(
    "name",
    ["showcase.sh", "rebuild-stack.sh", "status.sh"],
)
def test_help_works_from_any_directory_without_docker(
    name: str, tmp_path: Path
):
    for cwd in (PROJECT_ROOT, tmp_path):
        result = subprocess.run(
            [str(SCRIPTS / name), "--help"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert "Usage:" in result.stdout


@pytest.fixture
def mock_ops(tmp_path: Path):
    project_dir = tmp_path / "deploy project with spaces"
    project_dir.mkdir()
    (project_dir / "docker-compose.yml").write_text(
        "services: {}\n", encoding="utf-8"
    )
    (project_dir / ".env").write_text("UNCHANGED=value\n", encoding="utf-8")
    (project_dir / ".env.compose").write_text(
        "DEPLOY_ENVIRONMENT=test\n", encoding="utf-8"
    )
    bin_dir = tmp_path / "mock-bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s|%s\\n" "$PWD" "$*" >> "$MOCK_DOCKER_LOG"\n'
        'if [[ "$1" == "--version" ]]; then echo "Docker mock"; fi\n',
        encoding="utf-8",
    )
    docker.chmod(0o755)
    curl = bin_dir / "curl"
    curl.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s|%s\\n" "$PWD" "$*" >> "$MOCK_CURL_LOG"\n'
        'if [[ " $* " == *" --write-out "* ]]; then printf 200; '
        'elif [[ " $* " == *" -X POST "* ]]; then printf \'{"synchronized":0}\'; fi\n',
        encoding="utf-8",
    )
    curl.chmod(0o755)
    docker_log = tmp_path / "docker.log"
    curl_log = tmp_path / "curl.log"
    env = os.environ.copy()
    env.update(
        PATH=f"{bin_dir}:{os.environ['PATH']}",
        RADP_PROJECT_DIR=str(project_dir),
        RADP_APP_URL="http://127.0.0.1:9123/",
        MOCK_DOCKER_LOG=str(docker_log),
        MOCK_CURL_LOG=str(curl_log),
    )
    return project_dir, env, docker_log, curl_log


def _invoke(name: str, args: list[str], cwd: Path, env: dict[str, str]):
    result = subprocess.run(
        [str(SCRIPTS / name), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    return result


def test_showcase_runs_from_repository_root_and_uses_application_port(
    mock_ops,
):
    project, env, docker_log, curl_log = mock_ops
    result = _invoke("showcase.sh", ["--sync", "--no-open"], PROJECT_ROOT, env)
    assert f"Project: {project}" in result.stdout
    assert "Application: http://127.0.0.1:9123" in result.stdout
    assert (
        f"{project}|compose -f {project}/docker-compose.yml up -d --build"
        in docker_log.read_text()
    )
    calls = curl_log.read_text()
    assert "http://127.0.0.1:9123/health" in calls
    assert "http://127.0.0.1:9123/admin/certificates/sync" in calls
    assert ":8000/" not in calls


def test_rebuild_scripts_run_from_other_working_directory(
    mock_ops, tmp_path: Path
):
    project, env, docker_log, curl_log = mock_ops
    _invoke("rebuild-stack.sh", ["--no-cache"], tmp_path, env)
    _invoke("rebuild-service.sh", ["platform"], tmp_path, env)
    calls = docker_log.read_text()
    assert (
        f"{project}|compose -f {project}/docker-compose.yml build --no-cache"
        in calls
    )
    assert (
        f"{project}|compose -f {project}/docker-compose.yml build platform"
        in calls
    )
    assert (
        f"{project}|compose -f {project}/docker-compose.yml up -d --no-deps --force-recreate platform"
        in calls
    )
    assert "http://127.0.0.1:9123/health" in curl_log.read_text()


def test_update_thumbprint_runs_from_root_without_modifying_repo_env(mock_ops):
    project, env, docker_log, _ = mock_ops
    _invoke(
        "update-cert-thumbprint.sh", ["0123456789abcdef"], PROJECT_ROOT, env
    )
    content = (project / ".env").read_text()
    assert "UNCHANGED=value" in content
    assert "RADP_TRANSPORT__CERT_THUMBPRINT=0123456789abcdef" in content
    assert (
        f"{project}|compose -f {project}/docker-compose.yml build platform"
        in docker_log.read_text()
    )


def test_status_runs_from_elsewhere_and_reports_correct_health_url(
    mock_ops, tmp_path: Path
):
    project, env, docker_log, curl_log = mock_ops
    result = _invoke("status.sh", ["--logs"], tmp_path, env)
    assert f"Project directory: {project}" in result.stdout
    assert "All critical checks passed." in result.stdout
    assert "http://127.0.0.1:9123/health" in curl_log.read_text()
    assert (
        f"{project}|compose -f {project}/docker-compose.yml logs --tail=30 platform"
        in docker_log.read_text()
    )
