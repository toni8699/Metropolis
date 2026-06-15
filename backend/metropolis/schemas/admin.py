from metropolis.extensions import ma


class FleetSyncSchema(ma.Schema):
    status = ma.String(required=True)
    created = ma.Integer(required=True)
    existing = ma.Integer(required=True)


class AdminBookingsSchema(ma.Schema):
    status = ma.String(required=True)
    bookings = ma.List(ma.Raw(), required=True)


class AdminListingsSchema(ma.Schema):
    status = ma.String(required=True)
    listings = ma.List(ma.Raw(), required=True)


class AdminUsersSchema(ma.Schema):
    status = ma.String(required=True)
    users = ma.List(ma.Raw(), required=True)


class AdminCompanyLocationsSchema(ma.Schema):
    status = ma.String(required=True)
    areas = ma.List(ma.Raw(), required=True)
    branches = ma.List(ma.Raw(), required=True)
    parkingSpots = ma.List(ma.Raw(), required=True)
    vehicleClasses = ma.List(ma.Raw(), required=True)


class AdminAnalyticsSchema(ma.Schema):
    status = ma.String(required=True)
    analytics = ma.Raw(required=True)


class AdminKycQueueSchema(ma.Schema):
    status = ma.String(required=True)
    queue = ma.List(ma.Raw(), required=True)


class AdminKycUpdateSchema(ma.Schema):
    status = ma.String(required=True)
    userId = ma.Integer(required=True)
    verificationStatus = ma.String(required=True)


class AnalyticsScopeSchema(ma.Schema):
    scope = ma.String(
        required=True,
        metadata={"description": "owner (host) or fleet (admin)."},
    )


class KycQueueQuerySchema(ma.Schema):
    status = ma.String(required=False, metadata={"description": "pending (default)."})
