from metropolis.extensions import ma


class ReservationQuerySchema(ma.Schema):
    email = ma.String(
        required=True,
        metadata={
            "description": "Customer email address",
            "example": "mike.mccarthy@example.com",
        },
    )


class ReservationSchema(ma.Schema):
    resId = ma.Integer(required=True)
    bookedAt = ma.String(allow_none=True)
    pickupDate = ma.String(allow_none=True)
    returnDate = ma.String(allow_none=True)
    contractId = ma.Integer(allow_none=True)
    planType = ma.String(allow_none=True)
    totalCost = ma.Float(allow_none=True)
    employeeName = ma.String(allow_none=True)
    vehicleClassName = ma.String(allow_none=True)
    make = ma.String(allow_none=True)
    model = ma.String(allow_none=True)
    branchId = ma.Integer(allow_none=True)
    city = ma.String(allow_none=True)
    areaName = ma.String(allow_none=True)


class ReservationLookupResponseSchema(ma.Schema):
    status = ma.String(metadata={"example": "success"})
    message = ma.String(allow_none=True)
    reservations = ma.List(ma.Nested(ReservationSchema))
