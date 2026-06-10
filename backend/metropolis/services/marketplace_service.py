from __future__ import annotations

from metropolis.services.booking_service import BookingService
from metropolis.services.fleet_service import FleetService
from metropolis.services.listing_service import ListingService


class MarketplaceService(ListingService, BookingService, FleetService):
    pass


marketplace_service = MarketplaceService()
