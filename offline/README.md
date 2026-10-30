# RADP offline deployment scripts

This directory is intended to be copied into the RADP repository as `offline/`.
It provides two deployment modes with deliberately different responsibilities.

## Directory layout

```text
offline/
├── README.md
├── lib/
│   ├── common.sh
│   ├── install-common.sh
│   ├── package-common.sh
│   └── prepare-runtime.sh
├── full/
│   ├── prepare.sh
│   ├── package.sh
│   └── install.sh
└── partial/
    ├── prepare.sh
    ├── package.sh
    └── install.sh
```

- **`full`** creates a self-contained bundle. It downloads Docker, Compose and
  their dependency closure from the frozen Astra Linux SE 1.7.8 repositories,
  builds a local APT repository inside the bundle, and verifies that APT can
  resolve the required packages from that local repository alone.
- **`partial`** creates the complete RADP runtime bundle but omits the host OS
  package payload. It deliberately does not run `apt-get`, download `.deb` files,
  or include an OS package repository. “Partial” refers only to OS package
  provisioning; it is not a partial application/image deployment.
  Docker, Compose and OpenSSL must be provisioned separately by the target
  administrator from their verified package collection.

Both modes package the same application assets, Compose file, prebuilt images,
encrypted `.env`, SHA-256 checksums and target-platform metadata. The generated
archives are separate:

```text
release/radp-offline-full.zip
release/radp-offline-partial.zip
```

## Preparation host requirements

Run preparation on a connected Astra Linux SE 1.7.8 amd64 host. It must have:

- Bash, APT and dpkg tools (`dpkg-deb` is used to build the local package index).
- Docker Engine and a working Docker Compose command.
- OpenSSL, Python 3, `tar`, `sha256sum`, `awk`, `sed` and `paste`.
- Access to the frozen Astra Linux repositories for `full` mode.
- Access to the image registries used by the project.

The project layout expected by these scripts is the one from the existing RADP
repository: `pyproject.toml`, `uv.lock`, `docker/Dockerfile`,
`docker-compose.yml`, `.env`, and the `radp/`, `data/`, and `html/` directories.

## Build the full bundle

From the RADP repository root:

```bash
sudo ./offline/full/prepare.sh
sudo ./offline/full/package.sh
```

The preparation script pins the top-level packages to the versions currently
used by the project:

```text
docker.io=25.0.5.astra3+ci24
docker-compose=1.29.2-1astra.se1+ci1+b2
```

Override either package version only deliberately, for example:

```bash
sudo env RADP_DOCKER_PACKAGE_VERSION='25.0.5.astra3+ci24' \\
  RADP_COMPOSE_PACKAGE_VERSION='1.29.2-1astra.se1+ci1+b2' \\
  ./offline/full/prepare.sh
```

APT resolves the complete dependency closure with an empty package-status view,
so the set is not accidentally reduced by packages installed on the preparation
host. The downloaded archives are indexed from their embedded DEB control metadata. Before
preparation succeeds, a second APT operation is run against a `file:` source
pointing only at the generated local repository, with an empty status database.
That simulation fails if the local archive set cannot satisfy the requested
Docker/Compose/OpenSSL/CA-certificate installation.

The resulting `docker-install/package-inventory.tsv` records the package name,
version, architecture and archive filename. The exact two frozen repository
entries used for the download are preserved in `docker-install/frozen-sources.list`. `docker-install/debs/Packages`,
`Packages.gz` and `Release` form the local APT repository used on the target.

## Build the partial bundle

From the RADP repository root:

```bash
sudo ./offline/partial/prepare.sh
sudo ./offline/partial/package.sh
```

This path does **not** execute APT and does **not** collect or package any DEBs.
The resulting archive includes `HOST-REQUIREMENTS.txt`, which tells the target
administrator which Docker and Compose versions the project has been using.

The target host must already have Docker, Compose and OpenSSL installed. By
default, the installer expects Docker CLI 25.0.5 and Compose 1.29.2. If the
administrator's verified package collection provides different versions, first
confirm compatibility with the project, then explicitly allow the variance:

```bash
sudo env RADP_ALLOW_HOST_VERSION_VARIANCE=1 ./install.sh
```

The variance flag only bypasses the exact CLI version string check. It does not
bypass checks for a functioning Docker daemon, a working Compose command, the
Astra target version, architecture, bundle checksums, image references or
application startup.

## Install on the air-gapped target

Transfer the ZIP archive and its passphrase separately. Disconnect the target
VM's network adapter before installation. Extract into a new, empty directory,
then run the install script from the extracted bundle root.

Example for the full archive:

```bash
sudo mkdir -p /opt/radp-deploy-full
sudo unzip radp-offline-full.zip -d /opt/radp-deploy-full
cd /opt/radp-deploy-full/radp-offline-full
sudo ./install.sh
```

Example for the partial archive:

```bash
sudo mkdir -p /opt/radp-deploy-partial
sudo unzip radp-offline-partial.zip -d /opt/radp-deploy-partial
cd /opt/radp-deploy-partial/radp-offline-partial
sudo ./install.sh
```

The full installer configures APT for that transaction with one source only: the
local `file:` repository included in the bundle. It disables the normal APT
source-list fragments for that transaction. It does not use the host's configured
network repositories as a fallback. The partial installer does not invoke APT
at all.

Both installers refuse to overwrite an existing `.env`; use a fresh extraction
directory. They do not run `docker-compose down`, remove containers, prune images,
or delete volumes. They load the packaged images, validate Compose configuration,
start services without building images, and check that TCP port 8000 accepts
connections.

## Reproducibility and scope

- Reinstalling the **same ZIP** uses the same archived DEBs and Docker images.
  The full bundle includes a complete package inventory and SHA-256 checksums.
- The dependency closure is resolved from the frozen Astra repositories at
  preparation time. The exact resulting package versions are recorded in the
  inventory; preserve the generated ZIP and inventory as the deployment record.
- Image source tags such as `postgres:17` and `mcuadros/ofelia:latest` are mutable.
  The preparation script records image IDs and repository digests in
  `image-manifest.tsv` and warns when source references are tag-based. For repeatable
  future image builds, rerun preparation with digest-pinned sources, for example:

  ```bash
  sudo env \\
    RADP_POSTGRES_IMAGE_SOURCE='postgres@sha256:<verified-digest>' \\
    RADP_OFELIA_IMAGE_SOURCE='mcuadros/ofelia@sha256:<verified-digest>' \\
    ./offline/partial/prepare.sh
  ```

  Use the actual digests recorded in the image manifest; the placeholders above
  are not literal values. Also pin external `FROM` images in `docker/Dockerfile`
  by digest for repeatable application-image builds.
- The ZIP writer uses stable entry ordering and normalized ZIP timestamps, but
  `.env` encryption uses a fresh random salt and image builds may contain
  nondeterministic metadata. Consequently, separately prepared ZIP files are not
  promised to be byte-for-byte identical. The operational goal is a complete,
  auditable bundle whose contents can be installed without network access.
- These scripts target a clean Astra Linux SE 1.7.8 amd64 system. They do not
  package the operating system itself or its kernel. A clean, disconnected target
  installation and RADP acceptance tests remain required before claiming a
  verified deployment.

## Important safety notes

- `prepare.sh` rebuilds only `release/radp-offline-full` or
  `release/radp-offline-partial` under the repository's `release/` directory.
- The installers refuse an existing `.env`, and they do not delete Docker volumes.
- The full installer refuses to replace a pre-existing Docker/Compose installation
  when its package version differs from the pinned version in the bundle.
- Never treat a successful preparation or ZIP checksum check as proof that the
  target's kernel, storage, networking, secrets or RADP application configuration
  are correct. Validate these on the disconnected target.
