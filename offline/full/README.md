# Full offline bundle

This mode prepares the Docker/Compose package dependency closure from the frozen
Astra Linux SE 1.7.8 repositories and ships those DEBs with the RADP images and
runtime assets. Start with `prepare.sh`, then run `package.sh`. The generated
installer uses only the bundled local APT repository.

Before preparation completes, APT is pointed at the generated `file:` repository
as its **only** package source. It uses a separate empty package-status database
and performs an actual `--download-only --reinstall` install resolution for the
pinned Docker, Compose, OpenSSL and CA-certificate packages. This proves that APT
can resolve the dependency closure and retrieve every selected archive from the
local repository; it does not invoke dpkg or configure packages on the preparation
host. This deliberately replaces `apt-get --simulate`: older APT simulation code
has a documented bug with an empty status database that can report Essential
PAM/Parsec packages as broken even when the package closure is present (Debian
APT bug #973305). The local `Release` date is copied from the frozen repository
metadata.

The FULL installer is intended for a **fresh matching Astra Linux SE 1.7.8
amd64 target**. It installs the pinned host packages from the bundled local APT
repository only; it refuses conflicting/pre-existing Docker installations. Keep
the target network adapter disconnected during installation to verify the
air-gapped procedure.
