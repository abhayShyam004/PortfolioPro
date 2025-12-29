# PortfolioPro - Multi-Tenant SaaS Portfolio Platform

A secure, multi-user portfolio platform built with Django, featuring subdomain-based tenancy, JWT authentication, and extensive customization options.

## Features

- **Multi-Tenant Architecture**: Each user gets their own subdomain (e.g., `username.portfoliopro.site`)
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Custom User Model**: Roles (USER, SUPERADMIN), subdomain assignment, ban/activate
- **Portfolio Sections**: Profile, Skills, Projects, Experience, Education, Custom Sections
- **Theme Customization**: Colors, fonts, button styles, background effects
- **Superadmin Panel**: User management, impersonation, platform statistics
- **Security Hardened**: CSRF, XSS, clickjacking protection, HSTS, CSP
- **Docker Ready**: Production deployment with PostgreSQL, Redis, Nginx

## Quick Start

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd portfolio/resume

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# (Optional) Load theme presets
python manage.py preload_themes

# Run development server
python manage.py runserver
```

### Access Points

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/` | Main portfolio page |
| `http://127.0.0.1:8000/?subdomain=username` | View specific user's portfolio (dev mode) |
| `http://127.0.0.1:8000/admin-login/` | Admin panel login |
| `http://127.0.0.1:8000/admin-panel/` | Portfolio management |
| `http://127.0.0.1:8000/superadmin/` | Superadmin dashboard (requires SUPERADMIN role) |
| `http://127.0.0.1:8000/health/` | Health check endpoint |

## Production Deployment

### Docker Deployment

```bash
# Copy and configure environment
cp .env.docker.example .env.docker
# Edit .env.docker with production values

# Build and start services
docker-compose up -d --build

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Load theme presets
docker-compose exec web python manage.py preload_themes
```

### Wildcard DNS Setup

For subdomain routing to work in production:

1. **DNS Configuration**: Add a wildcard A record:
   ```
   *.portfoliopro.site -> your-server-ip
   portfoliopro.site -> your-server-ip
   ```

2. **SSL Certificate**: Use Let's Encrypt with wildcard:
   ```bash
   certbot certonly --manual --preferred-challenges=dns \
     -d portfoliopro.site -d *.portfoliopro.site
   ```

3. **Nginx**: The included `nginx/nginx.conf` handles wildcard subdomains

## API Reference

### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register/` | POST | Register new user |
| `/api/auth/login/` | POST | Get JWT tokens |
| `/api/auth/token/refresh/` | POST | Refresh access token |
| `/api/auth/logout/` | POST | Blacklist refresh token |
| `/api/auth/profile/` | GET/PUT | View/update profile |
| `/api/auth/check-subdomain/` | GET | Check subdomain availability |

### Portfolio Management (requires auth)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/profile/update/` | POST | Update profile info |
| `/api/skill/add/` | POST | Add skill |
| `/api/skill/<id>/update/` | POST | Update skill |
| `/api/skill/<id>/delete/` | POST | Delete skill |
| `/api/project/add/` | POST | Add project |
| `/api/project/<id>/update/` | POST | Update project |
| `/api/project/<id>/delete/` | POST | Delete project |
| `/api/appearance/update/` | POST | Update theme settings |

### Superadmin Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/superadmin/` | GET | Dashboard |
| `/superadmin/users/` | GET | User list |
| `/superadmin/users/<id>/` | GET | User detail |
| `/superadmin/users/<id>/ban/` | POST | Ban user |
| `/superadmin/users/<id>/unban/` | POST | Unban user |
| `/superadmin/users/<id>/impersonate/` | POST | Login as user |

## Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test app

# Run with coverage
pip install coverage
coverage run manage.py test
coverage report
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | (required) |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Allowed hosts | `localhost` |
| `MAIN_DOMAIN` | Base domain for subdomains | `portfoliopro.site` |
| `DATABASE_URL` | Database connection URL | SQLite |
| `REDIS_URL` | Redis connection URL | None (LocMem cache) |

## Project Structure

```
resume/
├── accounts/          # Custom user model & auth
│   ├── models.py      # User model with roles
│   ├── views.py       # Auth API views
│   └── serializers.py # DRF serializers
├── app/               # Portfolio application
│   ├── models.py      # Portfolio models (user-scoped)
│   ├── views.py       # Portfolio & admin views
│   ├── middleware.py  # Subdomain middleware
│   ├── cache.py       # Cache utilities
│   └── permissions.py # Object-level permissions
├── superadmin/        # Platform administration
│   ├── views.py       # User management
│   └── templates/     # Admin UI
├── nginx/             # Nginx configuration
├── Dockerfile         # Multi-stage build
└── docker-compose.yml # Service orchestration
```

## Security Features

- **CSRF Protection**: Secure cookies, trusted origins
- **XSS Protection**: Browser XSS filter, content type sniffing prevention
- **Clickjacking**: X-Frame-Options: DENY
- **HTTPS**: SSL redirect, HSTS in production
- **Rate Limiting**: DRF throttling + Nginx rate limits
- **Secure Cookies**: HttpOnly, SameSite, Secure flags
- **JWT Security**: Token expiration, refresh rotation, blacklisting

## License

MIT License - see LICENSE file for details.
