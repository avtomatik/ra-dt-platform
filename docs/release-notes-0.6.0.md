# RADP 0.6.0 — TOML folder configuration and reporting stabilization

- **Breaking:** certificate folder names now come exclusively from `config/certificate-folders.toml`. Remove the old `RADP_REMOTE_RA__CERTIFICATE_FOLDERS` environment variable and the `--certificate-folders` CLI override. The optional `RADP_REMOTE_RA__CERTIFICATE_FOLDERS_FILE` chooses an alternate path, not folder values.
- The TOML default path is independent of the process working directory, and both `db-init` and `platform` mount it read-only in Docker Compose.
- Curated V2 template labels are refreshed for each report or preview, without losing the old stored-certificate fallbacks.
- Malformed X.509 extensions generate a warning instead of silently suppressing all metadata.
- Removed two unreferenced helpers; no API, database schema or reporting-column changes.

The companion engineering review is not bundled with this source archive; see the project tests and release notes for implemented behavior. The supplied `cert-report` archive was encrypted; its code was not available for a grounded comparison.
