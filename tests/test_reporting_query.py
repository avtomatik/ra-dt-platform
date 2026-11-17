from datetime import date

from sqlalchemy.dialects import postgresql

from radp.application.reporting.enums import CertificateReportStatus
from radp.application.reporting.models import CertificateReportFilters
from radp.infrastructure.persistence.repositories.certificate_query import \
    CertificateQueryRepository


def compile_report_query(filters):
    repository = CertificateQueryRepository(engine=None)
    captured = []
    repository._list = lambda statement: captured.append(statement) or []
    repository.list_for_report(filters)
    return captured[0].compile(dialect=postgresql.dialect())


def test_all_status_filter_does_not_restrict_lifecycle_state():
    compiled = compile_report_query(
        CertificateReportFilters(status=CertificateReportStatus.ALL)
    )
    sql = str(compiled)
    assert '"certificates"."status"' not in sql.split("WHERE")[-1]


def test_valid_filter_is_applied_in_postgresql_with_utc_date_cutoff():
    compiled = compile_report_query(
        CertificateReportFilters(
            status=CertificateReportStatus.VALID, as_of_date=date(2026, 11, 17)
        )
    )
    sql = str(compiled)
    assert "certificates.status =" in sql
    assert "CAST" in sql.upper()
    assert "VALID" in compiled.params.values()
    assert any(
        "2026-11-17" in str(value) for value in compiled.params.values()
    )


def test_gid_filter_uses_jsonb_containment_in_postgresql():
    compiled = compile_report_query(CertificateReportFilters(gid="gid-123"))
    sql = str(compiled)
    assert "@>" in sql
    assert any("gid-123" in str(value) for value in compiled.params.values())
