from metropolis.extensions import ma


class OverloadedBranchSchema(ma.Schema):
    branchId = ma.Integer(required=True)
    city = ma.String(required=True)
    areaId = ma.Integer(required=True)
    utilizationPercent = ma.Float(required=True)
    needVehicles = ma.Integer(required=True)


class RelocationMoveSchema(ma.Schema):
    fromBranchId = ma.Integer(required=True)
    fromCity = ma.String(required=True)
    toBranchId = ma.Integer(required=True)
    toCity = ma.String(required=True)
    quantity = ma.Integer(required=True)
    transferCost = ma.Float(required=True)
    opportunityCost = ma.Float(required=True)
    totalCost = ma.Float(required=True)


class RelocationSimulationSchema(ma.Schema):
    status = ma.String(metadata={"example": "success"})
    message = ma.String(allow_none=True)
    relocationNeeded = ma.Boolean(required=True)
    overloadedBranches = ma.List(ma.Nested(OverloadedBranchSchema))
    moves = ma.List(ma.Nested(RelocationMoveSchema))
    totalVehiclesMoved = ma.Integer(required=True)
    totalTransferCost = ma.Float(required=True)
    totalOpportunityCost = ma.Float(required=True)
    grandTotalCost = ma.Float(required=True)


class FleetSyncSchema(ma.Schema):
    status = ma.String(required=True)
    created = ma.Integer(required=True)
    existing = ma.Integer(required=True)
