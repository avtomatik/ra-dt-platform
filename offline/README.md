# RADP offline bundle scripts

These scripts are intended to be copied to the repository's `offline/` directory. Run them **inside a connected Astra Linux 1.7 x86-64 VM**, using the same Astra update level as the eventual target.

## Important baseline requirement

`prepare.sh` intentionally refuses to run if Docker or Compose is already installed. APT omits packages that it believes are already installed; gathering a complete dependency set therefore needs a clean matching Astra baseline. Use a fresh clone/snapshot of the target Astra VM with internet access, then run the preparation script there. The script collects `.deb` files before installing Docker for the build.

The default expected APT packages are `docker.io` and `docker-compose-v2`. The script reports APT candidates and verifies that the installed `docker-compose` command is Compose v2 and supports `--pull` and `--no-build`. If Astra's repositories name the v2 package differently, rerun with an explicit override only after verifying the package really provides that CLI, for example `sudo env COMPOSE_PACKAGE=some-package ./offline/prepare.sh`.

## Build and package

From the repository root on the connected Astra VM:

```bash
sudo ./offline/prepare.sh
sudo ./offline/package.sh
```

During preparation, enter a strong passphrase twice to encrypt `.env`. The ZIP contains `.env.enc`, not plaintext `.env`; you will need the same passphrase during installation. The build context is staged without `.env` to avoid copying secrets into the RADP image.

Expected completion messages are `PREPARATION SUCCESS` and `PACKAGE SUCCESS`. Neither means that offline portability has been proven.

## Mandatory clean offline test

1. Create a clean VM from the same Astra 1.7 update-level baseline. Do not install Docker manually.
2. Disconnect/disable the VM's virtual network adapter in the hypervisor. Do not merely assume the guest has no internet.
3. Transfer and extract `radp-offline.zip` into a directory.
4. Run `sudo ./install.sh` from the extracted `radp-offline/` directory and enter the `.env` encryption passphrase.
5. Accept the bundle as offline-tested only if the script prints `DEPLOYMENT SUCCESS` and the VM's virtual NIC was disconnected for the entire installation.

The install script does not run `apt-get update`, does not download packages, does not pull images, and does not build images. It checks `SHA256SUMS`, Astra/base-package fingerprints, local package installation, image architecture/tags, Compose config, container startup, database readiness, successful `db-init`, and TCP readiness on port 9000.

The installer is for a fresh deployment. Do not use it as a database migration or destructive reset mechanism. Existing Docker volumes are not deleted.
