# Production Deployment Guide - AI Queue Insights

## 🎯 Overview

This guide will deploy the AI Queue Insights feature to production at:
**https://calc.gerardherrera.dev/queue-insights**

## ✅ Changes Made

### 1. Docker Compose Production Hardening
- ✅ Removed `--reload` flag (dev mode disabled)
- ✅ Added `restart: unless-stopped` to all services
- ✅ Added container names for easier debugging
- ✅ Configured `--workers 2` for production performance
- ✅ Connected web service to external `web` network for Caddy
- ✅ Added OpenAI API key env var (optional, commented out)

### 2. Router Registration
- ✅ Queue insights router already registered in `app/main.py`
- ✅ Routes available at `/queue-insights/*`
- ✅ Navigation menu updated in `templates/layout.html`

### 3. Network Configuration
- ✅ Web service attached to both `app-network` (internal) and `web` (Caddy)
- ✅ External network declared (must exist before deployment)

---

## 🚀 Deployment Steps

### **Step 1: Create External Network (One-Time Setup)**

On your production server, create the `web` network if it doesn't exist:

```bash
# Check if network exists
docker network ls | grep web

# If not exists, create it
docker network create web
```

### **Step 2: Verify Caddy Configuration**

Your Caddyfile should have this block for calc.gerardherrera.dev:

```caddy
calc.gerardherrera.dev {
    # Reverse proxy to FastAPI container
    reverse_proxy final_is218_app_web:8000
    
    # Enable compression
    encode gzip
    
    # Security headers
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
    
    # Logging
    log {
        output file /var/log/caddy/calc.gerardherrera.dev.log
        format json
    }
}
```

**Key Points:**
- Upstream is `final_is218_app_web:8000` (container name:port)
- Container name matches `docker-compose.yml`
- Both services on same `web` network

### **Step 3: Deploy the Application**

SSH into your production server and run:

```bash
# Navigate to project directory
cd /path/to/final_is218_app

# Pull latest code
git pull origin main

# Stop existing containers
docker compose down

# Rebuild images (picks up new code)
docker compose build --no-cache

# Start services in detached mode
docker compose up -d

# Wait for services to be healthy (30 seconds)
sleep 30

# Check service status
docker compose ps
```

Expected output:
```
NAME                       STATUS              PORTS
final_is218_app_web        Up (healthy)        0.0.0.0:8004->8000/tcp
final_is218_app_db         Up (healthy)        0.0.0.0:5432->5432/tcp
final_is218_app_pgadmin    Up                  0.0.0.0:5050->80/tcp
```

### **Step 4: Reload Caddy**

```bash
# Navigate to Caddy infrastructure directory
cd /path/to/infrastructure

# Reload Caddy configuration
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

Or if Caddy is not in compose:
```bash
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### **Step 5: Verify Deployment**

Run these commands to verify everything is working:

```bash
# 1. Check containers are running
docker compose -p final_is218_app ps

# 2. Check web container logs
docker logs final_is218_app_web --tail 50

# 3. Check database is ready
docker logs final_is218_app_db --tail 20 | grep "ready to accept connections"

# 4. Test health endpoint locally
docker exec final_is218_app_web curl -f http://localhost:8000/health

# 5. Test from host (if port exposed)
curl -f http://localhost:8004/health

# 6. Test through Caddy (from server)
curl -f https://calc.gerardherrera.dev/health

# 7. Test homepage
curl -sI https://calc.gerardherrera.dev/ | grep "200 OK"

# 8. Test queue insights endpoint
curl -sI https://calc.gerardherrera.dev/queue-insights | grep "200 OK"

# 9. Test login page
curl -sI https://calc.gerardherrera.dev/login | grep "200 OK"

# 10. Verify network connectivity
docker network inspect web | grep final_is218_app_web
```

---

## 🧪 Manual Testing Checklist

### From Your Browser

1. **Homepage**: https://calc.gerardherrera.dev/
   - ✅ Should load without errors
   - ✅ Login/Register links visible

2. **Login**: https://calc.gerardherrera.dev/login
   - ✅ Login form appears
   - ✅ Existing credentials work

3. **Dashboard**: https://calc.gerardherrera.dev/dashboard
   - ✅ Calculator interface loads
   - ✅ Navigation shows "Calculator" and "AI Queue Insights"

4. **Queue Insights**: https://calc.gerardherrera.dev/queue-insights
   - ✅ Dashboard loads
   - ✅ Shows "AI Queue Insights" header
   - ✅ "+ New Observation" button visible
   - ✅ "Generate Insights" button (if observations exist)

5. **Create Observation**: https://calc.gerardherrera.dev/queue-insights/new
   - ✅ Form appears
   - ✅ All fields present
   - ✅ Can submit and create observation

6. **Generate Insights**:
   - ✅ Click "Generate Insights" on dashboard
   - ✅ Insight appears (rule-based if no API key)
   - ✅ Badge shows "Rule-Based" or "AI-Generated"

---

## 🔧 Troubleshooting

### Issue: "Network web not found"

**Solution:**
```bash
docker network create web
docker compose up -d
```

### Issue: "Container name already in use"

**Solution:**
```bash
docker compose down
docker rm -f final_is218_app_web final_is218_app_db final_is218_app_pgadmin
docker compose up -d
```

### Issue: Caddy can't reach container

**Check:**
```bash
# Verify both services on web network
docker network inspect web

# Should show:
# - caddy (or your Caddy container name)
# - final_is218_app_web
```

**Fix:**
```bash
# Reconnect to network if needed
docker network connect web final_is218_app_web
```

### Issue: 502 Bad Gateway

**Causes:**
1. Container not running: `docker compose ps`
2. Wrong upstream name in Caddyfile (must be `final_is218_app_web:8000`)
3. Network issue: Both containers must be on `web` network

**Debug:**
```bash
# Check container is healthy
docker inspect final_is218_app_web | grep '"Status"'

# Check logs
docker logs final_is218_app_web --tail 100

# Test direct connection
docker exec caddy wget -O- http://final_is218_app_web:8000/health
```

### Issue: Database not initialized

**Solution:**
```bash
# Recreate database
docker compose down -v  # WARNING: Deletes data!
docker compose up -d
```

### Issue: Navigation menu not showing "AI Queue Insights"

**Causes:**
1. Not logged in (menu only shows for authenticated users)
2. JavaScript not loading (check browser console)
3. Template cache (hard refresh: Ctrl+Shift+R)

**Verify:**
```bash
# Check template file exists
docker exec final_is218_app_web ls -l /app/templates/queue_list.html
docker exec final_is218_app_web ls -l /app/templates/queue_form.html

# Check router is registered
docker exec final_is218_app_web python -c "from app.main import app; print([r.path for r in app.routes if 'queue' in r.path])"
```

---

## 📊 Monitoring

### Check Application Health

```bash
# Real-time logs
docker logs -f final_is218_app_web

# Check memory usage
docker stats final_is218_app_web --no-stream

# Check disk usage
docker system df
```

### Expected Resource Usage

- **Web Container**: ~100-200MB RAM
- **Database**: ~50-100MB RAM
- **Total**: ~150-300MB RAM (safe for low-memory servers)

---

## 🔐 Optional: Enable AI Mode

If you want to use OpenAI for insights (optional):

1. Get an OpenAI API key from https://platform.openai.com/api-keys

2. Add to `.env` file or docker-compose.yml:
   ```yaml
   environment:
     OPENAI_API_KEY: "sk-your-actual-key-here"
   ```

3. Restart the application:
   ```bash
   docker compose down
   docker compose up -d
   ```

4. Test by generating insights - should see "AI-Generated" badge

**Note:** Feature works perfectly without API key using rule-based fallback!

---

## 🎉 Success Criteria

Your deployment is successful when:

- ✅ https://calc.gerardherrera.dev/ loads
- ✅ Login/register works
- ✅ https://calc.gerardherrera.dev/queue-insights loads
- ✅ Navigation shows "AI Queue Insights" when logged in
- ✅ Can create observations
- ✅ Can generate insights (rule-based or AI)
- ✅ All services restart automatically (`restart: unless-stopped`)
- ✅ No manual `docker network connect` needed
- ✅ Survives server reboot

---

## 📋 Complete Deployment Sequence

Copy/paste this entire sequence on your production server:

```bash
#!/bin/bash
set -e  # Exit on error

echo "🚀 Deploying AI Queue Insights to Production"
echo "=============================================="

# Navigate to project
cd /path/to/final_is218_app

# Ensure external network exists
echo "📡 Checking network..."
docker network inspect web >/dev/null 2>&1 || docker network create web

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Stop and remove old containers
echo "🛑 Stopping old containers..."
docker compose down

# Rebuild with no cache
echo "🏗️  Building images..."
docker compose build --no-cache

# Start services
echo "🚀 Starting services..."
docker compose up -d

# Wait for health checks
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check status
echo "📊 Service status:"
docker compose ps

# Test health endpoint
echo "🏥 Testing health endpoint..."
docker exec final_is218_app_web curl -sf http://localhost:8000/health || echo "⚠️  Health check failed"

# Reload Caddy (adjust path as needed)
echo "🔄 Reloading Caddy..."
cd /path/to/infrastructure
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile || echo "⚠️  Caddy reload failed (may need manual reload)"

# Verify external access
echo "🌐 Testing external access..."
curl -sf https://calc.gerardherrera.dev/health && echo "✅ Health endpoint OK" || echo "❌ Health endpoint FAILED"
curl -sI https://calc.gerardherrera.dev/ | grep "200" && echo "✅ Homepage OK" || echo "❌ Homepage FAILED"
curl -sI https://calc.gerardherrera.dev/queue-insights | grep "200" && echo "✅ Queue Insights OK" || echo "❌ Queue Insights FAILED"

echo "=============================================="
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Visit https://calc.gerardherrera.dev/"
echo "2. Login with your credentials"
echo "3. Click 'AI Queue Insights' in the navigation"
echo "4. Add observations and generate insights!"
echo ""
echo "Logs: docker logs -f final_is218_app_web"
```

---

## 🔒 Security Notes

1. **Secrets Management**: Consider using Docker secrets or .env file for sensitive data
2. **Database Password**: Change default postgres password in production
3. **JWT Keys**: Use strong random keys (32+ characters)
4. **CORS**: Configure allowed origins if needed
5. **Rate Limiting**: Consider adding rate limiting to protect API

---

## 📝 Post-Deployment Tasks

- [ ] Test all user flows (register, login, dashboard, queue insights)
- [ ] Verify email addresses in user profiles
- [ ] Set up monitoring/alerting (optional)
- [ ] Configure backups for PostgreSQL data
- [ ] Update documentation with production URLs
- [ ] Share feature with users!

---

**Last Updated**: December 15, 2025  
**Service**: calc.gerardherrera.dev  
**Feature**: AI Queue Insights  
**Status**: Ready for Production ✅
