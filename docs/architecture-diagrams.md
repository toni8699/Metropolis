# Metropolis Nexus — Architecture Diagrams

Mermaid diagrams reflecting the current codebase. Render in GitHub, GitLab, VS Code (Mermaid preview), or [mermaid.live](https://mermaid.live).

| Diagram | Section |
|---------|---------|
| System architecture | [§1](#1-high-level-system-architecture) |
| Booking flow (sequence) | [§2](#2-booking-flow-sequence) |
| Database ER | [§3](#3-database-entity-relationship) |

**Notes:** Single React SPA (no mobile app). Flask monolith (no API gateway). Payment is mock UI only; no Stripe. KYC is `owner_profile` + S3 docs. No `maintenance_log` table — fleet health uses `vehicle.status`.

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
        PAY["Payment processing<br/>MVP: mock card UI only<br/>price_snapshot_json in DB"]
        KYC["Host verification<br/>owner_profile.verification_status<br/>S3 USER_DOC uploads — no vendor API"]
        GPS["Vehicle location<br/>listing_location lat/lng<br/>Fleet coords simulated in marketplace_service"]
    end

    RW & HD & FM -->|"REST JSON + Bearer JWT<br/>frontend/src/utils/api.js"| API
    MOB -.->|"planned"| API

    SVC -->|"psycopg2"| PG
    SVC -->|"boto3 presigned URLs"| S3
    RW & HD & FM -->|"direct PUT presigned"| S3
    RW & HD & FM -->|"@react-google-maps/api"| GM

    PAY -.->|"not wired — checkout UI only"| RW
    KYC --> S3
    GPS --> PG
    GPS -.-> GM

    style MOB stroke-dasharray: 5 5
    style PAY stroke-dasharray: 5 5
```

---

## 2. Booking Flow (Sequence)

End-to-end path: search → listing → checkout → `POST /api/bookings` → `marketplace_service.create_booking()` (status `CONFIRMED` on create).

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
    participant Pay as Payment (MVP mock)
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
    SPA->>Pay: Display mock card UI (no API call)
    Pay-->>SPA: UI acknowledgment only
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

    MS->>DB: INSERT booking status=CONFIRMED, price_snapshot_json
    MS->>DB: INSERT trip_event BOOKING_CREATED
    MS->>DB: COMMIT
    MS->>DB: SELECT booking (hydrate for response)
    Book-->>SPA: booking CONFIRMED
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
    app_user ||--o| owner_profile : "user_id PK/FK 1:1"
    app_user }o--o{ roles : "user_roles M:N"
    app_user ||--o{ vehicle_listing : "owner_user_id 1:N"
    app_user ||--o{ booking : "renter_user_id 1:N"
    app_user ||--o{ booking_instruction : "owner_user_id 1:N"
    app_user ||--o{ trip_event : "actor_user_id 0..N"
    app_user ||--o{ review : "author_user_id 1:N"
    app_user ||--o{ organization_members : "user_id M:N"
    app_user ||--o{ file_asset : "owner_user_id 0..N"

    roles {
        int id PK
        string name UK
    }

    user_roles {
        bigint user_id PK_FK
        int role_id PK_FK
    }

    owner_profile {
        bigint user_id PK_FK
        string verification_status
        text payout_ref
    }

    organizations ||--o{ organization_members : "organization_id 1:N"
    organizations ||--o{ vehicle_listing : "owner_organization_id 0..N"

    organizations {
        bigint id PK
        string name
    }

    organization_members {
        bigint user_id PK_FK
        bigint organization_id PK_FK
    }

    area ||--o{ branch : "areaid 1:N"
    branch ||--o{ employee : "branchid 1:N"
    branch ||--o| branchmanager : "branchid 1:1"
    vehicleclass ||--o{ vehicle : "classid 1:N"
    branch ||--o{ vehicle : "branchid 1:N"
    area ||--o{ relocation : "source_target M:N pair"
    branch ||--o{ company_parking_spot : "branch_id 0..N"
    area ||--o{ company_parking_spot : "area_id 1:N"

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

    vehicle {
        char17 vin PK
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

    company_parking_spot {
        bigint id PK
        int area_id FK
        int branch_id FK
        decimal lat
        decimal lng
    }

    vehicle ||--o| vehicle_listing : "fleet_vehicle_vin"
    vehicleclass ||--o{ vehicle_listing : "vehicle_class_id"
    branch ||--o{ vehicle_listing : "branch_id"
    company_parking_spot ||--o{ vehicle_listing : "parking_spot_id"

    vehicle_listing ||--|| listing_location : "listing_id PK/FK 1:1"
    vehicle_listing ||--o{ listing_availability : "listing_id 1:N"
    vehicle_listing ||--o{ booking : "listing_id 1:N"
    vehicle_listing }o--o{ file_asset : "listing_image M:N"
    vehicle_listing ||--o{ review : "target_listing_id"

    vehicle_listing {
        bigint listing_id PK
        bigint owner_user_id FK
        char17 fleet_vehicle_vin FK
        bigint owner_organization_id FK
        enum source_type "OWNER or FLEET"
        decimal price_per_day
        boolean is_company_owned
        boolean active
    }

    listing_location {
        bigint listing_id PK_FK
        decimal lat
        decimal lng
        string city_zone
    }

    listing_availability {
        bigint availability_id PK
        bigint listing_id FK
        timestamptz start_at
        timestamptz end_at
        enum status "AVAILABLE or BLOCKED"
    }

    booking ||--o{ booking_instruction : "booking_id 1:N"
    booking ||--o{ trip_event : "booking_id 1:N"
    booking ||--o{ review : "booking_id 1:N"

    booking {
        bigint booking_id PK
        bigint listing_id FK
        bigint renter_user_id FK
        timestamptz start_at
        timestamptz end_at
        enum status "PENDING CONFIRMED IN_PROGRESS COMPLETED CANCELLED"
        jsonb price_snapshot_json
    }

    booking_instruction {
        bigint instruction_id PK
        bigint booking_id FK
        bigint owner_user_id FK
        text message
    }

    trip_event {
        bigint event_id PK
        bigint booking_id FK
        bigint actor_user_id FK
        string event_type
        jsonb metadata_json
    }

    file_asset {
        bigint file_id PK
        bigint owner_user_id FK
        bigint listing_id FK
        string object_key UK
        enum scope "FLEET OWNER_LISTING USER_DOC"
    }

    listing_image {
        bigint listing_id PK_FK
        bigint file_id PK_FK
        int display_order
    }

    review {
        bigint review_id PK
        bigint booking_id FK
        bigint author_user_id FK
        bigint target_user_id FK
        bigint target_listing_id FK
        enum target_type "LISTING or RENTER"
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
| Base schema | `db/schema.sql` |
| Migrations | `db/migrations/` |
