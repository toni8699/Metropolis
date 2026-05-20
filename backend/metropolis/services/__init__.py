from metropolis.services.auth_service import AuthService
from metropolis.services.marketplace_service import MarketplaceService
from metropolis.services.rental_service import RentalService
from metropolis.services.uploads_service import UploadsService

auth_service = AuthService()
marketplace_service = MarketplaceService()
rental_service = RentalService()
uploads_service = UploadsService()

__all__ = [
    "AuthService",
    "MarketplaceService",
    "RentalService",
    "UploadsService",
    "auth_service",
    "marketplace_service",
    "rental_service",
    "uploads_service",
]
