# Database Schema (ER Diagrams)

Mermaid ER diagrams for current schema, split by domain flow/API surface so each diagram stays readable.

---

## 1) Identity + Ownership Flow (`/api/auth`, host onboarding, admin host verification)

```mermaid
erDiagram
    app_user ||--o| owner_profile : "has host profile"
    app_user ||--o{ vehicle_listing : "owns listings"
    app_user ||--o{ vehicle_asset : "owns/manages assets"
    app_user ||--o{ vehicle_management_assignment : "assigned manager"

    app_user {
        bigint user_id PK
        varchar email UK
        text password_hash
        user_role role
        boolean is_admin
    }

    owner_profile {
        bigint user_id PK,FK
        varchar verification_status
        text payout_ref
    }

    vehicle_asset {
        bigint vehicle_id PK
        varchar vin UK
        vehicle_owner_type owner_type
        bigint owner_party_user_id FK
        vehicle_asset_status asset_status
    }
```

---

## 2) Asset + Listing Catalog Flow (`/api/listings`, `/api/listings?scope=*`, browse/search)

```mermaid
erDiagram
    vehicle_asset ||--o{ vehicle_listing : "projected as listing"
    app_user ||--o{ vehicle_listing : "owner_user_id"
    vehicle_listing ||--|| listing_location : "has location"
    vehicle_listing ||--o{ listing_availability : "blocked windows"
    vehicle_listing ||--o{ listing_image : "image links"
    file_asset ||--o{ listing_image : "image source"

    vehicle_listing {
        bigint listing_id PK
        bigint vehicle_id FK
        bigint owner_user_id FK
        listing_source_type source_type
        listing_visibility_status visibility_status
        boolean active
        decimal price_per_day
    }

    listing_location {
        bigint listing_id PK,FK
        decimal lat
        decimal lng
        varchar city_zone
    }

    listing_availability {
        bigint availability_id PK
        bigint listing_id FK
        timestamptz start_at
        timestamptz end_at
        availability_status status
    }
```

---

## 3) Booking + Payment + Trip Lifecycle (`/api/bookings*`, `/webhooks/stripe`)

```mermaid
erDiagram
    vehicle_listing ||--o{ booking : "booked as"
    app_user ||--o{ booking : "renter_user_id"
    booking ||--o| payment : "payment record"
    booking ||--o{ trip_event : "lifecycle events"
    app_user ||--o{ trip_event : "actor_user_id"
    booking ||--o{ booking_instruction : "host instructions"
    app_user ||--o{ booking_instruction : "owner_user_id"

    booking {
        bigint booking_id PK
        bigint listing_id FK
        bigint renter_user_id FK
        booking_status status
        booking_access_type access_type
        jsonb price_snapshot_json
    }

    payment {
        bigint payment_id PK
        bigint booking_id FK,UK
        integer amount_cents
        varchar currency
        varchar status
        varchar stripe_payment_intent_id
    }

    trip_event {
        bigint event_id PK
        bigint booking_id FK
        bigint actor_user_id FK
        varchar event_type
        jsonb metadata_json
    }
```

---

## 4) Chat / Inbox Flow (`/api/bookings/:id/messages`, inbox page)

```mermaid
erDiagram
    booking ||--o{ booking_message : "chat thread"
    app_user ||--o{ booking_message : "sender"
    booking ||--o{ booking_chat_state : "per-user read cursor"
    app_user ||--o{ booking_chat_state : "reader"
    booking_message ||--o{ booking_chat_state : "last_read_message_id"

    booking_message {
        bigint message_id PK
        bigint booking_id FK
        bigint sender_id FK
        text message_text
        timestamp created_at
    }

    booking_chat_state {
        bigint booking_id PK,FK
        bigint user_id PK,FK
        bigint last_read_message_id FK
        timestamptz last_read_at
    }
```

---

## 5) Reviews + Media Flow (`/api/listings/:id/reviews`, uploads)

```mermaid
erDiagram
    booking ||--o{ review : "review source trip"
    app_user ||--o{ review : "author"
    app_user ||--o{ review : "target user"
    vehicle_listing ||--o{ review : "target listing"
    app_user ||--o{ file_asset : "uploaded by"
    vehicle_listing ||--o{ file_asset : "attached to listing"

    review {
        bigint review_id PK
        bigint booking_id FK
        bigint author_user_id FK
        review_target_type target_type
        bigint target_user_id FK
        bigint target_listing_id FK
        int rating
    }

    file_asset {
        bigint file_id PK
        bigint owner_user_id FK
        bigint listing_id FK
        text object_key UK
        varchar scope
    }
```

---

## 6) Managed Hosting + Fleet Operations Flow (`/api/fleet/*`, company operations)

```mermaid
erDiagram
    management_program ||--o{ vehicle_management_assignment : "selected program"
    vehicle_asset ||--o{ vehicle_management_assignment : "assignment history"
    vehicle_asset ||--o{ vehicle_compliance_event : "compliance checks"
    vehicle_asset ||--o{ vehicle_insurance_policy : "policies"
    parking_hub ||--o{ parking_spot_allocation : "hub spots"
    vehicle_asset ||--o{ parking_spot_allocation : "allocated parking"
    membership_tier ||--o{ vehicle_membership_eligibility : "tier mapping"
    vehicle_asset ||--o{ vehicle_membership_eligibility : "eligible assets"

    management_program {
        bigint program_id PK
        varchar name UK
        decimal commission_rate
        jsonb included_services
    }

    vehicle_management_assignment {
        bigint assignment_id PK
        bigint vehicle_id FK
        bigint manager_party_user_id FK
        bigint program_id FK
        management_assignment_status status
    }

    vehicle_compliance_event {
        bigint compliance_event_id PK
        bigint vehicle_id FK
        compliance_event_type event_type
        compliance_result result
    }
```

