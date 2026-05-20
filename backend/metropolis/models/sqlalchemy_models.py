"""SQLAlchemy models (incremental adoption alongside psycopg2 services)."""

from metropolis.extensions import sqldb


class UserModel(sqldb.Model):
    __tablename__ = "app_user"

    user_id = sqldb.Column(sqldb.BigInteger, primary_key=True)
    email = sqldb.Column(sqldb.String(255), nullable=False, unique=True)
    password_hash = sqldb.Column(sqldb.Text, nullable=False)
    is_admin = sqldb.Column(sqldb.Boolean, nullable=False, default=False)
    created_at = sqldb.Column(sqldb.DateTime(timezone=True), nullable=False)


class VehicleListingModel(sqldb.Model):
    __tablename__ = "vehicle_listing"

    listing_id = sqldb.Column(sqldb.BigInteger, primary_key=True)
    owner_user_id = sqldb.Column(sqldb.BigInteger, nullable=True)
    created_by_user_id = sqldb.Column(sqldb.BigInteger, nullable=True)
    fleet_vehicle_vin = sqldb.Column(sqldb.String(17), nullable=True)
    source_type = sqldb.Column(sqldb.String(16), nullable=False)
    title = sqldb.Column(sqldb.String(120), nullable=False)
    brand = sqldb.Column(sqldb.String(80), nullable=True)
    make = sqldb.Column(sqldb.String(80), nullable=True)
    model = sqldb.Column(sqldb.String(80), nullable=True)
    year = sqldb.Column(sqldb.Integer, nullable=True)
    description = sqldb.Column(sqldb.Text, nullable=True)
    guidelines = sqldb.Column(sqldb.Text, nullable=True)
    transmission = sqldb.Column(sqldb.String(30), nullable=True)
    fuel_type = sqldb.Column(sqldb.String(30), nullable=True)
    seats = sqldb.Column(sqldb.Integer, nullable=True)
    doors = sqldb.Column(sqldb.Integer, nullable=True)
    features = sqldb.Column(sqldb.JSON, nullable=True)
    images = sqldb.Column(sqldb.JSON, nullable=True)
    address = sqldb.Column(sqldb.String(255), nullable=True)
    latitude = sqldb.Column(sqldb.Float, nullable=True)
    longitude = sqldb.Column(sqldb.Float, nullable=True)
    price_per_day = sqldb.Column(sqldb.Numeric(10, 2), nullable=False)
    is_company_owned = sqldb.Column(sqldb.Boolean, nullable=False, default=False)
    status = sqldb.Column(sqldb.String(30), nullable=True)
    created_at = sqldb.Column(sqldb.DateTime(timezone=True), nullable=False)
