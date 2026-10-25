# Plagiarism Checker

Plagiarism Checker uses a FastAPI backend, a Streamlit UI, and a C++ ingestion engine. Document metadata, authentication, and compressed document storage use the configured Supabase project; Compose does not create a local database or replace Supabase services.

## Prerequisites

- Docker Desktop (or Docker Engine) with the Docker Compose plugin.
- A Supabase project with its database, Auth, and Storage services enabled.

## One-time Supabase setup

1. In the Supabase SQL Editor, run [`database/schema.sql`](./database/schema.sql) to create the application tables, indexes, and `compressed_docs` Storage bucket.
2. Copy [`backend/.env.example`](./backend/.env.example) to `backend/.env`:

   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```

3. Set the values in `backend/.env` from the Supabase project:
   - `DATABASE_URL`: the Supabase PostgreSQL connection string used by the API.
   - `DIRECT_URL`: the direct Supabase PostgreSQL connection string (used by Alembic migrations).
   - `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_KEY`: the project URL, anon key, and service-role key.
   - `JWT_SECRET`: the project's JWT secret.

Keep `backend/.env` private; it is excluded from version control and the Docker build context. The service-role key grants elevated access and must not be shared publicly.

## Start the application

From the repository root:

```sh
docker compose up -d --build
```

- Streamlit UI: <http://localhost:8501>
- FastAPI: <http://localhost:8000>
- API documentation: <http://localhost:8000/docs>

Compose builds the C++ CLI into the API image and connects the UI to the API over the internal Compose network. All application data remains in Supabase.

## Deploy to Render

Deploy two separate Render **Web Services** from the repository:

| Service | Runtime | Dockerfile path | Docker context |
| --- | --- | --- | --- |
| API | Docker | `backend/Dockerfile` | repository root |
| UI | Docker | `frontend/Dockerfile` | repository root |

For both services, leave the root directory at the repository root. The Dockerfiles listen on Render's injected `PORT` and bind to `0.0.0.0`.

1. Create the API web service first. Add the Supabase values listed above as Render environment variables. Set the health check path to `/`.
2. Create the UI web service. Set `API_BASE_URL` to the API service URL followed by `/api`, for example `https://your-api-service.onrender.com/api`.
3. Deploy both services in the same Render region. The UI calls the API server-side; for private networking, use the API's internal URL instead of its public URL.

Do not upload or commit `.env` files to Render or Git. Configure secrets in each service's Render environment settings.

To inspect service logs or stop the containers:

```sh
docker compose logs -f
docker compose down
```
