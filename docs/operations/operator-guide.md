# RADP Operator Guide

This guide is for users who have been granted access to the RADP web interface.
It does not require shell access, Docker knowledge, database credentials, or
access to the Administrator environment.

## 1. Open RADP

Open the RADP address supplied by the system administrator. The landing page
presents the available certificate operations.

## 2. Available actions

- **Перечень сертификатов** opens `/web` and displays the first records from the
  local certificate database.
- **Предварительный просмотр** opens `/export/preview` and displays the first
  records matching the selected report filters.
- **Все сертификаты** downloads an Excel workbook containing all certificate
  lifecycle states.
- **Действительные сертификаты** downloads an Excel workbook containing
  certificates whose lifecycle state is `VALID` and whose `not_after` timestamp
  has not passed the UTC date cutoff.

Excel datetime columns contain native Excel date/time values in UTC and display
as `yyyy-mm-dd hh:mm:ss`.

## 3. Optional report filters

The report endpoints accept URL parameters:

- `status=ALL` or `status=VALID`.
- `gid=<exact-value>` to select one GID.
- `as_of_date=YYYY-MM-DD` to set the inclusive UTC validity cutoff for the
  `VALID` report.

Example:

```text
/export/certificates?status=VALID&gid=example-gid&as_of_date=2026-11-17
```

Only use filters supplied by the administrator or specified by the business
process.

## 4. When data looks outdated or an operation fails

RADP operates against its local database. The Administrator environment may not
be available during ordinary user operations. If recently issued, changed, or
revoked certificates are not visible, note the time and contact the system
administrator; do not attempt to connect to the Administrator machine yourself.

For an export failure, record the page URL and approximate time, then contact
the system administrator. Users must not restart services or alter application
configuration unless separately authorized.
