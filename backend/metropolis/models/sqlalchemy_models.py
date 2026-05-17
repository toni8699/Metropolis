"""SQLAlchemy models (incremental adoption alongside psycopg2 services)."""

from metropolis.extensions import sqldb


class VehicleListingModel(sqldb.Model):
    __tablename__ = "vehicle_listing"

    listing_id = sqldb.Column(sqldb.BigInteger, primary_key=True)
    owner_user_id = sqldb.Column(sqldb.BigInteger, nullable=True)
    fleet_vehicle_vin = sqldb.Column(sqldb.String(17), nullable=True)
    source_type = sqldb.Column(sqldb.String(16), nullable=False)
    title = sqldb.Column(sqldb.String(120), nullable=False)
    brand = sqldb.Column(sqldb.String(80), nullable=True)
    make = sqldb.Column(sqldb.String(80), nullable=True)
    model = sqldb.Column(sqldb.String(80), nullable=True)
    year = sqldb.Column(sqldb.Integer, nullable=True)
    price_per_day = sqldb.Column(sqldb.Numeric(10, 2), nullable=False)
