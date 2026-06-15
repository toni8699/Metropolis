# Metropolis Nexus — Architecture Diagrams

Mermaid diagrams reflecting the current codebase. Render in GitHub, GitLab, VS Code (Mermaid preview), or [mermaid.live](https://mermaid.live).

| Diagram | Section |
|---------|---------|
| System architecture | [§1](#1-high-level-system-architecture) |
| Booking flow (sequence) | [§2](#2-booking-flow-sequence) |
| Database ER | [§3](#3-database-entity-relationship) |

**Notes:** Single React SPA (no mobile app). FastAPI monolith (no API gateway). Payments via Stripe PaymentIntents (`payment_service.py`, `/webhooks/stripe`); dev/CI uses mock path when `STRIPE_SECRET_KEY` is absent. KYC is `owner_profile` + S3 docs. No `maintenance_log` table — fleet health uses `vehicle.status`. API docs at `/docs` (FastAPI Swagger).

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph Clients["Client tier — single React SPA (Vite)"]
        RW["Renter marketplace<br/>/ · /app/*<br/>MapBrowse · Listing · Checkout · Trips"]
        HD["Host dashboard<br/>/host · /host/dashboard<br/>HostOnboardingFlow · HostDashboard owner"]
        FM["Fleet / admin portal<br/>/admin<br/>HostDashboard admin · fleet sync"]
        MOB["Mobile app<br/>(not in repo — future)"]
    end

    subgraph Edge["API layer"]
        API["FastAPI ASGI :5000<br/>/api/auth · /api/listings · /api/bookings<br/>/api/users · /api/uploads · /api/fleet"]
        AUTH["JWT auth + slowapi<br/>dependencies/auth.py"]
        SVC["Service layer<br/>listing_service · booking_service · fleet_service<br/>auth_service · review_service · uploads_service"]
        API --> AUTH
        API --> SVC
    end

    subgraph Data["Data & storage"]
        PG[("Neon PostgreSQL<br/>Fleet: area · branch · vehicle<br/>Marketplace: app_user · vehicle_listing · booking")]
        S3[("AWS S3<br/>Listing photos · host KYC docs")]
    end

    subgraph External["Third-party & external (as implemented)"]
        GM["Google Maps / Places JS API<br/>Client-side geocoding & map UI"]
        PAY["Stripe<br/>PaymentIntents + Webhooks<br/>payment_service.py · /webhooks/stripe<br/>Dev/CI: mock path (no key needed)"]
        KYC["Host verification<br/>owner_profile.verification_status<br/>S3 USER_DOC uploads — no vendor API"]
        GPS["Vehicle location<br/>listing_location lat/lng<br/>Fleet coords simulated in fleet_service"]
    end

    RW & HD & FM -->|"REST JSON + Bearer JWT<br/>frontend/src/shared/api/api.js"| API
    MOB -.->|"planned"| API

    SVC -->|"psycopg2"| PG
    SVC -->|"boto3 presigned URLs"| S3
    RW & HD & FM -->|"direct PUT presigned"| S3
    RW & HD & FM -->|"@react-google-maps/api"| GM

    SVC -->|"Stripe SDK"| PAY
    RW -->|"@stripe/react-stripe-js"| PAY
    KYC --> S3
    GPS --> PG
    GPS -.-> GM

    style MOB stroke-dasharray: 5 5
```

---

## 2. Booking Flow (Sequence)

End-to-end path: search → listing → checkout → `POST /api/bookings` (status `PENDING`) → `POST /api/bookings/:id/payments` (Stripe PaymentIntent or dev mock) → status transitions to `CONFIRMED` or `PENDING_APPROVAL`.

```mermaid
sequenceDiagram
    autonumber
    actor Renter
    participant SPA as React SPA
    participant Auth as FastAPI /api/auth
    participant Listings as FastAPI /api/listings
    participant Book as FastAPI /api/bookings
    participant LS as listing_service
    participant BS as booking_service
    participant DB as PostgreSQL
    participant Pay as Stripe / payment_service
    participant Host as Host (P2P OWNER listing)
    participant Fleet as Fleet ops (FLEET listing)

    Note over Renter,Fleet: Discovery
    Renter->>SPA: Search location + dates (Header)
    SPA->>Listings: GET /api/listings?bbox&lat&lng&radius
    Listings->>LS: search_listings()
    LS->>DB: SELECT vehicle_listing + listing_location
    DB-->>SPA: active listings

    Renter->>SPA: Open listing /app/listings/:id
    SPA->>Listings: GET /api/listings/:id
    Listings->>LS: get_listing()
    LS->>DB: SELECT listing + hydrate photos/ratings
    DB-->>SPA: listing detail

    Note over Renter,Fleet: Reserve intent
    Renter->>SPA: Select dates, Reserve
    alt not authenticated
        SPA->>Auth: POST /api/auth/login (or register)
        Auth->>DB: verify app_user, issue JWT
        Auth-->>SPA: access token
    end
    SPA->>SPA: navigate /app/book/:id + date state

    Note over Renter,Fleet: Checkout
    SPA->>Listings: GET /api/listings/:id (reload)
    Renter->>SPA: Request to book
    SPA->>SPA: bookingWindowFromDateStrings() → ISO startAt/endAt
    SPA->>Book: POST /api/bookings {listingId, startAt, endAt}
    Book->>BS: create_booking(renter_user_id, payload)

    BS->>DB: SELECT vehicle_listing FOR UPDATE
    alt source_type = FLEET
        BS->>DB: Conflict check by listing_id OR fleet_vehicle_vin
        Note right of Fleet: Same VIN cannot double-book
    else source_type = OWNER (P2P)
        BS->>DB: Conflict check by listing_id only
    end

    BS->>DB: INSERT booking status=PENDING, price_snapshot_json
    BS->>DB: INSERT trip_event BOOKING_CREATED
    BS->>DB: COMMIT
    Book-->>SPA: booking PENDING

    Note over Renter,Fleet: Payment
    SPA->>Pay: Display @stripe/react-stripe-js card UI
    Renter->>SPA: Submit payment form
    SPA->>Book: POST /api/bookings/:id/payments
    Book->>Pay: Create/confirm Stripe PaymentIntent (or mock)
    Pay-->>Book: PaymentIntent confirmed
    Book->>BS: resolve post-payment status
    BS->>DB: UPDATE booking → CONFIRMED or PENDING_APPROVAL
    BS->>DB: INSERT trip_event PAYMENT_COMPLETED
    Book-->>SPA: booking CONFIRMED or PENDING_APPROVAL
    SPA->>Renter: redirect /app/trips

    par Host / fleet notification (read path)
        alt OWNER listing
            Host->>Book: GET /api/bookings?scope=owner
            Book->>BS: owner_bookings()
            BS->>DB: SELECT bookings for host listings
        else FLEET listing
            Fleet->>Book: GET /api/bookings?scope=fleet
            Book->>BS: admin_bookings()
            BS->>DB: SELECT company fleet bookings
        end
    end

    Note over Renter,Fleet: Trip lifecycle
    Renter->>SPA: Trips /app/trips
    SPA->>Book: GET /api/bookings?scope=mine
    Book->>BS: list_renter_bookings()
    BS->>DB: SELECT bookings for renter

    opt pickup coordination
        Host->>Book: PATCH /api/bookings/:id {status}
        Book->>BS: update_booking_status()
        BS->>DB: UPDATE booking + trip_event
    end

    Renter->>Book: PATCH /api/bookings/:id {status: COMPLETED}
    BS->>DB: UPDATE booking → COMPLETED + trip_event

    opt review
        Renter->>Book: POST /api/bookings/:id/reviews
        BS->>DB: INSERT review
    end
```


---

## 3. Database Entity-Relationship

Canonical schema: `db/schema.sql`, applied on empty databases via Alembic baseline `000001_new_base`. For current ER diagrams split by domain, see [database-schema.md](database-schema.md).

---

## Source references

| Topic | Location |
|-------|----------|
| Frontend routes | `frontend/src/app/App.jsx` |
| API routers | `backend/metropolis/routers/` |
| ASGI entry (HTTP + Socket.IO) | `backend/metropolis/asgi.py` |
| Auth dependencies | `backend/metropolis/dependencies/auth.py` |
| Pydantic schemas | `backend/metropolis/schemas/*_models.py` |
| Booking logic | `backend/metropolis/services/booking_service.py` |
| Listing logic | `backend/metropolis/services/listing_service.py` |
| Fleet logic | `backend/metropolis/services/fleet_service.py` |
| Payment logic | `backend/metropolis/services/payment_service.py` |
| Stripe webhook | `backend/metropolis/routers/webhooks.py` |
| Socket.IO | `backend/metropolis/sockets/booking_chat.py` |
| ARQ booking sweep | `backend/metropolis/jobs/booking_sweep.py` |
| Base schema | `db/schema.sql` |
| Active migrations | `backend/alembic/versions/` |
| ER diagrams (current) | `docs/database-schema.md` |
