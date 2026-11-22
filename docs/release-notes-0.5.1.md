# RADP 0.5.1 — focused reporting and web-interface follow-up

This implementation candidate is based on the user-supplied RADP 0.5.0
source archive. It does not replace the production-verified 0.4.0 baseline and
has not been verified on the Astra Linux production target.

## Changes

- Reworks the landing page and certificate preview as shared Jinja2 templates
  with a common base layout and external responsive CSS.
- Uses FastAPI's `Jinja2Templates` integration and mounts the static asset
  directory at `/static`; template autoescaping remains enabled.
- Keeps the deployment-friendly top-level `html/` asset directory, which is
  already copied into the Docker image and offline deployment bundles.
- Adds Microsoft V1 certificate-template name decoding for the
  `1.3.6.1.4.1.311.20.2` extension. The standards-defined
  `SEQUENCE { UTF8String }` encoding and a deployed bare `BMPString` form are
  supported.
- Prefers the V1 human-readable name when both V1 and V2 template extensions
  exist. V2 remains supported through the template-OID metadata lookup.
- Adds compatibility decoding for historical repr-like V1 extension values
  already persisted in certificate JSONB payloads.
- Adds the V1 extension OID to the seed registry and documents how to curate
  CA-specific V2 template names.
- Corrects the README's one-run CLI option to `--certificate-folders`.

## Certificate-template name limitation

A V2 template extension contains a template OID and optional version numbers,
not the friendly template name. The OID is specific to the issuing CA's
template catalogue. Therefore, a V2-only certificate still requires an
authoritative name mapping in the RADP OID registry. Unknown names remain blank
rather than displaying an OID as a human-readable label. See
`docs/operations/certificate-template-names.md`.

## Compatibility and migrations

No PostgreSQL schema migration or new runtime dependency is introduced. The new
`Extension.template_oid` and `Extension.template_name` fields remain optional,
and the projection supports the previously persisted extension representation.

## Verification

Verified in the implementation environment:

- Python test suite: 81 passed.
- Python compilation: passed.
- `uv lock --check --offline`: passed.
- Offline FULL and PARTIAL package-builder tests: passed.
- Static CSS route and Jinja2 escaping: covered by API tests.
- V1 DER decoding and legacy stored-value decoding: covered by unit tests.

Not verified in this environment:

- Live certificate samples from the target Registry Authority.
- Live PostgreSQL/RA integration.
- Installation and operation on Astra Linux SE 1.7.8.
- Production deployment and user acceptance.

## Security note

Application-level authentication and authorization are still not implemented.
Keep the web interface restricted according to the existing access-control
prerequisite document until the offline identity and authorization model is
implemented and tested.
