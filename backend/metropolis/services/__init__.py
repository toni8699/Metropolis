from metropolis.services.auth_service import AuthService
from metropolis.services.kyc_service import KycService, kyc_service
from metropolis.services.marketplace_service import marketplace_service
from metropolis.services.message_service import MessageService
from metropolis.services.payment_service import PaymentService, payment_service
from metropolis.services.review_service import ReviewService
from metropolis.services.uploads_service import UploadsService

auth_service = AuthService()
message_service = MessageService()
review_service = ReviewService()
uploads_service = UploadsService()

__all__ = [
    "auth_service",
    "kyc_service",
    "marketplace_service",
    "message_service",
    "payment_service",
    "review_service",
    "uploads_service",
    "AuthService",
    "KycService",
    "MessageService",
    "PaymentService",
    "ReviewService",
    "UploadsService",
]
