from marshmallow import RAISE

from metropolis.extensions import ma


class AuthRegisterSchema(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True)
    fullName = ma.String(required=False, allow_none=True)
    role = ma.String(required=False, metadata={"example": "user"})


class AuthLoginSchema(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True)


class AuthGoogleSchema(ma.Schema):
    idToken = ma.String(required=True)


class UserSummarySchema(ma.Schema):
    userId = ma.Integer(required=True)
    email = ma.Email(required=True)
    fullName = ma.String(allow_none=True)
    role = ma.String(required=True)
    isAdmin = ma.Boolean(required=True)
    hasListings = ma.Boolean(required=True)


class AuthTokenSchema(ma.Schema):
    status = ma.String(required=True)
    token = ma.String(required=True)
    user = ma.Nested(UserSummarySchema)


class MeUserSchema(UserSummarySchema):
    phone = ma.String(allow_none=True)
    profilePhotoUrl = ma.String(allow_none=True)
    createdAt = ma.String(allow_none=True)
    joinedLabel = ma.String(allow_none=True)
    lives = ma.String(allow_none=True)
    about = ma.String(allow_none=True)
    languages = ma.String(allow_none=True)
    work = ma.String(allow_none=True)
    isApprovedToDrive = ma.Boolean(required=True)
    hasEmail = ma.Boolean(required=True)
    hasPhone = ma.Boolean(required=True)
    tripsCount = ma.Integer(required=True)
    averageRating = ma.Float(allow_none=True)


class MeSchema(ma.Schema):
    status = ma.String(required=True)
    user = ma.Nested(MeUserSchema)


class MeUpdateSchema(ma.Schema):
    class Meta:
        unknown = RAISE

    fullName = ma.String(required=False, allow_none=True)
    phone = ma.String(required=False, allow_none=True)
    profilePhotoUrl = ma.String(required=False, allow_none=True)
    lives = ma.String(required=False, allow_none=True)
    about = ma.String(required=False, allow_none=True)
    languages = ma.String(required=False, allow_none=True)
    work = ma.String(required=False, allow_none=True)
