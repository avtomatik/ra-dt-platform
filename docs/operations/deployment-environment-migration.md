# RADP environment and offline-bundle migration

This release replaces the unconditional `extra_hosts` mapping with a production
Compose overlay, and makes both environment files first-class offline assets.

## Configuration layout

| File | Responsibility | Included in offline bundle? |
| --- | --- | --- |
| `.env` | Application runtime settings, remote RA URL, database configuration and credentials | Encrypted as `.env.enc` |
| `.env.compose` | Compose images, container identity, selected environment, optional production IP | Encrypted as `.env.compose.enc` |
| `config/certificate-folders.toml` | Certificate folders to synchronize | Yes, plaintext runtime configuration |
| `docker-compose.yml` | Shared services with no forced host alias | Yes |
| `docker-compose.production.yml` | Production-only `extra_hosts` mapping for `platform` | Yes |
| `ops/lib/deployment-env.sh` | Shared environment loader and Compose-file selector | Included in bundle as `deployment-env.sh` |

### Migration from the previous repository layout

1. Back up the current `.env`, `.env.compose`, and folder TOML locally. Do not commit or share the backups.
2. Ensure `.env` contains `RADP_REMOTE_RA__BASE_URL=http://ra-server-name/api/ra/` for the customer endpoint.
3. Keep all application secrets and `RADP_DATABASE__*` configuration in `.env`.
4. Put Compose-only `DEPLOY_*` variables in `.env.compose`. Copy the relevant example and merge your actual image references and UID/GID there.
5. For a customer installation, set `DEPLOY_ENVIRONMENT=production` and `DEPLOY_RA_HOST_IP=127.1.1.1` in `.env.compose` (replace with the actual site's address).
6. For development or emulator testing, set `DEPLOY_ENVIRONMENT=test` and omit the production-only IP. The default Compose model does not modify container `/etc/hosts`.
7. Keep `config/certificate-folders.toml` as the only folder-list source.
8. Run `./ops/scripts/compose.sh config --quiet`, then `./ops/scripts/status.sh`. Use the same wrapper for Compose operations rather than raw `docker compose`.
9. Prepare a new offline bundle using `./offline/full/prepare.sh` or `./offline/partial/prepare.sh`; do not reuse a previous ZIP built with the one-environment-file installer.

The production hostname is **not** configured twice. `radp_config_activate`
extracts `ra-server-name` from `RADP_REMOTE_RA__BASE_URL` and passes it to
`docker-compose.production.yml`; only the IPv4 address is independently
configured. This avoids mismatches between the hostname used by the API
client and the hostname injected into `/etc/hosts`.

The environment loader does not `source` `.env` files as shell scripts, so
shell substitutions and commands in them are never executed. It supports
simple dotenv `KEY=value` lines, comments, and enclosing single/double quotes.
Do not rely on Compose variable expansion *inside* those values.

## Offline installation contract

Both encrypted environment files have dedicated SHA-256 checksums. The installer
validates the archive checksum manifest before decrypting them, verifies both
plaintext hashes, creates mode `0600` files without overwriting existing files,
and rechecks deployment mode and the RA URL/IP relationship before Compose
startup. The bundle now also contains the folder configuration required by
both `db-init` and `platform`.

For safety, the host's PostgreSQL port is bound to `127.0.0.1:15432`
rather than all interfaces. The runtime-requirements health target is TCP
port **9000**, matching Compose.
Compose uses version **2.4** syntax for compatibility with the bundle's pinned
legacy `docker-compose` 1.29.2. Unsupported `pull_policy` entries were removed;
the offline installer still verifies and loads all required image references
before startup. `COMPOSE_PROJECT_NAME` defaults to `radp` and is used by Ofelia's
project-label filter. Modern Compose may issue an informational warning that
`version` is obsolete; it remains for the pinned legacy deployment. This
legacy compatibility is based on documented Compose behavior and requires a
real CLI validation on the target host.

The offline bundle builders remain specifically targeted to Astra Linux SE
1.7.8 amd64, with a preinstalled or locally bundled Docker and Compose version.
A validated ZIP is not proof of a deployment on the actual target.

## Validation

```bash
python -m pytest -q
./offline/tests/run-tests.sh
./ops/scripts/compose.sh config --quiet  # requires Docker Compose CLI
```

On the customer host, verify that `platform` resolves `ra-server-name` to the
configured IPv4 address and can actually connect through the required
CryptoPro transport before starting the scheduled synchronization. The offline
packager does **not** contain an automatically produced real customer-site
bundle: that still requires the connected Astra preparation host and its
required images and packages.
