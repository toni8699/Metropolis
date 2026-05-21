\echo 'Applying clean initial schema from current baseline'
\ir ../schema.sql
\ir ./001_marketplace_mvp.sql
\ir ./002_listing_vehicle_fields.sql
\ir ./003_s3_assets_and_regions.sql
\ir ./004_multi_role_rbac.sql
\ir ./005_simplify_rbac_to_user_admin.sql
\ir ./006_company_location_sources.sql
\ir ./007_listing_vehicle_specs.sql
\ir ./008_listing_rich_details.sql
\ir ./009_schema_standardization.sql
