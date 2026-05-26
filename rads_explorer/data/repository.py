from datetime import datetime, timezone

from rads_explorer.data.models import Dataset


class Repository:
    def __init__(self, dataset: Dataset):
        self.ds = dataset

    # =========================================================================
    # CERTIFICATES
    # =========================================================================
    def list_certificates(self):
        return self.ds.certificates

    def get_certificate(self, serial_number: str):
        return next(
            c for c in self.ds.certificates if c.serial_number == serial_number
        )

    # =========================================================================
    # REPORTS
    # =========================================================================
    def expired_certificates(self):
        now = datetime.now(timezone.utc)
        return [c for c in self.ds.certificates if c.not_after < now]

    def expiring_within(self, days: int):
        now = datetime.now(timezone.utc)
        return [
            c
            for c in self.ds.certificates
            if 0 <= (c.not_after - now).days <= days
        ]

    def certificates_by_users(self):
        result = {}
        for c in self.ds.certificates:
            uid = c.user_id
            result.setdefault(uid, []).append(c)
        return result

    # =========================================================================
    # SEARCH
    # =========================================================================
    def search_certificates(self, query: str):
        q = query.lower()

        return [
            c
            for c in self.ds.certificates
            if (
                (c.name_attributes.common_name or "").lower().find(q) >= 0
                or c.serial_number.lower().find(q) >= 0
                or c.thumbprint.lower().find(q) >= 0
            )
        ]

    def search_users(self, query: str):
        q = query.lower()
        return [
            u
            for u in self.ds.users
            if (u.name_attributes.common_name or "").lower().find(q) >= 0
        ]

    # =========================================================================
    # FILTERS
    # =========================================================================
    def certificates_expiring_before(self, days: int):
        from datetime import timedelta

        threshold = datetime.now(timezone.utc) + timedelta(days=days)

        return [c for c in self.ds.certificates if c.not_after <= threshold]

    def certificates_by_user(self, user_id: str):
        return [c for c in self.ds.certificates if c.user_id == user_id]

    # =========================================================================
    # ANALYTICS
    # =========================================================================
    def issuer_distribution(self):
        result = {}
        for c in self.ds.certificates:
            result[c.issuer] = result.get(c.issuer, 0) + 1
        return result
