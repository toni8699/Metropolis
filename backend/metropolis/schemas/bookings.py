from metropolis.extensions import ma


class BookingCreateSchema(ma.Schema):
    listingId = ma.Integer(required=True)
    startAt = ma.DateTime(required=True)
    endAt = ma.DateTime(required=True)


class BookingInstructionCreateSchema(ma.Schema):
    message = ma.String(required=True)


class BookingStatusTransitionSchema(ma.Schema):
    status = ma.String(required=False)


class BookingInstructionSchema(ma.Schema):
    instructionId = ma.Integer(required=True)
    ownerUserId = ma.Integer(required=True)
    message = ma.String(required=True)
    sentAt = ma.String(required=True)
    readAt = ma.String(allow_none=True)


class BookingSchema(ma.Schema):
    bookingId = ma.Integer(required=True)
    listingId = ma.Integer(required=True)
    listingTitle = ma.String(allow_none=True)
    sourceType = ma.String(required=True)
    ownerUserId = ma.Integer(allow_none=True)
    renterUserId = ma.Integer(required=True)
    startAt = ma.String(required=True)
    endAt = ma.String(required=True)
    status = ma.String(required=True)
    priceSnapshot = ma.Raw(required=True)
    createdAt = ma.String(required=True)
    updatedAt = ma.String(required=True)
    instructions = ma.List(ma.Nested(BookingInstructionSchema))


class BookingItemSchema(ma.Schema):
    status = ma.String(required=True)
    booking = ma.Nested(BookingSchema)
