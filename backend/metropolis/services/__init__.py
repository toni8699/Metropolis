from metropolis.services.auth_service import AuthService
from metropolis.services.marketplace_service import MarketplaceService
from metropolis.services.rental_service import RentalService

auth_service = AuthService()
marketplace_service = MarketplaceService()
rental_service = RentalService()

__all__ = [
    "AuthService",
    "MarketplaceService",
    "RentalService",
    "auth_service",
    "marketplace_service",
    "rental_service",
]
