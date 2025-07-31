# Render.com Deployment Guide

This guide covers deploying the Book Club Backend to Render.com with automatic seeding capabilities.

## Quick Setup

1. **Fork/Clone** this repository to your GitHub account
2. **Connect** your repository to Render.com
3. **Deploy** using the provided `render.yaml` configuration
4. **Configure** environment variables as needed

## Files Overview

### render-build.sh
This is the main build script that Render.com will execute during deployment. It:
- Installs dependencies
- Runs database migrations
- Collects static files
- Conditionally seeds the database based on `SEED_ON_STARTUP` setting

### render.yaml
This is the Render.com configuration file that defines:
- PostgreSQL database service
- Django web service with environment variables
- Build and start commands

## Environment Variables

### Required Variables (Auto-configured by render.yaml)
- `DATABASE_URL` - Persistent PostgreSQL connection string (auto-populated from database service)
- `SECRET_KEY` - Django secret key (auto-generated)
- `PYTHON_VERSION` - Python version (3.12.3)
- `DEBUG` - Debug mode (False for production)
- `ALLOWED_HOSTS` - Allowed hosts (set to "*" for flexibility)

### Optional Variables
- `SEED_ON_STARTUP` - Whether to seed database on deployment (default: "false")
- `CORS_ALLOWED_ORIGINS` - Frontend domains for CORS (update with your frontend URL)

## Database Configuration

The `render.yaml` file automatically configures:
1. **PostgreSQL Service**: A persistent PostgreSQL database
2. **DATABASE_URL**: Automatically populated connection string pointing to the persistent database
3. **Connection Persistence**: `conn_max_age=600` for connection pooling

The database will persist across deployments, ensuring data integrity.

## Seeding Configuration

### Automatic Seeding
Set `SEED_ON_STARTUP=true` in Render dashboard to enable automatic seeding during deployment:

```bash
# In Render dashboard environment variables
SEED_ON_STARTUP=true
```

This will run `python manage.py master_seed --level=production` during build.

### Manual Seeding
For manual control, keep `SEED_ON_STARTUP=false` (default) and seed manually:

1. **Via Render Shell**:
   ```bash
   python manage.py master_seed --level=production
   ```

2. **Via Manual Deploy** with custom build command:
   ```bash
   python manage.py master_seed --level=production --reset
   ```

### Seeding Levels
- `basic`: Minimal data (10 users, 20 books, 5 clubs)
- `full`: Complete dataset (50 users, 100 books, 15 clubs)  
- `production`: Optimized for production (25 users, 50 books, 8 clubs)

## Avoiding Data Duplication

### On Re-seeding
To re-seed without duplicates:

1. **Method 1 - Reset Flag**:
   ```bash
   python manage.py master_seed --level=production --reset
   ```
   This flushes existing data before seeding.

2. **Method 2 - Manual Deploy**:
   - Go to Render dashboard
   - Navigate to your service
   - Click "Manual Deploy"
   - Set build command: `python manage.py master_seed --level=production --reset`

### Database Persistence
- The PostgreSQL database persists across deployments
- `DATABASE_URL` points to the same persistent database instance
- Data is only reset when explicitly using `--reset` flag

## Deployment Steps

### First-Time Deployment

1. **Prepare Repository**:
   ```bash
   git add render.yaml render-build.sh
   git commit -m "Add Render deployment configuration"
   git push origin main
   ```

2. **Create Render Service**:
   - Go to [render.com](https://render.com)
   - Connect your GitHub repository
   - Render will automatically detect `render.yaml`
   - Click "Apply" to create services

3. **Configure Environment** (optional):
   - Update `CORS_ALLOWED_ORIGINS` with your frontend URL
   - Set `SEED_ON_STARTUP=true` if you want automatic seeding

4. **Deploy**:
   - Render will automatically build and deploy
   - Monitor build logs for seeding progress

### Subsequent Deployments

Regular deployments will:
- Run migrations automatically
- Preserve database data
- Skip seeding (unless `SEED_ON_STARTUP=true`)

## Manual Operations

### Shell Access
Access your deployed application shell:
```bash
# Via Render dashboard shell
python manage.py shell
```

### Database Operations
```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Seed database
python manage.py master_seed --level=production

# Reset and seed
python manage.py master_seed --level=production --reset
```

### Monitoring
Monitor your deployment:
- **Logs**: Check Render dashboard logs for deployment status
- **Health**: Access your deployed URL to verify functionality
- **Database**: Monitor database connections and performance

## Troubleshooting

### Build Failures
- Check `render-build.sh` permissions: `chmod +x render-build.sh`
- Verify `requirements.txt` contains all dependencies
- Check Python version compatibility

### Database Issues
- Verify `DATABASE_URL` is properly set
- Check PostgreSQL service is running
- Monitor connection limits

### Seeding Problems
- Check individual seed commands work: `python manage.py seed_users --count=5`
- Verify data models and migrations are up to date
- Use `--reset` flag to clear problematic data

### CORS Issues
- Update `CORS_ALLOWED_ORIGINS` with your actual frontend domain
- Ensure URLs include protocol (https://)
- Check that frontend is making requests to correct backend URL

## Production Recommendations

### Security
- Never set `DEBUG=True` in production
- Use strong `SECRET_KEY` (auto-generated by Render)
- Configure proper `ALLOWED_HOSTS`
- Set up proper CORS origins

### Performance
- Monitor database connection usage
- Consider upgrading database plan for heavy usage
- Use CDN for static files if needed
- Monitor application performance metrics

### Maintenance
- Regular database backups (Render handles this for PostgreSQL)
- Monitor logs for errors
- Keep dependencies updated
- Test deployments in staging environment first

## Support

For issues specific to:
- **Render platform**: Check [Render documentation](https://render.com/docs)
- **Django deployment**: Check [Django deployment docs](https://docs.djangoproject.com/en/stable/howto/deployment/)
- **This application**: Check repository issues or create new issue

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Auto-generated | PostgreSQL connection string |
| `SECRET_KEY` | Auto-generated | Django secret key |
| `DEBUG` | `False` | Django debug mode |
| `ALLOWED_HOSTS` | `*` | Allowed host names |
| `CORS_ALLOWED_ORIGINS` | Your frontend URL | CORS allowed origins |
| `SEED_ON_STARTUP` | `false` | Enable automatic seeding |
| `PYTHON_VERSION` | `3.12.3` | Python version |

Update the `CORS_ALLOWED_ORIGINS` value in `render.yaml` with your actual frontend domain before deploying.
