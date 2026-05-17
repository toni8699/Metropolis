from metropolis.extensions import ma


class AreaAvailabilitySchema(ma.Schema):
    areaName = ma.String(required=True)
    availableCount = ma.Integer(required=True)
