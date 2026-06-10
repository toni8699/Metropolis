from metropolis.extensions import ma


class PaymentIntentResponseSchema(ma.Schema):
    bookingId = ma.Integer(required=True)
    clientSecret = ma.String(allow_none=True)
    mock = ma.Boolean()
    alreadyPaid = ma.Boolean()
