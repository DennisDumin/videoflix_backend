# Videoflix Backend

Videoflix is a Django REST backend for the Videoflix frontend project. It provides user registration, account activation, cookie based JWT login, password reset, video metadata, protected HLS streaming, Docker setup, PostgreSQL, Redis, Django RQ background jobs, and ffmpeg based video processing.

## Tech Stack

- Python 3.12
- Django
- Django REST Framework
- Simple JWT
- PostgreSQL
- Redis
- Django RQ
- ffmpeg
- Gunicorn
- Docker Compose

## Project Structure

```text
videoflix_backend/
  accounts/          User model, auth endpoints, emails, JWT cookies
  videos/            Video model, admin upload, HLS processing, streaming
  core/              Django settings, root urls, WSGI/ASGI
  backend.Dockerfile
  backend.entrypoint.sh
  docker-compose.yml
  requirements.txt
  .env.example
```

## Setup

Create a local environment file:

```powershell
copy .env.example .env
```

Start Docker Desktop first, then build and start the containers:

```powershell
docker compose up --build
```

This runs the app in the foreground and shows the logs in the terminal. Closing the terminal or pressing `Ctrl+C` stops the containers.

For background mode:

```powershell
docker compose up -d --build
```

In background mode you can close the terminal. Useful follow-up commands:

```powershell
docker compose logs -f web
docker compose ps
docker compose down
docker compose restart web
```

The backend runs at:

```text
http://127.0.0.1:8000
```

The Django admin is available at:

```text
http://127.0.0.1:8000/admin/
```

## Docker Volumes

Docker does not unpack images into the project folder. The source code is mounted from this project into `/app`, but generated runtime data is stored in named Docker volumes:

- `videoflix_backend_postgres_data`
- `videoflix_backend_redis_data`
- `videoflix_backend_videoflix_media`
- `videoflix_backend_videoflix_static`

The uploaded videos, generated thumbnails, HLS manifests, and HLS `.ts` segments are inside the `videoflix_backend_videoflix_media` volume.

Inspect generated media files:

```powershell
docker compose exec web sh
ls -la /app/media
ls -la /app/media/videos
```

List Docker volumes:

```powershell
docker volume ls
```

## Entrypoint Behavior

When the `web` container starts, `backend.entrypoint.sh` does the following:

1. Waits until PostgreSQL is ready.
2. Runs `collectstatic`.
3. Runs `makemigrations`.
4. Runs `migrate`.
5. Creates a superuser from environment variables if it does not exist.
6. Starts one RQ worker for the `default` queue.
7. Starts Gunicorn on port `8000`.

Because the RQ worker is started inside the `web` container, restart the web container after changing task code:

```powershell
docker compose restart web
```

## Superuser

Default superuser values are read from `.env`:

```env
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=adminpassword
```

Use these credentials for the Django admin, or change them before the first start.

## Local Development Without Docker

Docker is the recommended way for this project. If you run it locally without Docker, install PostgreSQL, Redis, and ffmpeg yourself.

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run Django checks:

```powershell
python manage.py check
```

Run the development server:

```powershell
python manage.py runserver
```

Start an RQ worker:

```powershell
python manage.py rqworker default
```

On Windows, a normal RQ worker can have fork-related issues. If that happens, install `rq-win` and use:

```powershell
python manage.py rqworker --worker-class rq_win.WindowsWorker default
```

## Environment Variables

Important `.env` values:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,[::1]
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=videoflix_password
DB_HOST=db
DB_PORT=5432

REDIS_LOCATION=redis://redis:6379/1
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
FRONTEND_URL=http://127.0.0.1:5500

JWT_ACCESS_COOKIE_NAME=access_token
JWT_REFRESH_COOKIE_NAME=refresh_token
JWT_COOKIE_SECURE=False
JWT_COOKIE_SAMESITE=Lax
```

For local frontend development, make sure `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` match the frontend URL.

## Authentication

Authentication uses JWT tokens stored as HttpOnly cookies:

- `access_token`
- `refresh_token`

The backend accepts the access token from either the `Authorization: Bearer <token>` header or the `access_token` cookie. Postman can use the cookies automatically after login.

## API Endpoints

Base URL:

```text
http://127.0.0.1:8000/api
```

### Register

```http
POST /api/register/
Content-Type: application/json
```

Body:

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "confirmed_password": "SecurePassword123!"
}
```

Success: `201 Created`

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com"
  },
  "token": "activation-token"
}
```

The user is inactive until the activation link is opened. With the console email backend, the activation email is printed in the Docker logs.

### Activate Account

```http
GET /api/activate/<uidb64>/<token>/
```

Success: `200 OK`

```json
{
  "message": "Account successfully activated."
}
```

### Login

```http
POST /api/login/
Content-Type: application/json
```

Body:

```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

Success: `200 OK`

```json
{
  "detail": "Login successful",
  "user": {
    "id": 1,
    "username": "user@example.com"
  }
}
```

The response sets the `access_token` and `refresh_token` cookies.

### Refresh Token

```http
POST /api/token/refresh/
```

Requires the `refresh_token` cookie.

Success: `200 OK`

```json
{
  "detail": "Token refreshed",
  "access": "new-access-token"
}
```

### Logout

```http
POST /api/logout/
```

Requires valid auth and the `refresh_token` cookie.

Success: `200 OK`

```json
{
  "detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."
}
```

The response deletes both JWT cookies and blacklists the refresh token.

### Password Reset

```http
POST /api/password_reset/
Content-Type: application/json
```

Body:

```json
{
  "email": "user@example.com"
}
```

Success: `200 OK`

```json
{
  "detail": "An email has been sent to reset your password."
}
```

The response is the same for existing and non-existing users to avoid exposing accounts.

### Password Confirm

```http
POST /api/password_confirm/<uidb64>/<token>/
Content-Type: application/json
```

Body:

```json
{
  "new_password": "NewSecurePassword123!",
  "confirm_password": "NewSecurePassword123!"
}
```

Success: `200 OK`

```json
{
  "detail": "Your Password has been successfully reset."
}
```

### Video List

```http
GET /api/video/
```

Requires auth.

Success: `200 OK`

```json
[
  {
    "id": 1,
    "created_at": "2026-06-21T10:00:00Z",
    "title": "Example Video",
    "description": "Example description",
    "thumbnail_url": "http://127.0.0.1:8000/media/thumbnails/1.jpg",
    "category": "Drama"
  }
]
```

### HLS Manifest

```http
GET /api/video/<movie_id>/<resolution>/index.m3u8
```

Allowed resolutions:

- `480p`
- `720p`
- `1080p`

Requires auth.

Success: `200 OK`

Content type:

```text
application/vnd.apple.mpegurl
```

### HLS Segment

```http
GET /api/video/<movie_id>/<resolution>/<segment>
```

Example:

```http
GET /api/video/1/720p/segment_000.ts
```

Requires auth.

Success: `200 OK`

Content type:

```text
video/MP2T
```

## Video Upload And HLS Processing

Videos are uploaded through the Django admin:

1. Open `/admin/`.
2. Log in with the superuser.
3. Add a `Video`.
4. Fill `title`, `description`, `category`, and `original_file`.
5. Save.

After saving, a post-save signal adds a background job to the RQ queue. The worker processes the uploaded file with ffmpeg and updates the video status:

```text
pending -> processing -> ready
```

If ffmpeg fails, the status becomes:

```text
failed
```

The backend creates:

- 480p HLS playlist and segments
- 720p HLS playlist and segments
- 1080p HLS playlist and segments
- thumbnail image if none was uploaded

Generated paths look like this inside the media volume:

```text
/app/media/videos/<video_id>/480p/index.m3u8
/app/media/videos/<video_id>/480p/segment_000.ts
/app/media/videos/<video_id>/720p/index.m3u8
/app/media/videos/<video_id>/1080p/index.m3u8
/app/media/thumbnails/<video_id>.jpg
```

The HLS command uses 10 second segments:

```text
-hls_time 10
-hls_list_size 0
-hls_playlist_type vod
```

The backend generates HLS files that can be played by Video.js. The 10 second loading behavior is mostly controlled by HLS segment duration and the frontend player preload behavior. In Video.js, the frontend should load the `.m3u8` manifest and can use `preload="auto"` if the browser/player should start buffering early.

## Manual Postman Test Plan

No automated Django `tests.py` files are required for this project. The endpoints can be tested manually with Postman.

### Auth Happy Path

1. `POST /api/register/` with a valid email and matching secure passwords.
   - Expected: `201 Created`
   - Expected body contains `user.id`, `user.email`, and `token`.
2. Copy the activation URL from Docker logs or build it from the returned token and uid from the email.
   - Expected: activation email is printed when `EMAIL_BACKEND` is console.
3. `GET /api/activate/<uidb64>/<token>/`.
   - Expected: `200 OK`
   - Expected body: `Account successfully activated.`
4. `POST /api/login/` with the activated user.
   - Expected: `200 OK`
   - Expected cookies: `access_token`, `refresh_token`
5. `GET /api/video/` with login cookies.
   - Expected: `200 OK`
   - Expected body: array of videos.
6. `POST /api/token/refresh/` with the refresh cookie.
   - Expected: `200 OK`
   - Expected new `access_token` cookie.
7. `POST /api/logout/` with both cookies.
   - Expected: `200 OK`
   - Expected cookies are deleted.

### Auth Unhappy Path

1. `POST /api/register/` with different `password` and `confirmed_password`.
   - Expected: `400 Bad Request`
2. `POST /api/register/` with an already registered email.
   - Expected: `400 Bad Request`
3. `POST /api/login/` before account activation.
   - Expected: `400 Bad Request`
4. `POST /api/login/` with a wrong password.
   - Expected: `400 Bad Request`
5. `GET /api/activate/<uidb64>/invalid-token/`.
   - Expected: `400 Bad Request`
6. `POST /api/token/refresh/` without refresh cookie.
   - Expected: `401 Unauthorized`
7. `POST /api/logout/` without access cookie.
   - Expected: `401 Unauthorized`

### Password Reset Happy Path

1. `POST /api/password_reset/` with an active user email.
   - Expected: `200 OK`
   - Expected reset email in Docker logs when `EMAIL_BACKEND` is console.
2. Open the reset link from the logs.
3. `POST /api/password_confirm/<uidb64>/<token>/` with matching secure passwords.
   - Expected: `200 OK`
4. `POST /api/login/` with the new password.
   - Expected: `200 OK`

### Password Reset Unhappy Path

1. `POST /api/password_reset/` with an unknown email.
   - Expected: `200 OK`
   - Reason: account existence is not exposed.
2. `POST /api/password_confirm/<uidb64>/<token>/` with mismatching passwords.
   - Expected: `400 Bad Request`
3. `POST /api/password_confirm/<uidb64>/invalid-token/` with valid passwords.
   - Expected: `400 Bad Request`

### Video Happy Path

1. Log in and keep cookies in Postman.
2. Upload a video in Django admin.
3. Watch Docker logs.
   - Expected: RQ worker starts processing.
4. Refresh the video in admin.
   - Expected: `processing_status` becomes `ready`.
5. `GET /api/video/`.
   - Expected: `200 OK`
   - Expected: uploaded video appears in the list.
6. `GET /api/video/<movie_id>/480p/index.m3u8`.
   - Expected: `200 OK`
   - Expected content type: `application/vnd.apple.mpegurl`
7. `GET /api/video/<movie_id>/480p/segment_000.ts`.
   - Expected: `200 OK`
   - Expected content type: `video/MP2T`
8. Repeat manifest check for `720p` and `1080p`.
   - Expected: `200 OK`

### Video Unhappy Path

1. `GET /api/video/` without login cookies.
   - Expected: `401 Unauthorized`
2. `GET /api/video/9999/480p/index.m3u8`.
   - Expected: `404 Not Found`
3. `GET /api/video/<movie_id>/240p/index.m3u8`.
   - Expected: `404 Not Found`
4. `GET /api/video/<movie_id>/480p/not-a-segment.txt`.
   - Expected: `404 Not Found`
5. Upload an invalid video file in admin.
   - Expected: background job fails.
   - Expected admin status: `failed`

## Useful Commands

Run Django checks inside Docker:

```powershell
docker compose exec -T web python manage.py check
```

Check for pending migrations:

```powershell
docker compose exec -T web python manage.py makemigrations --check --dry-run
```

Open a Django shell:

```powershell
docker compose exec web python manage.py shell
```

Open a container shell:

```powershell
docker compose exec web sh
```

Show web logs:

```powershell
docker compose logs -f web
```

Restart only the backend container:

```powershell
docker compose restart web
```

Stop all containers:

```powershell
docker compose down
```