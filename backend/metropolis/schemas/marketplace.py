from marshmallow import EXCLUDE, pre_load

from metropolis.extensions import ma
from metropolis.schemas.common import LinkSchema, ListingLocationWriteSchema


class ListingCreateSchema(ma.Schema):
    title = ma.String(required=True)
    brand = ma.String(required=False, allow_none=True)
    make = ma.String(required=False, allow_none=True)
    model = ma.String(required=False, allow_none=True)
    year = ma.Integer(required=False, allow_none=True)
    mileage = ma.Integer(required=False, allow_none=True)
    vehicleClassId = ma.Integer(required=False, allow_none=True)
    description = ma.String(required=False, allow_none=True)
    guidelines = ma.String(required=False, allow_none=True)
    transmission = ma.String(required=False, allow_none=True)
    fuelType = ma.String(required=False, allow_none=True)
    seats = ma.Integer(required=False, allow_none=True)
    doors = ma.Integer(required=False, allow_none=True)
    features = ma.List(ma.String(), required=False, allow_none=True)
    images = ma.List(ma.String(), required=False, allow_none=True)
    latitude = ma.Float(required=False, allow_none=True)
    longitude = ma.Float(required=False, allow_none=True)
    rules = ma.String(required=False, allow_none=True)
    pickupNotesTemplate = ma.String(required=False, allow_none=True)
    pricePerDay = ma.Float(required=True)
    photos = ma.List(ma.String(), required=False)
    lat = ma.Float(required=False, allow_none=True)
    lng = ma.Float(required=False, allow_none=True)
    cityZone = ma.String(required=False, allow_none=True)
    pickupAddress = ma.String(required=False, allow_none=True)
    isCompanyOwned = ma.Boolean(required=False)
    areaId = ma.Integer(required=False, allow_none=True)
    locationSourceType = ma.String(required=False, allow_none=True)
    branchId = ma.Integer(required=False, allow_none=True)
    parkingSpotId = ma.Integer(required=False, allow_none=True)
    instantBook = ma.Boolean(required=False)


class ListingUpdateSchema(ma.Schema):
    class Meta:
        unknown = EXCLUDE

    @pre_load
    def coerce_empty_numeric_fields(self, data, **_kwargs):
        if not isinstance(data, dict):
            return data
        cleaned = dict(data)
        for key in ("year", "mileage", "vehicleClassId"):
            if cleaned.get(key) == "":
                cleaned[key] = None
        return cleaned

    title = ma.String(required=False)
    brand = ma.String(required=False, allow_none=True)
    make = ma.String(required=False, allow_none=True)
    model = ma.String(required=False, allow_none=True)
    year = ma.Integer(required=False, allow_none=True)
    mileage = ma.Integer(required=False, allow_none=True)
    vehicleClassId = ma.Integer(required=False, allow_none=True)
    description = ma.String(required=False, allow_none=True)
    guidelines = ma.String(required=False, allow_none=True)
    transmission = ma.String(required=False, allow_none=True)
    fuelType = ma.String(required=False, allow_none=True)
    seats = ma.Integer(required=False, allow_none=True)
    doors = ma.Integer(required=False, allow_none=True)
    features = ma.List(ma.String(), required=False, allow_none=True)
    images = ma.List(ma.String(), required=False, allow_none=True)
    latitude = ma.Float(required=False, allow_none=True)
    longitude = ma.Float(required=False, allow_none=True)
    rules = ma.String(required=False, allow_none=True)
    pickupNotesTemplate = ma.String(required=False, allow_none=True)
    pickupAddress = ma.String(required=False, allow_none=True)
    pricePerDay = ma.Float(required=False)
    photos = ma.List(ma.String(), required=False)
    active = ma.Boolean(required=False)
    status = ma.String(required=False, allow_none=True)
    isCompanyOwned = ma.Boolean(required=False)
    lat = ma.Float(required=False, allow_none=True)
    lng = ma.Float(required=False, allow_none=True)
    cityZone = ma.String(required=False, allow_none=True)
    instantBook = ma.Boolean(required=False)


ListingLocationInputSchema = ListingLocationWriteSchema


class ListingAvailabilitySchema(ma.Schema):
    startAt = ma.DateTime(required=True)
    endAt = ma.DateTime(required=True)
    status = ma.String(required=False, metadata={"example": "AVAILABLE"})


class ListingSearchSchema(ma.Schema):
    bbox = ma.String(
        required=False,
        metadata={
            "description": "minLng,minLat,maxLng,maxLat",
            "example": "-73.75,45.45,-73.50,45.62",
        },
    )
    start_at = ma.DateTime(
        required=False,
        metadata={"description": "Search window start (ISO 8601)."},
    )
    end_at = ma.DateTime(
        required=False,
        metadata={"description": "Search window end (ISO 8601)."},
    )
    start = ma.DateTime(required=False)
    end = ma.DateTime(required=False)
    cityZone = ma.String(required=False)

    @pre_load
    def normalize_search_window(self, data, **_kwargs):
        # Flask query args are MultiDict, not dict — must flatten before alias copy.
        if hasattr(data, "to_dict"):
            cleaned = data.to_dict(flat=True)
        elif isinstance(data, dict):
            cleaned = dict(data)
        else:
            cleaned = dict(data)
        if cleaned.get("start_at") is None and cleaned.get("start") is not None:
            cleaned["start_at"] = cleaned["start"]
        if cleaned.get("end_at") is None and cleaned.get("end") is not None:
            cleaned["end_at"] = cleaned["end"]
        return cleaned


class ListingListSchema(ListingSearchSchema):
    scope = ma.String(
        required=False,
        metadata={
            "description": "mine (owner), fleet (admin), or host (admin). Omit for public search.",
        },
    )


class ListingSchema(ma.Schema):
    listingId = ma.Integer(required=True)
    vehicleId = ma.Integer(allow_none=True)
    sourceType = ma.String(required=True)
    title = ma.String(required=True)
    brand = ma.String(allow_none=True)
    make = ma.String(allow_none=True)
    model = ma.String(allow_none=True)
    year = ma.Integer(allow_none=True)
    mileage = ma.Integer(allow_none=True)
    vehicleClassId = ma.Integer(allow_none=True)
    description = ma.String(allow_none=True)
    guidelines = ma.String(allow_none=True)
    transmission = ma.String(allow_none=True)
    fuelType = ma.String(allow_none=True)
    seats = ma.Integer(allow_none=True)
    doors = ma.Integer(allow_none=True)
    features = ma.List(ma.String(), allow_none=True)
    images = ma.List(ma.String(), allow_none=True)
    latitude = ma.Float(allow_none=True)
    longitude = ma.Float(allow_none=True)
    rules = ma.String(allow_none=True)
    pickupNotesTemplate = ma.String(allow_none=True)
    pricePerDay = ma.Float(required=True)
    photos = ma.List(ma.String(), required=True)
    active = ma.Boolean(required=True)
    status = ma.String(allow_none=True)
    ownerUserId = ma.Integer(allow_none=True)
    isCompanyOwned = ma.Boolean(required=True)
    ownerName = ma.String(allow_none=True)
    ownerProfilePhotoUrl = ma.String(allow_none=True)
    fleetVehicleVin = ma.String(allow_none=True)
    lat = ma.Float(allow_none=True)
    lng = ma.Float(allow_none=True)
    cityZone = ma.String(allow_none=True)
    geohash = ma.String(allow_none=True)
    pickupAddress = ma.String(allow_none=True)
    locationSourceType = ma.String(allow_none=True)
    branchId = ma.Integer(allow_none=True)
    parkingSpotId = ma.Integer(allow_none=True)
    createdByUserId = ma.Integer(allow_none=True)
    createdAt = ma.String(required=True)
    updatedAt = ma.String(required=True)
    averageRating = ma.Float(allow_none=True)
    reviewCount = ma.Integer(required=True)
    instantBook = ma.Boolean(required=True)
    _links = ma.Dict(keys=ma.String(), values=ma.Nested(LinkSchema), required=False)


class ListingCollectionSchema(ma.Schema):
    status = ma.String(required=True)
    scope = ma.String(required=False)
    listings = ma.List(ma.Nested(ListingSchema))
    _links = ma.Dict(keys=ma.String(), values=ma.Nested(LinkSchema), required=False)


class ListingItemSchema(ma.Schema):
    status = ma.String(required=True)
    listing = ma.Nested(ListingSchema)
    _links = ma.Dict(keys=ma.String(), values=ma.Nested(LinkSchema), required=False)


class BookedRangeSchema(ma.Schema):
    startAt = ma.String(required=True)
    endAt = ma.String(required=True)


class BookedRangeCollectionSchema(ma.Schema):
    status = ma.String(required=True)
    ranges = ma.List(ma.Nested(BookedRangeSchema), required=True)


class VehicleClassCollectionSchema(ma.Schema):
    status = ma.String(required=True)
    vehicleClasses = ma.List(ma.Raw(), required=True)


class OwnerBookingsSchema(ma.Schema):
    status = ma.String(required=True)
    bookings = ma.List(ma.Raw(), required=True)
