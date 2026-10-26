# RADP offline deployment workflow

## Scope

This workflow targets **Astra Linux SE 1.7.8, amd64/x86_64**, Docker Engine
`25.0.5.astra3+ci24`, and `docker-compose` v1.29.2. It packages images named
by the actual `docker-compose.yml`, plus an encrypted `.env`, into one ZIP.

It is not certified portable until the ZIP installs and starts successfully on
a clean matching VM while its virtual network adapter is disconnected.

## Run on the connected Astra 1.7.8 preparation VM

From the repository root:

```bash
chmod +x offline/prepare.sh offline/package.sh offline/install.sh
sudo ./offline/prepare.sh
sudo ./offline/package.sh
```

Output: `release/radp-offline.zip`. Keep generated ZIPs, `.deb` files, image
archives, and secrets out of Git. Commit the scripts, README, and `.dockerignore`.

Preparation uses frozen Astra 1.7.8 base/update repositories. It downloads a
conservative dependency closure with `apt-rdepends`; this can include extra
alternatives. It then installs the pinned Docker/Compose versions on the
preparation VM, builds RADP, pulls PostgreSQL 17 and Ofelia, and tags them to
match the image references in Compose. If the actual Compose references contain
another image, the script stops rather than guessing where to obtain it.

The `.env` is encrypted with OpenSSL AES-256-CBC + PBKDF2 (250,000 iterations).
Keep the passphrase out of Git and transfer it separately to the authorized
installer. The plaintext `.env` is never written into the ZIP.

## Required acceptance test

1. Create a clean VM matching the production Astra 1.7.8 update/base package
   baseline. Do not use a VM with pre-installed Docker/Compose for the acceptance
   test.
2. Disconnect its virtual NIC before installing.
3. Transfer and extract the ZIP into a new directory.
4. Run `sudo ./install.sh` from that directory and enter the encryption passphrase.
5. Confirm the installer prints `DEPLOYMENT SUCCESS`.
6. If this succeeds with networking disconnected, record `OFFLINE TEST SUCCESS`
   in the release/change record. Do not claim offline portability before then.

The installer uses `apt-get --no-download`; it cannot fetch missing OS packages.
If that step fails on the clean target, the dependency archive is incomplete or
the target base differs. Capture the missing package names and update the
preparation workflow, then rebuild and retest.

## Safety notes

- Fresh deployment only. The installer refuses to overwrite an existing `.env`.
- It does not remove Docker volumes or delete existing containers/volumes.
- Do not run this installer against an existing production deployment without a
  separate backup/rollback plan.
- PostgreSQL should remain internal to the Compose network; verify the actual
  Compose file does not publish port 5432.
- Compose v1.29.2 does not support `--pull never`; the installer instead checks
  the complete image manifest is loaded locally and invokes `docker-compose up
  -d --no-build`. The disconnected-network acceptance test is the proof that
  no network access is required.
