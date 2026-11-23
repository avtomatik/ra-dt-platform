from pathlib import Path


def test_all_services_loading_radp_settings_mount_the_folder_file():
    compose_path = Path(__file__).resolve().parents[1] / "docker-compose.yml"
    compose = compose_path.read_text(encoding="utf-8")
    for service, following_service in (
        ("db-init", "platform"),
        ("platform", "scheduler"),
    ):
        section = compose.split(f"  {service}:\n", 1)[1].split(
            f"  {following_service}:\n", 1
        )[0]
        assert "./config:/app/config:ro" in section
