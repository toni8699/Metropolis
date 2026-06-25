"""Vehicle / VIN / catalog schemas."""

from __future__ import annotations

from pydantic import Field

from vroom.schemas.camel import CamelModel


class VinDecodeRequest(CamelModel):
    vin: str


class BodyTypeResponse(CamelModel):
    body_type_id: int = Field(serialization_alias="bodyTypeId")
    code: str
    display_name: str = Field(serialization_alias="displayName")
    sort_order: int = Field(serialization_alias="sortOrder")


class SuggestedBodyTypeResponse(CamelModel):
    body_type_id: int = Field(serialization_alias="bodyTypeId")
    code: str
    display_name: str = Field(serialization_alias="displayName")


class SpecFieldResponse(CamelModel):
    value: str | int | None = None
    is_verified: bool = Field(default=False, serialization_alias="isVerified")
    source: str = "missing"


class DecodedVehicleResponse(CamelModel):
    make: str | None = None
    model: str | None = None
    model_year: int | None = Field(default=None, serialization_alias="modelYear")
    transmission: SpecFieldResponse | None = None
    fuel_type: SpecFieldResponse | None = Field(default=None, serialization_alias="fuelType")
    seats: SpecFieldResponse | None = None
    doors: SpecFieldResponse | None = None
    body_class: str | None = Field(default=None, serialization_alias="bodyClass")
    body_type_id: int | None = Field(default=None, serialization_alias="bodyTypeId")
    suggested_body_type: SuggestedBodyTypeResponse | None = Field(
        default=None, serialization_alias="suggestedBodyType"
    )


class VinDecodeResponse(CamelModel):
    status: str
    vin: str | None = None
    message: str | None = None
    decoded: DecodedVehicleResponse | None = None
    raw_stored: bool = Field(default=False, serialization_alias="rawStored")


class BodyTypeCollectionResponse(CamelModel):
    status: str
    body_types: list[BodyTypeResponse] = Field(
        default_factory=list, serialization_alias="bodyTypes"
    )


class FeatureResponse(CamelModel):
    feature_id: int = Field(serialization_alias="featureId")
    code: str
    name: str
    icon_key: str = Field(serialization_alias="iconKey")
    category: str
    sort_order: int = Field(serialization_alias="sortOrder")


class FeatureCollectionResponse(CamelModel):
    status: str
    features: list[FeatureResponse] = Field(default_factory=list)
