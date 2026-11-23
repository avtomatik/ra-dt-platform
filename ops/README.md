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
cat .env.compose.example >> .env
cp config/certificate-folders.toml.example config/certificate-folders.toml
```

Edit `.env` for the real connection and deployment settings, and edit
`config/certificate-folders.toml` for the certificate folder list. **Certificate
folder names do not belong in `.env`.** The two environment examples have
complementary keys: the first configures the application; the second supplies
required Docker Compose image and container-user settings. Do not commit `.env`
or the local TOML configuration.

The provided Compose stack does not include RA-Emulator: configure
`RADP_REMOTE_RA__BASE_URL` to point to a separately reachable RA endpoint.

## Commands

| Command | Purpose |
| --- | --- |
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
