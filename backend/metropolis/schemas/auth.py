from metropolis.extensions import ma


class AuthRegisterSchema(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True)
    fullName = ma.String(required=False, allow_none=True)
    role = ma.String(required=False, metadata={"example": "RENTER"})


class AuthLoginSchema(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True)


class UserSummarySchema(ma.Schema):
    userId = ma.Integer(required=True)
    email = ma.Email(required=True)
    role = ma.String(required=True)
    fullName = ma.String(allow_none=True)


class AuthTokenSchema(ma.Schema):
    status = ma.String(required=True)
    token = ma.String(required=True)
    user = ma.Nested(UserSummarySchema)


class MeUserSchema(UserSummarySchema):
    phone = ma.String(allow_none=True)
    createdAt = ma.String(allow_none=True)


class MeSchema(ma.Schema):
    status = ma.String(required=True)
    user = ma.Nested(MeUserSchema)
