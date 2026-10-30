# Partial offline bundle

This mode ships RADP runtime assets and images but intentionally ships no DEBs.
The target administrator must first install Docker, Compose and OpenSSL from the
host's approved package collection. Start with `prepare.sh`, then run
`package.sh`; `HOST-REQUIREMENTS.txt` documents the expected host tools.
