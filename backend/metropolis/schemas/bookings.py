from metropolis.extensions import ma
from metropolis.schemas.common import LinkSchema


class BookingCreateSchema(ma.Schema):
    listingId = ma.Integer(required=True)
    startAt = ma.DateTime(required=True)
    endAt = ma.DateTime(required=True)


class BookingPatchSchema(ma.Schema):
    status = ma.String(
        required=False,
        metadata={
            "description": "CONFIRMED, CANCELLED, IN_PROGRESS, or COMPLETED.",
        },
    )
class BookingListSchema(ma.Schema):
    scope = ma.String(
        required=True,
        metadata={
            "description": "mine (renter), owner (host), or fleet (admin).",
        },
    )


class ListingLocationSchema(ma.Schema):
    lat = ma.Float(allow_none=True)
    lng = ma.Float(allow_none=True)
    cityZone = ma.String(allow_none=True)
    address = ma.String(allow_none=True)
    geohash = ma.String(allow_none=True)


class HostProfileSchema(ma.Schema):
    userId = ma.Integer(allow_none=True)
    name = ma.String(allow_none=True)
    email = ma.String(allow_none=True)
    verified = ma.Boolean(required=True)


class RenterProfileSchema(ma.Schema):
    userId = ma.Integer(allow_none=True)
    name = ma.String(allow_none=True)
    email = ma.String(allow_none=True)


class HostEarningsSchema(ma.Schema):
    pricePerDay = ma.Float(required=True)
    dayCount = ma.Integer(required=True)
    subtotal = ma.Float(required=True)
    cleaningFee = ma.Float(required=True)
    grossPayout = ma.Float(required=True)
    currency = ma.String(required=True)


class PriceBreakdownSchema(ma.Schema):
    pricePerDay = ma.Float(required=True)
    dayCount = ma.Integer(required=True)
    subtotal = ma.Float(required=True)
    serviceFee = ma.Float(required=True)
    cleaningFee = ma.Float(required=True)
    securityDeposit = ma.Float(required=True)
    total = ma.Float(required=True)
    currency = ma.String(required=True)


class TripEventSchema(ma.Schema):
    eventId = ma.Integer(required=True)
    eventType = ma.String(required=True)
    actorUserId = ma.Integer(allow_none=True)
    eventAt = ma.String(required=True)
    metadata = ma.Raw(required=True)


class BookingSchema(ma.Schema):
    bookingId = ma.Integer(required=True)
    listingId = ma.Integer(required=True)
    listingTitle = ma.String(allow_none=True)
    sourceType = ma.String(required=True)
    ownerUserId = ma.Integer(allow_none=True)
    renterUserId = ma.Integer(required=True)
    renterEmail = ma.String(allow_none=True)
    cityZone = ma.String(allow_none=True)
    startAt = ma.String(required=True)
    endAt = ma.String(required=True)
    status = ma.String(required=True)
    priceSnapshot = ma.Raw(required=True)
    createdAt = ma.String(required=True)
    updatedAt = ma.String(required=True)
    needsReview = ma.Boolean(required=True)
    listingPhoto = ma.String(allow_none=True)
    pickupNotes = ma.String(allow_none=True)
    listingLocation = ma.Nested(ListingLocationSchema, allow_none=True)
    host = ma.Nested(HostProfileSchema, allow_none=True)
    renter = ma.Nested(RenterProfileSchema, allow_none=True)
    userRole = ma.String(allow_none=True)
    pricing = ma.Nested(PriceBreakdownSchema, allow_none=True)
    earnings = ma.Nested(HostEarningsSchema, allow_none=True)
    tripEvents = ma.List(ma.Nested(TripEventSchema), allow_none=True)
    canCancel = ma.Boolean(allow_none=True)
    canConfirmPickup = ma.Boolean(allow_none=True)
    canCompleteTrip = ma.Boolean(allow_none=True)
    canApprove = ma.Boolean(allow_none=True)
    canReject = ma.Boolean(allow_none=True)
    _links = ma.Dict(keys=ma.String(), values=ma.Nested(LinkSchema), required=False)


class BookingCollectionSchema(ma.Schema):
    status = ma.String(required=True)
    scope = ma.String(required=False)
    bookings = ma.List(ma.Nested(BookingSchema))
    _links = ma.Dict(keys=ma.String(), values=ma.Nested(LinkSchema), required=False)


class BookingItemSchema(ma.Schema):
    status = ma.String(required=True)
    booking = ma.Nested(BookingSchema)
    _links = ma.Dict(keys=ma.String(), values=ma.Nested(LinkSchema), required=False)
