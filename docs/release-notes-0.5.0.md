# RADP 0.5.0 — implementation package (not yet production-verified)

This successor package is based on the production-verified RADP 0.4.0 baseline.
It contains the following additive changes:

- Replaces the singular RA folder setting with the comma-separated
  `RADP_REMOTE_RA__CERTIFICATE_FOLDERS` setting, parsed by Pydantic into a tuple.
- Synchronizes each configured folder independently, deduplicates certificates
  across pages/folders, continues after a folder-level failure, and reports an
  aggregate failure after all folders have been attempted.
- Adds `--certificate-folders` as the one-run CLI override.
- Replaces the OID constants module with the `OID(StrEnum)` catalog while
  retaining the dynamic PostgreSQL OID metadata registry.
- Consolidates reporting mapping into the existing `CertificateProjection`,
  with validated optional column selection and the existing inventory columns
  as the default.
- Adds PostgreSQL-backed `status=ALL|VALID`, exact GID, and UTC `as_of_date`
  report filters shared by preview and XLSX export.
- Adds certificate classification as reporting metadata without altering the
  existing inventory workbook column contract.
- Resolves Microsoft certificate template identifiers to human-readable names
  when corresponding curated OID registry metadata exists. Legacy 0.4.0
  extension representations are also recognized for this lookup.
- Writes Excel datetime columns as native UTC Excel datetime cells with the
  `yyyy-mm-dd hh:mm:ss` number format.
- Adds Administrator and Operator operational documentation and records the
  authentication/authorization prerequisite before wider user exposure.

No PostgreSQL table or column migration is introduced by this package. New
extension JSON fields are optional and default to `None`, preserving validation
of existing JSONB certificate payloads.

## Verification status

The test suite passed in the implementation environment. The locked dependency
installation and the offline bundle build were not executed in the isolated
inspection environment. Run the project tests and the FULL/PARTIAL package
builders in the approved build environment before promotion. Treat 0.5.0 as a
candidate package until that verification and production acceptance are complete.

## Operational/security notes

- The RA's actual folder-membership semantics remain unverified. RADP stores one
  certificate record per certificate ID and does not add a folder-membership
  table in this release.
- Human-readable template names require a meaningful `name` or `description`
  for the template OID in the existing OID registry. Unknown names are left
  blank; RADP does not invent labels or display raw template OIDs in the report.
- API routes still have no application-level authentication or authorization.
  Follow `docs/security/access-control-before-user-exposure.md` before exposing
  the new UI to Operators beyond the approved restricted boundary.
