from metropolis.extensions import ma


class ReviewSubmitSchema(ma.Schema):
    targetType = ma.String(required=True, metadata={"example": "LISTING"})
    rating = ma.Integer(required=True, metadata={"example": 5})
    comment = ma.String(required=False, allow_none=True)


class ReviewSchema(ma.Schema):
    reviewId = ma.Integer(required=True)
    bookingId = ma.Integer(required=True)
    authorUserId = ma.Integer(required=True)
    authorName = ma.String(allow_none=True)
    targetType = ma.String(required=True)
    targetUserId = ma.Integer(allow_none=True)
    targetListingId = ma.Integer(allow_none=True)
    rating = ma.Integer(required=True)
    comment = ma.String(allow_none=True)
    createdAt = ma.String(required=True)


class ReviewItemSchema(ma.Schema):
    status = ma.String(required=True)
    review = ma.Nested(ReviewSchema)


class ReviewCollectionSchema(ma.Schema):
    status = ma.String(required=True)
    reviews = ma.List(ma.Nested(ReviewSchema))
