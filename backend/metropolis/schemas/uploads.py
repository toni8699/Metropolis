from metropolis.extensions import ma


class UploadPresignRequestSchema(ma.Schema):
    fileName = ma.String(required=True)
    contentType = ma.String(required=True)
    scope = ma.String(required=True, metadata={"example": "OWNER_LISTING"})
    listingId = ma.Integer(required=False, allow_none=True)


class UploadPresignResponseSchema(ma.Schema):
    status = ma.String(required=True)
    presignedUrl = ma.String(required=True)
    objectKey = ma.String(required=True)
    fileUrl = ma.String(required=True)
    expiresIn = ma.Integer(required=True)


class UploadCompleteRequestSchema(ma.Schema):
    objectKey = ma.String(required=True)
    contentType = ma.String(required=False, allow_none=True)
    sizeBytes = ma.Integer(required=False, allow_none=True)
    scope = ma.String(required=True, metadata={"example": "OWNER_LISTING"})
    listingId = ma.Integer(required=False, allow_none=True)


class UploadCompleteResponseSchema(ma.Schema):
    status = ma.String(required=True)
    fileId = ma.Integer(required=True)
    objectKey = ma.String(required=True)
    fileUrl = ma.String(required=True)
