from metropolis.extensions import ma


class ReviewSubmitSchema(ma.Schema):
    targetType = ma.String(required=True, metadata={"example": "LISTING"})
    rating = ma.Integer(required=True, metadata={"example": 5})
    cleanliness = ma.Integer(required=False, allow_none=True, metadata={"example": 5})
    accuracy = ma.Integer(required=False, allow_none=True, metadata={"example": 5})
    communication = ma.Integer(required=False, allow_none=True, metadata={"example": 5})
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
    cleanliness = ma.Integer(allow_none=True)
    accuracy = ma.Integer(allow_none=True)
    communication = ma.Integer(allow_none=True)
    comment = ma.String(allow_none=True)
    createdAt = ma.String(required=True)


class ReviewItemSchema(ma.Schema):
    status = ma.String(required=True)
    review = ma.Nested(ReviewSchema)


class ReviewCollectionSchema(ma.Schema):
    status = ma.String(required=True)
    reviews = ma.List(ma.Nested(ReviewSchema))
