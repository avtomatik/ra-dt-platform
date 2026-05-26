from rads_explorer.application.services.cert_request_service import \
    CertificateRequestService
from rads_explorer.application.services.certificate_service import \
    CertificateService
from rads_explorer.application.services.user_service import UserService
from rads_explorer.data.export.xlsx import XLSXExporter
from tests.helpers.demo_flow import DemoFlow


def test_demo_flow_runs(client, report_service, detail_cache):
    flow = DemoFlow(
        certificate_service=CertificateService(client, detail_cache),
        cert_request_service=CertificateRequestService(client),
        user_service=UserService(client),
        exporter=XLSXExporter(),
        reports=report_service,
    )

    flow.run()
