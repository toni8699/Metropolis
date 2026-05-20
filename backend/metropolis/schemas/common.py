from metropolis.extensions import ma


class HealthSchema(ma.Schema):
    status = ma.String(metadata={"example": "ok"})


class ErrorSchema(ma.Schema):
    status = ma.String(metadata={"example": "error"})
    message = ma.String()
    error = ma.String(required=False)


class StatusSchema(ma.Schema):
    status = ma.String(required=True)
