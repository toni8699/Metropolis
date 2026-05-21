from metropolis.services.auth_service import AuthService
from metropolis.services.marketplace_service import MarketplaceService
from metropolis.services.rental_service import RentalService
from metropolis.services.review_service import ReviewService
from metropolis.services.uploads_service import UploadsService

auth_service = AuthService()
marketplace_service = MarketplaceService()
rental_service = RentalService()
review_service = ReviewService()
uploads_service = UploadsService()

__all__ = [
    "AuthService",
    "MarketplaceService",
    "RentalService",
    "ReviewService",
    "UploadsService",
    "auth_service",
    "marketplace_service",
    "rental_service",
    "review_service",
    "uploads_service",
]
