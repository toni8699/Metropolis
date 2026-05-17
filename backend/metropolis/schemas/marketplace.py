from metropolis.extensions import ma


class ListingCreateSchema(ma.Schema):
    title = ma.String(required=True)
    brand = ma.String(required=False, allow_none=True)
    make = ma.String(required=False, allow_none=True)
    model = ma.String(required=False, allow_none=True)
    year = ma.Integer(required=False, allow_none=True)
    description = ma.String(required=False, allow_none=True)
    rules = ma.String(required=False, allow_none=True)
    pickupNotesTemplate = ma.String(required=False, allow_none=True)
    pricePerDay = ma.Float(required=True)
    photos = ma.List(ma.String(), required=False)
    lat = ma.Float(required=True)
    lng = ma.Float(required=True)
    cityZone = ma.String(required=True)


class ListingUpdateSchema(ma.Schema):
    title = ma.String(required=False)
    brand = ma.String(required=False, allow_none=True)
    make = ma.String(required=False, allow_none=True)
    model = ma.String(required=False, allow_none=True)
    year = ma.Integer(required=False, allow_none=True)
    description = ma.String(required=False, allow_none=True)
    rules = ma.String(required=False, allow_none=True)
    pickupNotesTemplate = ma.String(required=False, allow_none=True)
    pricePerDay = ma.Float(required=False)
    photos = ma.List(ma.String(), required=False)
    active = ma.Boolean(required=False)


class ListingLocationSchema(ma.Schema):
    lat = ma.Float(required=True)
    lng = ma.Float(required=True)
    cityZone = ma.String(required=True)


class ListingAvailabilitySchema(ma.Schema):
    startAt = ma.DateTime(required=True)
    endAt = ma.DateTime(required=True)
    status = ma.String(required=False, metadata={"example": "AVAILABLE"})


class ListingSearchSchema(ma.Schema):
    bbox = ma.String(
        required=False,
        metadata={"description": "minLng,minLat,maxLng,maxLat", "example": "-73.75,45.45,-73.50,45.62"},
    )
    start = ma.DateTime(required=False)
    end = ma.DateTime(required=False)
    cityZone = ma.String(required=False)


class ListingSchema(ma.Schema):
    listingId = ma.Integer(required=True)
    sourceType = ma.String(required=True)
    title = ma.String(required=True)
    brand = ma.String(allow_none=True)
    make = ma.String(allow_none=True)
    model = ma.String(allow_none=True)
    year = ma.Integer(allow_none=True)
    description = ma.String(allow_none=True)
    rules = ma.String(allow_none=True)
    pickupNotesTemplate = ma.String(allow_none=True)
    pricePerDay = ma.Float(required=True)
    photos = ma.List(ma.String(), required=True)
    active = ma.Boolean(required=True)
    ownerUserId = ma.Integer(allow_none=True)
    ownerName = ma.String(allow_none=True)
    fleetVehicleVin = ma.String(allow_none=True)
    lat = ma.Float(allow_none=True)
    lng = ma.Float(allow_none=True)
    cityZone = ma.String(allow_none=True)
    geohash = ma.String(allow_none=True)
    createdAt = ma.String(required=True)
    updatedAt = ma.String(required=True)


class ListingCollectionSchema(ma.Schema):
    status = ma.String(required=True)
    listings = ma.List(ma.Nested(ListingSchema))


class ListingItemSchema(ma.Schema):
    status = ma.String(required=True)
    listing = ma.Nested(ListingSchema)
