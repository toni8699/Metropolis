from metropolis.services.auth_service import AuthService
from metropolis.services.booking_service import BookingService, booking_service
from metropolis.services.fleet_service import FleetService, fleet_service
from metropolis.services.kyc_service import KycService, kyc_service
from metropolis.services.listing_service import ListingService, listing_service
from metropolis.services.message_service import MessageService
from metropolis.services.payment_service import PaymentService, payment_service
from metropolis.services.payout_service import PayoutService, payout_service
from metropolis.services.review_service import ReviewService
from metropolis.services.saved_listing_service import SavedListingService, saved_listing_service
from metropolis.services.uploads_service import UploadsService

auth_service = AuthService()
message_service = MessageService()
review_service = ReviewService()
uploads_service = UploadsService()

__all__ = [
    "auth_service",
    "booking_service",
    "fleet_service",
    "kyc_service",
    "listing_service",
    "message_service",
    "payment_service",
    "payout_service",
    "review_service",
    "saved_listing_service",
    "uploads_service",
    "AuthService",
    "BookingService",
    "FleetService",
    "KycService",
    "ListingService",
    "MessageService",
    "PaymentService",
    "PayoutService",
    "ReviewService",
    "SavedListingService",
    "UploadsService",
]
