# Full offline bundle

This mode prepares the Docker/Compose package dependency closure from the frozen
Astra Linux SE 1.7.8 repositories and ships those DEBs with the RADP images and
runtime assets. Start with `prepare.sh`, then run `package.sh`. The generated
installer uses only the bundled local APT repository.
