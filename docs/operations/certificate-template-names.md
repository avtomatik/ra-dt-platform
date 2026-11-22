# Certificate-template name resolution

RADP supports the two Microsoft certificate-template extension versions:

- **V1 — `1.3.6.1.4.1.311.20.2`:** carries the human-readable template name.
  Microsoft specifies a DER `SEQUENCE` containing a `UTF8String`. RADP also
  accepts the bare `BMPString` form encountered in deployed certificates.
- **V2 — `1.3.6.1.4.1.311.21.7`:** carries a template OID and optional version
  numbers. The OID identifies the issuing CA's template; it is not itself a
  human-readable template name.

When both extensions exist, RADP prefers the V1 name. For V2-only certificates,
RADP resolves the template OID through the local OID registry. Unknown names
remain blank; the report never substitutes a raw OID for a friendly name.

## Curating a V2 template name

The actual template identifiers are specific to the issuing CA's template
catalogue. Obtain the authoritative display names from the CA administrator.
Then, with the RADP environment configured and the database available:

1. Export the current registry to its seed file:

   ```bash
   uv run python -m radp oid export
   ```

2. Edit `data/seed/oid_registry.json`. Find the entry whose `oid` equals the
   V2 `templateID` and populate its `name` with the authoritative friendly
   template name (or its `description` if that is the agreed convention). Do not
   change the built-in extension OID entry; the entry to enrich is the template
   identifier contained inside the V2 extension.

3. Merge the enriched metadata into the database:

   ```bash
   uv run python -m radp oid sync
   ```

The registry synchronizer fills missing metadata without overwriting values
already curated in the database. Existing certificate payloads do not need to
be fetched again for this V2 lookup to take effect.

## Existing stored certificates

Older certificate payloads may not contain the dedicated `template_oid` and
`template_name` fields. RADP retains compatibility fallbacks for the previous
serialized V2 extension and can decode the historical repr-like representation
of a V1 `UnrecognizedExtension`. These fallbacks allow report generation to
benefit from the new mapping without forcing a certificate refresh, provided
the original extension value remains in the stored payload.

## Operational validation

After curating the registry, generate a report and verify representative
certificates from each issuing CA and template family. Include V1-only, V2-only,
and certificates carrying both extensions. The unit tests exercise the DER
parser with synthetic encodings; a real-certificate check is still required to
confirm the exact encodings issued in the target environment.
