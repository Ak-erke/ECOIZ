# Database Setup for Python Backend

This project uses PostgreSQL in Docker and Prisma only for schema management, migrations, and seed data.

The Python backend (FastAPI / SQLAlchemy) should connect directly to PostgreSQL using the same `DATABASE_URL`.

## Connection Parameters

- Host: `localhost`
- Port: `5432`
- Database: `ecoiz`
- User: `ecoiz`
- Password: `ecoiz_password`
- Connection string: `postgresql://ecoiz:ecoiz_password@localhost:5432/ecoiz`

## Project Structure

```text
database/
├ prisma/
│  ├ schema.prisma
│  ├ migrations/
│  └ seed.ts
├ package.json
├ docker-compose.yml
└ .env
```

## Tables Overview

Prisma models are mapped to PostgreSQL tables in snake_case:

- `User` -> `user`
- `Profile` -> `profile`
- `EcoCategory` -> `eco_category`
- `Habit` -> `habits`
- `UserHabit` -> `user_habit`
- `HabitLog` -> `habit_log`
- `Post` -> `post`
- `PostLike` -> `post_like`
- `PostComment` -> `post_comment`
- `Achievement` -> `achievement`
- `UserAchievement` -> `user_achievement`
- `RefreshToken` -> `refresh_token`

## Main Relationships

- `profile.user_id` -> `user.id`
- `habit.category_id` -> `eco_category.id`
- `habit.creator_id` -> `user.id`
- `user_habit.user_id` -> `user.id`
- `user_habit.habit_id` -> `habits.id`
- `habit_log.user_habit_id` -> `user_habit.id`
- `post.author_id` -> `user.id`
- `post_like.user_id` -> `user.id`
- `post_like.post_id` -> `post.id`
- `post_comment.post_id` -> `post.id`
- `post_comment.author_id` -> `user.id`
- `user_achievement.user_id` -> `user.id`
- `user_achievement.achievement_id` -> `achievement.id`
- `refresh_token.user_id` -> `user.id`

All primary keys use UUIDs.

## Run PostgreSQL in Docker

From the `database` directory:

```bash
docker-compose up -d
```

Stop containers:

```bash
docker-compose down
```

Stop containers and remove volume data:

```bash
docker-compose down -v
```

## Run Prisma Migrations

Install dependencies if needed:

```bash
npm install
```

Apply migrations in development:

```bash
npm run migrate
```

If you need to deploy existing migrations in a non-interactive environment:

```bash
npx prisma migrate deploy
```

## Run Seed

```bash
npm run seed
```

The seed script creates:

- eco categories
- default habits for each category

## Python Backend Usage

For FastAPI / SQLAlchemy, connect directly with:

```bash
postgresql://ecoiz:ecoiz_password@localhost:5432/ecoiz
```

Prisma is not intended to be used as the Python ORM here. It is kept only for:

- schema definition
- migrations
- seed data
