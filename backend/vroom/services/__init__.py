from vroom.services.auth_service import AuthService
from vroom.services.booking_service import BookingService, booking_service
from vroom.services.fleet_service import FleetService, fleet_service
from vroom.services.kyc_service import KycService, kyc_service
from vroom.services.listing_service import ListingService, listing_service
from vroom.services.message_service import MessageService
from vroom.services.payment_service import PaymentService, payment_service
from vroom.services.payout_service import PayoutService, payout_service
from vroom.services.review_service import ReviewService
from vroom.services.saved_listing_service import SavedListingService, saved_listing_service
from vroom.services.trip_inspection_service import (
    TripInspectionService,
    trip_inspection_service,
)
from vroom.services.uploads_service import UploadsService

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
    "trip_inspection_service",
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
    "TripInspectionService",
    "UploadsService",
]
