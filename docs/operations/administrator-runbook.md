# RADP Administrator Runbook

This runbook describes the commands present in the RADP 0.5.0 source archive. It
is intended for an administrator with access to the source repository or the
installed host. Adapt paths and environment-specific image/registry settings to
the approved deployment, but do not remove the offline bundle verification
steps.

## 1. Configuration

Create `.env` from `.env.example` and configure the RA, transport, and database
settings. The RA folder setting is a comma-separated list:

```dotenv
RADP_REMOTE_RA__CERTIFICATE_FOLDERS=production
# or
RADP_REMOTE_RA__CERTIFICATE_FOLDERS=production,archive
```

Pydantic parses this as a tuple. Each folder is synchronized independently.
The optional `RADP_REPORTING__PROJECTION_FIELDS` setting selects a comma-separated
subset of the existing inventory fields. Omit it to retain every current RADP
inventory column.

Never place production secrets, thumbprints, private keys, or credentials in
source control or in a package shared outside the approved deployment channel.
The offline bundle scripts encrypt the `.env` payload; transfer its passphrase
separately.

## 2. Development and pre-release checks

From the repository root, with the required package sources available:

```bash
uv sync --locked --group dev
uv run pytest
uv run python -m radp doctor
```

The full test suite should be run with the same Python version and locked
dependencies used for the release build. The `doctor` command performs live
checks and therefore requires the configured database, RA endpoint, and
transport to be reachable.

For shell/offline deployment tooling:

```bash
./offline/tests/run-tests.sh
```

Review the output and the generated package manifests before promoting a build.

## 3. Host execution

The common operational commands are:

```bash
uv run python -m radp --help
uv run python -m radp doctor
uv run python -m radp sync run
uv run python -m radp sync run --certificate-folders "production,archive"
uv run python -m radp serve --host 0.0.0.0 --port 9000
```

`--certificate-folders` is an optional, comma-separated, one-run override. When
omitted, `RADP_REMOTE_RA__CERTIFICATE_FOLDERS` from `.env` or the environment is
used.

## 4. Docker Compose operations

Validate the Compose configuration before changing the running deployment:

```bash
docker-compose config -q
# or
docker compose config -q
```

Start the stack:

```bash
docker-compose up -d
```

Inspect service state and logs:

```bash
docker-compose ps
docker-compose logs --tail=100
docker-compose logs -f platform
```

Check the application health endpoint:

```bash
curl -fsS http://localhost:9000/health
```

Restart only the application service:

```bash
docker-compose restart platform
```

Restart all services without deleting data:

```bash
docker-compose restart
```

Stop the stack:

```bash
docker-compose stop
```

Start a previously stopped stack:

```bash
docker-compose up -d
```

**Never use `docker-compose down -v` or `docker compose down -v` as a routine
restart command.** The PostgreSQL volume is persistent data. Volume removal is a
destructive operation and requires an approved backup and recovery procedure.

Generated reports are stored under `data/exports/`, which is mounted into the
application container. Do not remove this directory as part of an application
restart.

## 5. Offline deployment bundle creation

Bundle creation is performed on the connected, approved preparation host, not
on the air-gapped target. The scripts require the host prerequisites described
in `offline/README.md`.

### Full bundle

The FULL mode packages the Docker/Compose OS dependency closure as well as the
RADP runtime:

```bash
sudo ./offline/full/prepare.sh
sudo ./offline/full/package.sh
```

Expected output:

```text
release/radp-offline-full.zip
release/radp-offline-full.zip.sha256
```

### Partial bundle

The PARTIAL mode packages the RADP runtime and images but deliberately omits OS
package payloads. The target administrator must provision Docker, Compose, and
OpenSSL separately from an approved package collection:

```bash
sudo ./offline/partial/prepare.sh
sudo ./offline/partial/package.sh
```

Expected output:

```text
release/radp-offline-partial.zip
release/radp-offline-partial.zip.sha256
```

The FULL and PARTIAL modes are alternatives, not sequential steps. Follow the
matching README and installer for the selected mode.

## 6. Air-gapped target installation

Transfer the ZIP and its `.sha256` sidecar to the target. Transfer the `.env`
passphrase through a separate approved channel. Verify the archive before
extracting it into a new deployment directory.

FULL example:

```bash
sha256sum -c radp-offline-full.zip.sha256
sudo mkdir -p /opt/radp-deploy-full
sudo unzip radp-offline-full.zip -d /opt/radp-deploy-full
cd /opt/radp-deploy-full/radp-offline-full
sudo ./install.sh
```

PARTIAL example:

```bash
sha256sum -c radp-offline-partial.zip.sha256
sudo mkdir -p /opt/radp-deploy-partial
sudo unzip radp-offline-partial.zip -d /opt/radp-deploy-partial
cd /opt/radp-deploy-partial/radp-offline-partial
sudo ./install.sh
```

Do not run an installer over an existing deployment directory. The installers
are designed for a fresh extraction and refuse to overwrite an existing `.env`.
They load the packaged images and start the Compose services without building
images on the target.

After installation:

```bash
docker-compose ps
docker-compose logs --tail=100 platform
curl -fsS http://localhost:9000/health
```

## 7. Synchronization and report operations

Run synchronization on demand:

```bash
docker-compose exec platform /app/.venv/bin/python -m radp sync run
```

The normal container command uses the folder list in `.env`. The command-line
folder override is available when running `radp sync run` directly; for
container operation, edit the configured environment only through the approved
change process and recreate the platform container after validation.

Reports are available from the application at `/`:

- `/web` — local PostgreSQL certificate overview.
- `/export/preview` — report preview.
- `/export/certificates?status=ALL` — all lifecycle states.
- `/export/certificates?status=VALID` — VALID certificates not expired at the UTC
  date cutoff.

Optional query filters include `gid` and `as_of_date=YYYY-MM-DD`. Preview and
XLSX export use the same query contract.

## 8. Backup and rollback

The current archive does not define a complete organization-specific backup
schedule or retention policy. Before deployment, document and test:

- PostgreSQL backup creation and restore.
- `data/exports/` retention and backup requirements.
- Backup destination and access control.
- Restore verification and recovery time objectives.
- Previous image/bundle retention and application rollback.

Do not treat a Docker image archive as a database backup. Preserve the previous
known-good image/bundle and database backup independently.
