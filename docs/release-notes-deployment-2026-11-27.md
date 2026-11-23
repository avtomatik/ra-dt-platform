# RADP deployment and offline-flow hardening — 2026-11-27

This change set applies to the uploaded RADP project, preserving its data model
and application API.

## Applied changes

1. Addressed all four findings in the supplied `shellcheck-output.txt` (SC2155,
   SC2034 and two SC2164 instances). See
   `docs/operations/shellcheck-remediation.md`.
2. Split Compose runtime settings into `.env` and `.env.compose`, consistently
   read by ops and offline tooling without executing either file.
3. Moved the production RA `/etc/hosts` override into a conditional Compose
   overlay. `DEPLOY_RA_HOSTNAME` is derived from the application base URL;
   `DEPLOY_RA_HOST_IP` is the configurable customer address.
4. Kept local/test mode free of static host mappings. Added separate example
   Compose environment files and a wrapper for legacy/current Compose.
5. Restored offline parity: both files are encrypted, checked, delivered and
   decrypted; certificate-folder TOML and the production Compose overlay ship
   with full and partial bundles. Offline installer checks port 9000.
6. Adjusted the Compose schema for legacy `docker-compose` 1.29.2 by declaring
   version 2.4 and dropping its unsupported `pull_policy` keys. The installer
   still verifies the image manifest and preloads images.
7. Set a stable Compose project name for Ofelia's project-label filter, and
   bound the host PostgreSQL port to loopback instead of all interfaces.
8. Added deployment-mode, command and encryption/decryption regression tests.

## Verification scope

- `python -m pytest -q`: 112 tests passed.
- `./offline/tests/run-tests.sh`: passed, including both FULL/PARTIAL ZIP
  fixture assembly, encrypted environment restoration and local APT
  dependency-resolution fixture tests.
- `bash -n`: passed for all shell scripts.
- Static YAML structural checks: passed for both Compose files.

Not executed: real ShellCheck (binary unavailable here), Docker Compose CLI,
Docker daemon, Astra Linux SE 1.7.8 deployment, customer RA connectivity, and
actual customer bundle preparation using vendor images and repositories. The
historical ShellCheck warnings are fixed in source but CI should verify the new
scripts after checkout.

## Preparing the customer bundle

1. Copy `.env.example` to `.env` and populate the real credentials, URLs and
   RA transport settings. Do not commit it.
2. Copy `.env.compose.production.example` to `.env.compose`; populate the actual
   application image, container identity and `DEPLOY_RA_HOST_IP`.
3. Configure `config/certificate-folders.toml`.
4. Run `./ops/scripts/compose.sh config --quiet` on a machine with Compose.
5. On a connected matching Astra preparation host, prepare and package full or
   partial offline artifacts using the documented `offline/<mode>/` scripts.
6. On the isolated customer host, run the supplied installer in a fresh
   extraction directory. Verify RA hostname resolution, CryptoPro connectivity,
   and sync separately before the demonstration.

The delivered source ZIP intentionally omits actual `.env` and `.env.compose`
values to avoid redistributing local credentials.
