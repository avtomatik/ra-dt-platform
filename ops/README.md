# RADP operational scripts

Run these commands **from the repository root**. They also work when invoked by an
absolute path from another working directory. They resolve the Compose project
relative to the scripts, rather than assuming the current directory contains
`docker-compose.yml`.

All scripts under `ops/scripts/` must be executable (`chmod +x ops/scripts/*.sh`
on Unix if the file permissions were lost during copying).

## First-time configuration

```bash
cp .env.example .env
cp .env.compose.example .env.compose     # test/local
# or: cp .env.compose.production.example .env.compose  # production
cp config/certificate-folders.toml.example config/certificate-folders.toml
```

Edit `.env` for application settings, including `RADP_REMOTE_RA__BASE_URL`,
`.env.compose` for Docker image/identity and deployment mode, and
`config/certificate-folders.toml` for the certificate folder list. **Certificate
folder names do not belong in `.env`.** **Never concatenate the two files.** The first configures the application;
the second supplies Docker image, container identity, and production mapping
settings. Use `DEPLOY_ENVIRONMENT=test` (default) for emulator/local deployments
without static host mapping. For production, use `DEPLOY_ENVIRONMENT=production`
and `DEPLOY_RA_HOST_IP=127.1.1.1` (set the actual customer RA IP). The
`extra_hosts` hostname is *derived* from `.env`'s
`RADP_REMOTE_RA__BASE_URL`, so it cannot drift from that configured URI.
The production-only overlay is `docker-compose.production.yml`.
Both Compose files use legacy-compatible version 2.4 syntax to support the
Astra offline bundle's pinned docker-compose 1.29.2. Set
`COMPOSE_PROJECT_NAME=radp` consistently for the Ofelia scheduler (the loader
also defaults it to `radp` if omitted). Do not commit `.env`
or the local TOML configuration.

The provided Compose stack does not include RA-Emulator: configure
`RADP_REMOTE_RA__BASE_URL` to point to a separately reachable RA endpoint.

## Commands

| Command | Purpose |
| --- | --- |
| `./ops/scripts/compose.sh config --quiet` | Validate selected Compose files and interpolated configuration |
| `./ops/scripts/compose.sh ps` | Compose access through the two-file deployment loader |
| `./ops/scripts/deploy.sh` | Deploy prebuilt images after identity and mount checks |
| `./ops/scripts/showcase.sh --no-open` | Build/start the stack, check health, and display local URLs |
| `./ops/scripts/showcase.sh --sync --no-open` | Same, then request certificate synchronization |
| `./ops/scripts/status.sh` | Read-only service and application status |
| `./ops/scripts/status.sh --logs` | Status plus recent application logs |
| `./ops/scripts/rebuild-stack.sh` | Rebuild/recreate the stack without removing volumes |
| `./ops/scripts/rebuild-stack.sh --no-cache` | Rebuild without cached build layers |
| `./ops/scripts/rebuild-service.sh platform` | Rebuild/recreate one Compose service |
| `./ops/scripts/update-cert-thumbprint.sh HEX` | Update the local `.env` thumbprint and redeploy `platform` |

`showcase.sh --sync`, `rebuild-*`, and `update-cert-thumbprint.sh` have side
effects. Read the command flags before using them in production. In particular,
`rebuild-stack.sh` recreates the services, but does **not** delete volumes.

### Environment overrides

- `RADP_PROJECT_DIR`: deployment directory containing `docker-compose.yml`
  (defaults to the repository root)
- `RADP_APP_SERVICE`: Compose application service (default `platform`)
- `RADP_APP_URL`: browser and API base URL (default `http://127.0.0.1:9000`)
- `RADP_HEALTH_URL`: health-check URL (defaults to `$RADP_APP_URL/health`)

For every command, including offline preparation and installation, the safe
configuration loader parses `.env` and `.env.compose` as data rather than
executing them as shell scripts. Use `./ops/scripts/compose.sh ...` in place of
raw `docker compose ...` or `docker-compose ...`; this is also compatible with
legacy Compose 1.29, which cannot be assumed to support repeated `--env-file`.
The scripts run Compose from `RADP_PROJECT_DIR`. If using a different project
installation, make sure its `.env`, Compose file, and folder TOML have been
configured. `status.sh --help` and other supported help commands do not
require Docker.

### Validation

```bash
bash -n ops/lib/common.sh ops/scripts/*.sh
python -m pytest -q tests/test_ops_scripts.py
```

The tests use simulated Docker and HTTP commands, so a successful test does
not establish that the actual Docker daemon or remote RA is reachable.
