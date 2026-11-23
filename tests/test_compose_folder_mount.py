from pathlib import Path


def test_all_services_loading_radp_settings_mount_the_folder_file():
    compose = (
        Path(__file__).resolve().parents[1] / "docker-compose.yml"
    ).read_text(encoding="utf-8")
    # Both services inherit the shared YAML anchor: verify its content as well
    # as the inheriting services, not the expanded text of individual sections.
    shared = compose.split("x-radp-common: &radp-common\n", 1)[1].split(
        "\nservices:", 1
    )[0]
    assert "./config:/app/config:ro" in shared
    for service, following in (
        ("db-init", "platform"),
        ("platform", "scheduler"),
    ):
        section = compose.split(f"  {service}:\n", 1)[1].split(
            f"  {following}:\n", 1
        )[0]
        assert "<<: *radp-common" in section
