# ECOIZ

ECOIZ is a team project with a user-facing app, admin web, backend, and shared reference layers.

## Structure

- `admin-web/` - Next.js admin panel
- `backend/` - FastAPI backend and tests
- `frontend/` - iOS frontend (`EcoIz-IOS`), Xcode project, and UI tests
- `ai-reference/` - shared AI reference implementation from the team repository
- `database/` - legacy Prisma schema and seed data kept for reference

## Notes

- Current working runtime stack is `admin-web -> backend -> PostgreSQL`.
- `database/` is not the active runtime database layer right now because the backend uses SQLAlchemy + Alembic.
- `ai-reference/` is stored as a reference layer and is not wired into the active backend runtime by default.
