# Partial offline bundle

This mode prepares the RADP runtime bundle and images only. It does not run APT,
resolve package dependencies, download/index/package DEBs, or install/upgrade any
host packages. `HOST-REQUIREMENTS.txt` records the Docker Engine/CLI and Compose
versions expected by the bundle. The target administrator is responsible for
provisioning and validating those host packages and their complete dependency
closure before running `install.sh`.

The target must also provide an OpenSSL CLI supporting
`openssl enc -aes-256-cbc -pbkdf2 -iter` for decrypting the protected `.env` file.
No exact OpenSSL version is pinned in PARTIAL mode; the target's OpenSSL command
is exercised by the actual decrypt operation.

The installer validates Docker/Compose versions and daemon availability. It does
not invoke APT or dpkg package installation commands. It still enables/starts the
Docker systemd service, loads the packaged images and starts the RADP Compose
project. Use a fresh application deployment directory and preserve any existing
application data; it does not remove Docker volumes.
