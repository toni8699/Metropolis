# Metropolis Nexus — Architecture Diagrams

Mermaid diagrams reflecting the current codebase. Render in GitHub, GitLab, VS Code (Mermaid preview), or [mermaid.live](https://mermaid.live).

| Diagram | Section |
|---------|---------|
| System architecture | [§1](#1-high-level-system-architecture) |
| Booking flow (sequence) | [§2](#2-booking-flow-sequence) |
| Database ER | [§3](#3-database-entity-relationship) |

**Notes:** Single React SPA (no mobile app). Flask monolith (no API gateway). Payments via Stripe PaymentIntents (`payment_service.py`, `/webhooks/stripe`); dev/CI uses mock path when `STRIPE_SECRET_KEY` is absent. KYC is `owner_profile` + S3 docs. No `maintenance_log` table — fleet health uses `vehicle.status`.

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
        API["Flask monolith :5000<br/>Blueprints: /api/auth · /market · /bookings<br/>/owner · /admin · /uploads · /vehicles"]
        AUTH["JWT auth + Flask-Limiter<br/>metropolis/auth.py"]
        SVC["Service layer<br/>marketplace_service · rental_service<br/>auth_service · review_service · uploads_service"]
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
        GPS["Vehicle location<br/>listing_location lat/lng<br/>Fleet coords simulated in marketplace_service"]
    end

    RW & HD & FM -->|"REST JSON + Bearer JWT<br/>frontend/src/utils/api.js"| API
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

End-to-end path: search → listing → checkout → `POST /api/bookings` (status `PENDING`) → `POST /api/bookings/:id/payment-intent` (Stripe PaymentIntent or dev mock) → status transitions to `CONFIRMED` or `PENDING_APPROVAL`.

```mermaid
sequenceDiagram
    autonumber
    actor Renter
    participant SPA as React SPA
    participant Auth as Flask /api/auth
    participant Market as Flask /api/market
    participant Book as Flask /api/bookings
    participant MS as marketplace_service
    participant DB as PostgreSQL
    participant Pay as Stripe / payment_service
    participant Host as Host (P2P OWNER listing)
    participant Fleet as Fleet ops (FLEET listing)

    Note over Renter,Fleet: Discovery
    Renter->>SPA: Search location + dates (Header)
    SPA->>Market: GET /api/market/listings?bbox&lat&lng&radius
    Market->>MS: search_listings()
    MS->>DB: SELECT vehicle_listing + listing_location
    DB-->>SPA: active listings

    Renter->>SPA: Open listing /app/listings/:id
    SPA->>Market: GET /api/market/listings/:id
    Market->>MS: get_listing()
    MS->>DB: SELECT listing + hydrate photos/ratings
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
    SPA->>Market: GET /api/market/listings/:id (reload)
    Renter->>SPA: Request to book
    SPA->>SPA: bookingWindowFromDateStrings() → ISO startAt/endAt
    SPA->>Book: POST /api/bookings {listingId, startAt, endAt}
    Book->>MS: create_booking(renter_user_id, payload)

    MS->>DB: SELECT vehicle_listing FOR UPDATE
    alt source_type = FLEET
        MS->>DB: Conflict check by listing_id OR fleet_vehicle_vin
        Note right of Fleet: Same VIN cannot double-book
    else source_type = OWNER (P2P)
        MS->>DB: Conflict check by listing_id only
    end

    MS->>DB: INSERT booking status=PENDING, price_snapshot_json
    MS->>DB: INSERT trip_event BOOKING_CREATED
    MS->>DB: COMMIT
    Book-->>SPA: booking PENDING

    Note over Renter,Fleet: Payment
    SPA->>Pay: Display @stripe/react-stripe-js card UI
    Renter->>SPA: Submit payment form
    SPA->>Book: POST /api/bookings/:id/payment-intent
    Book->>Pay: Create/confirm Stripe PaymentIntent (or mock)
    Pay-->>Book: PaymentIntent confirmed
    Book->>MS: resolve post-payment status
    MS->>DB: UPDATE booking → CONFIRMED or PENDING_APPROVAL
    MS->>DB: INSERT trip_event PAYMENT_COMPLETED
    Book-->>SPA: booking CONFIRMED or PENDING_APPROVAL
    SPA->>Renter: redirect /app/trips

    par Host / fleet notification (read path)
        alt OWNER listing
            Host->>Book: GET /api/owner/bookings
            Book->>MS: owner_bookings()
            MS->>DB: SELECT bookings for host listings
        else FLEET listing
            Fleet->>Book: GET /api/admin/bookings
            Book->>MS: admin_bookings()
            MS->>DB: SELECT company fleet bookings
        end
    end

    Note over Renter,Fleet: Trip lifecycle
    Renter->>SPA: Trips /app/trips
    SPA->>Book: GET /api/bookings/mine
    Book->>MS: list_renter_bookings()
    MS->>DB: SELECT bookings for renter

    opt pickup coordination
        Host->>Book: POST /api/bookings/:id/instructions
        Book->>MS: send_instruction()
        MS->>DB: INSERT booking_instruction + trip_event
        Renter->>Book: POST /api/bookings/:id/confirm-pickup
        MS->>DB: UPDATE booking → IN_PROGRESS
    end

    Renter->>Book: POST /api/bookings/:id/complete
    MS->>DB: UPDATE booking → COMPLETED + trip_event

    opt review
        Renter->>Book: POST /api/bookings/:id/reviews
        MS->>DB: INSERT review
    end
```

**Legacy path (not used by checkout UI):** `GET /api/vehicles/available` and `GET /api/reservations?email=` via `rental_service`.

---

## 3. Database Entity-Relationship

Schema from `db/schema.sql` plus migrations `004`–`012`. PostgreSQL lowercases unquoted identifiers.

```mermaid
erDiagram
    app_user ||--o| owner_profile : has
    app_user }o--o{ roles : has
    app_user ||--o{ vehicle_listing : owns
    app_user ||--o{ booking : rents
    app_user ||--o{ booking_instruction : sends
    app_user ||--o{ trip_event : acts
    app_user ||--o{ review : writes
    app_user ||--o{ organization_members : member
    app_user ||--o{ file_asset : uploads

    organizations ||--o{ organization_members : has
    organizations ||--o{ vehicle_listing : owns

    area ||--o{ branch : has
    branch ||--o{ employee : employs
    branch ||--o| branchmanager : managed_by
    vehicleclass ||--o{ vehicle : classifies
    branch ||--o{ vehicle : stations
    area ||--o{ relocation : routes
    branch ||--o{ company_parking_spot : has
    area ||--o{ company_parking_spot : contains

    vehicle ||--o| vehicle_listing : listed_as
    vehicleclass ||--o{ vehicle_listing : classifies
    branch ||--o{ vehicle_listing : at_branch
    company_parking_spot ||--o{ vehicle_listing : at_spot

    vehicle_listing ||--|| listing_location : located
    vehicle_listing ||--o{ listing_availability : windows
    vehicle_listing ||--o{ booking : receives
    vehicle_listing }o--o{ file_asset : images
    vehicle_listing ||--o{ review : reviewed

    booking ||--o{ booking_instruction : has
    booking ||--o{ trip_event : logs
    booking ||--o{ review : source

    app_user {
        bigint user_id PK
        string email UK
        string password_hash
        string role
        boolean is_admin
    }

    owner_profile {
        bigint user_id PK
        string verification_status
        string payout_ref
    }

    roles {
        int id PK
        string name UK
    }

    user_roles {
        bigint user_id PK
        int role_id PK
    }

    organizations {
        bigint id PK
        string name
    }

    organization_members {
        bigint user_id PK
        bigint organization_id PK
    }

    area {
        int areaid PK
        string areaname
    }

    branch {
        int branchid PK
        int areaid FK
        int managerid FK
        decimal lat
        decimal lng
    }

    employee {
        int eid PK
        int branchid FK
        int supervisorid FK
    }

    branchmanager {
        int eid PK
        int branchid FK
    }

    vehicle {
        string vin PK
        int classid FK
        int branchid FK
        string status
        string make
        string model
        int mileage
    }

    vehicleclass {
        int classid PK
        string classname
        decimal securitydeposit
    }

    relocation {
        int sourceareaid PK
        int targetareaid PK
        decimal fee
    }

    company_parking_spot {
        bigint id PK
        int area_id FK
        int branch_id FK
        decimal lat
        decimal lng
    }

    vehicle_listing {
        bigint listing_id PK
        bigint owner_user_id FK
        string fleet_vehicle_vin FK
        bigint owner_organization_id FK
        string source_type
        decimal price_per_day
        boolean is_company_owned
        boolean active
    }

    listing_location {
        bigint listing_id PK
        decimal lat
        decimal lng
        string city_zone
    }

    listing_availability {
        bigint availability_id PK
        bigint listing_id FK
        datetime start_at
        datetime end_at
        string status
    }

    booking {
        bigint booking_id PK
        bigint listing_id FK
        bigint renter_user_id FK
        datetime start_at
        datetime end_at
        string status
        string price_snapshot_json
    }

    booking_instruction {
        bigint instruction_id PK
        bigint booking_id FK
        bigint owner_user_id FK
        string message
    }

    trip_event {
        bigint event_id PK
        bigint booking_id FK
        bigint actor_user_id FK
        string event_type
        string metadata_json
    }

    file_asset {
        bigint file_id PK
        bigint owner_user_id FK
        bigint listing_id FK
        string object_key UK
        string scope
    }

    listing_image {
        bigint listing_id PK
        bigint file_id PK
        int display_order
    }

    review {
        bigint review_id PK
        bigint booking_id FK
        bigint author_user_id FK
        bigint target_user_id FK
        bigint target_listing_id FK
        string target_type
        int rating
        int cleanliness
        int accuracy
        int communication
    }
```

---

## Source references

| Topic | Location |
|-------|----------|
| Frontend routes | `frontend/src/App.jsx` |
| API blueprints | `backend/metropolis/api/` |
| Booking logic | `backend/metropolis/services/marketplace_service.py` |
| Payment logic | `backend/metropolis/services/payment_service.py` |
| Stripe webhook | `backend/metropolis/api/webhooks.py` |
| Base schema | `db/schema.sql` |
| Active migrations | `backend/alembic/versions/` |
| Historical SQL migrations | `db/migrations/` (read-only history) |
