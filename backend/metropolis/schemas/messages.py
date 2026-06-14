from metropolis.extensions import ma


class BookingMessageSchema(ma.Schema):
    messageId = ma.Integer(required=True)
    bookingId = ma.Integer(required=True)
    senderId = ma.Integer(required=True)
    senderName = ma.String(allow_none=True)
    messageText = ma.String(required=True)
    createdAt = ma.String(required=True)


class BookingMessageCreateSchema(ma.Schema):
    messageText = ma.String(required=True)


class BookingMessageItemSchema(ma.Schema):
    message = ma.Nested(BookingMessageSchema, required=True)


class BookingMessageCollectionSchema(ma.Schema):
    messages = ma.List(ma.Nested(BookingMessageSchema), required=True)


class ThreadParticipantSchema(ma.Schema):
    userId = ma.Integer(required=True)
    name = ma.String(allow_none=True)
    email = ma.String(allow_none=True)


class ThreadLatestMessageSchema(ma.Schema):
    messageText = ma.String(required=True)
    createdAt = ma.String(required=True)


class ThreadListingSchema(ma.Schema):
    listingId = ma.Integer(required=True)
    title = ma.String(allow_none=True)
    pricePerDay = ma.Float(required=True)
    coverPhoto = ma.String(allow_none=True)


class ThreadPricingSchema(ma.Schema):
    pricePerDay = ma.Float(required=True)
    dayCount = ma.Integer(allow_none=True)
    total = ma.Float(required=True)
    currency = ma.String(required=True)


class MessageThreadSchema(ma.Schema):
    bookingId = ma.Integer(required=True)
    listingId = ma.Integer(required=True)
    status = ma.String(required=True)
    startAt = ma.String(required=True)
    endAt = ma.String(required=True)
    cityZone = ma.String(allow_none=True)
    userRole = ma.String(required=True)
    renterUserId = ma.Integer(required=True)
    ownerUserId = ma.Integer(required=True)
    otherParty = ma.Nested(ThreadParticipantSchema, required=True)
    listing = ma.Nested(ThreadListingSchema, required=True)
    pricing = ma.Nested(ThreadPricingSchema, required=True)
    latestMessage = ma.Nested(ThreadLatestMessageSchema, allow_none=True)
    unreadCount = ma.Integer(required=True)


class MessageThreadCollectionSchema(ma.Schema):
    threads = ma.List(ma.Nested(MessageThreadSchema), required=True)
