// Optional Buildx Bake definition (used when COMPOSE_BAKE=true).
// Build: docker buildx bake
// Or:    COMPOSE_BAKE=true docker compose build

group "default" {
  targets = ["backend", "frontend"]
}

target "backend" {
  context    = "."
  dockerfile = "backend/Dockerfile"
  tags       = ["drivebnb-backend:local"]
}

target "frontend" {
  context    = "./frontend"
  dockerfile = "Dockerfile"
  tags       = ["drivebnb-frontend:local"]
}
