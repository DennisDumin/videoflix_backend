# Videoflix Backend

Videoflix is a Django REST Framework backend for a Netflix-style video
streaming application. It provides email-based authentication, JWT auth with
HTTP-only cookies, password reset, admin-based video uploads, asynchronous
video processing with Redis/RQ, and protected HLS streaming for the existing
Videoflix frontend.

This repository contains only the backend. Do not commit frontend files,
`.env`, uploaded media files, generated HLS files, Docker volumes, or local
virtual environments.

## Tech Stack

- Python 3.12
- Django
- Django REST Framework
- Simple JWT with HTTP-only auth cookies
- PostgreSQL
- Redis with django-redis
- Django RQ
- ffmpeg for HLS conversion
- Gunicorn
- Whitenoise
- django-import-export
- Docker Compose

## Features

- Email-based user registration and login
- Account activation by email link
- Password reset by email link
- JWT access and refresh tokens stored in HTTP-only cookies
- Protected video metadata and HLS streaming endpoints
- Video upload through Django admin
- Background video processing with Django signals and RQ
- HLS output for `480p`, `720p`, and `1080p`
- Automatic thumbnail generation when no thumbnail is uploaded
- Admin action for reprocessing videos

## Setup With Docker

Create a local environment file:

```powershell
copy .env.example .env
```

Start Docker Desktop, then build and run the backend:

```powershell
docker compose up --build
```

The backend is available at:

```text
http://127.0.0.1:8000
```

The Django admin is available at:

```text
http://127.0.0.1:8000/admin/
```

Default admin credentials from `.env.example`:

```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=adminpassword
```

The entrypoint waits for PostgreSQL, runs static collection, runs migrations,
creates the configured superuser, starts an RQ worker, and starts Gunicorn.

Useful Docker commands:

```powershell
docker compose logs -f web
docker compose ps
docker compose restart web
docker compose down
```

## Frontend

The frontend is a separate repository. Start it with Live Server from the
frontend project root by opening the top-level `index.html`.

Local frontend URL:

```text
http://127.0.0.1:5500
```

If Live Server uses a different port, update these values in `.env` and restart
the backend:

```env
FRONTEND_URL=http://127.0.0.1:5500
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

## Environment Variables

Important `.env` values:

| Name | Description |
| --- | --- |
| `SECRET_KEY` | Django secret key. |
| `DEBUG` | Enables development mode. |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts. |
| `CORS_ALLOWED_ORIGINS` | Allowed frontend origins for CORS. |
| `CSRF_TRUSTED_ORIGINS` | Trusted frontend origins for CSRF. |
| `DB_NAME` | PostgreSQL database name. |
| `DB_USER` | PostgreSQL database user. |
| `DB_PASSWORD` | PostgreSQL database password. |
| `DB_HOST` | PostgreSQL host, usually `db` in Docker. |
| `DB_PORT` | PostgreSQL port. |
| `REDIS_LOCATION` | Redis cache URL. |
| `REDIS_HOST` | Redis host for RQ. |
| `REDIS_PORT` | Redis port for RQ. |
| `REDIS_DB` | Redis database number for RQ. |
| `EMAIL_BACKEND` | Uses console emails locally by default. |
| `FRONTEND_URL` | Base URL used in activation and reset emails. |
| `JWT_ACCESS_COOKIE_NAME` | Access token cookie name. |
| `JWT_REFRESH_COOKIE_NAME` | Refresh token cookie name. |

Local emails are printed to the backend logs when
`EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`.

## Authentication

Authentication uses JWT tokens stored in HTTP-only cookies:

- `access_token` authenticates protected API requests.
- `refresh_token` is used by `/api/token/refresh/`.

The frontend does not need to store tokens manually. Login and refresh set the
cookies, logout deletes them, and refresh tokens are blacklisted where possible.

## API Endpoints

Base URL:

```text
http://127.0.0.1:8000/api
```

### Auth

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/register/` | Register an inactive user and send activation email. | No |
| `GET` | `/api/activate/<uidb64>/<token>/` | Activate a user account. | No |
| `POST` | `/api/login/` | Login and set JWT cookies. | No |
| `POST` | `/api/logout/` | Delete JWT cookies and blacklist refresh token if present. | No |
| `POST` | `/api/token/refresh/` | Create a new access cookie from the refresh cookie. | Refresh cookie |
| `POST` | `/api/password_reset/` | Send a password reset email if the user exists. | No |
| `POST` | `/api/password_confirm/<uidb64>/<token>/` | Save a new password. | No |

### Videos

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| `GET` | `/api/video/` | List ready videos for the frontend. | Yes |
| `GET` | `/api/video/<movie_id>/<resolution>/index.m3u8` | Return a protected HLS manifest. | Yes |
| `GET` | `/api/video/<movie_id>/<resolution>/<segment>` | Return a protected HLS segment. | Yes |

Allowed HLS resolutions:

- `480p`
- `720p`
- `1080p`

## Video Upload And Processing

Videos are uploaded through Django admin:

1. Open `/admin/`.
2. Log in with the superuser.
3. Add a `Video`.
4. Fill `title`, `description`, `category`, and `original_file`.
5. Save.

After saving, a Django `post_save` signal queues an RQ background job. The job
uses ffmpeg to convert the uploaded video into HLS playlists and `.ts` segments.

Generated media structure:

```text
media/videos/<video_id>/480p/index.m3u8
media/videos/<video_id>/480p/segment_000.ts
media/videos/<video_id>/720p/index.m3u8
media/videos/<video_id>/1080p/index.m3u8
media/thumbnails/<video_id>.jpg
```

Processing status flow:

```text
pending -> processing -> ready
```

If ffmpeg fails, the video status becomes `failed` and the error is stored in
`processing_error`.

## Manual Demo Flow

1. Start the backend with Docker Compose.
2. Start the frontend with Live Server.
3. Register a user in the frontend.
4. Copy the activation link from `docker compose logs -f web` and open it.
5. Log in with the activated user.
6. Upload an `.mp4` video in Django admin.
7. Wait until the video status is `ready`.
8. Refresh the frontend video list and play the uploaded video.

## Manual API Checks

The project can be tested manually with Postman:

- Register with matching and mismatching passwords.
- Activate with a valid and invalid token.
- Login before and after activation.
- Refresh with and without a refresh cookie.
- Logout with and without valid cookies.
- Request password reset for known and unknown emails.
- Confirm password reset with valid, invalid, and mismatching payloads.
- Verify that unauthenticated video endpoints return `401`.
- Verify that missing videos, invalid resolutions, and invalid segments return
  `404`.
- Upload a video, wait for `ready`, then request the video list, manifest, and
  HLS segments.

## Development Checks

Run the Django system check inside Docker:

```powershell
docker compose exec -T web python manage.py check
```

Check for missing migrations:

```powershell
docker compose exec -T web python manage.py makemigrations --check --dry-run
```

Open a Django shell:

```powershell
docker compose exec web python manage.py shell
```

## Admin

The Django admin is enabled at `/admin/`. Videos can be created, inspected,
imported, exported, and reprocessed there.
