# Metropolis Nexus

Vehicle rental platform — backend rental logic in Java, PostgreSQL on Neon, React web UI coming in `frontend/`.

## Layout

```text
backend/          Java rental services + dev CLI
  src/            RentalService, options, Database
  scripts/        build.sh, run.sh, clean.sh
db/               schema.sql, seed.sql, setup-neon.sh
frontend/         React + Tailwind (planned)
```

## Database (Neon)

1. Create a project at [neon.tech](https://neon.tech).
2. Copy the connection string into `.env`:

   ```bash
   cp .env.example .env
   # edit DATABASE_URL
   ```

3. Apply schema and sample data (requires `psql`):

   ```bash
   chmod +x db/setup-neon.sh
   ./db/setup-neon.sh
   ```

## Backend CLI (optional dev tool)

```bash
chmod +x backend/scripts/*.sh db/setup-neon.sh
./backend/scripts/build.sh
./backend/scripts/run.sh
```

Loads `DATABASE_URL` from `.env` when present.

## Rental logic

Business rules live in `backend/src/RentalService.java` (reservations, relocation simulation, revenue, etc.). The CLI in `options.java` mirrors the same operations for local testing.
