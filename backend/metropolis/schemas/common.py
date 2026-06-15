from metropolis.extensions import ma


class HealthSchema(ma.Schema):
    status = ma.String(metadata={"example": "ok"})


class ErrorSchema(ma.Schema):
    status = ma.String(metadata={"example": "error"})
    message = ma.String()
    error = ma.String(required=False)


class StatusSchema(ma.Schema):
    status = ma.String(required=True)


class LinkSchema(ma.Schema):
    href = ma.String(required=True)
    method = ma.String(required=True)


class ListingLocationSchema(ma.Schema):
    """Location on booking/listing API responses (fields optional)."""

    lat = ma.Float(allow_none=True)
    lng = ma.Float(allow_none=True)
    cityZone = ma.String(allow_none=True)
    pickupAddress = ma.String(allow_none=True)
    address = ma.String(allow_none=True)
    geohash = ma.String(allow_none=True)


class ListingLocationWriteSchema(ma.Schema):
    """POST /api/listings/:id/location request body."""

    lat = ma.Float(required=True)
    lng = ma.Float(required=True)
    cityZone = ma.String(required=True)
    pickupAddress = ma.String(required=False, allow_none=True)
