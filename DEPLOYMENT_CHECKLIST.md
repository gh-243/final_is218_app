# 🚀 Production Deployment Checklist

## Pre-Deployment (Run Locally)

- [x] Feature code implemented
- [x] Router registered in `app/main.py`
- [x] Navigation menu updated
- [x] Docker compose hardened (no --reload)
- [x] External network configured
- [x] Container names set
- [x] Restart policies added
- [x] Pre-deployment check passes
- [ ] Code pushed to git main branch

```bash
# Run this locally before deploying:
./pre-deploy-check.sh
git add .
git commit -m "feat: Add AI Queue Insights feature for production"
git push origin main
```

---

## Server Deployment (Run on Production Server)

### Quick Deploy (Recommended)

```bash
# SSH to server
ssh user@your-server

# Navigate to project
cd /path/to/final_is218_app

# Run automated deployment
./deploy.sh
```

### Manual Deploy (Step-by-Step)

- [ ] **Step 1:** Create external network
```bash
docker network create web
```

- [ ] **Step 2:** Pull latest code
```bash
git pull origin main
```

- [ ] **Step 3:** Stop containers
```bash
docker compose down
```

- [ ] **Step 4:** Build images
```bash
docker compose build --no-cache
```

- [ ] **Step 5:** Start services
```bash
docker compose up -d
```

- [ ] **Step 6:** Verify health
```bash
sleep 30
docker compose ps
docker exec final_is218_app_web curl -f http://localhost:8000/health
```

- [ ] **Step 7:** Reload Caddy
```bash
# Adjust path to your infrastructure directory
cd /path/to/infrastructure
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
```

---

## Caddy Configuration

- [ ] **Verify Caddyfile has correct config:**

```caddy
calc.gerardherrera.dev {
    reverse_proxy final_is218_app_web:8000
    encode gzip
    
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
    }
    
    log {
        output file /var/log/caddy/calc.gerardherrera.dev.log
        format json
    }
}
```

**Critical:**
- Upstream: `final_is218_app_web:8000` (matches container_name)
- Both containers on `web` network

---

## Verification (After Deployment)

### Docker Checks

- [ ] Containers running
```bash
docker compose ps
# Expected: All services "Up" or "Up (healthy)"
```

- [ ] Web container healthy
```bash
docker logs final_is218_app_web --tail 50
# Should see: "Application startup complete"
```

- [ ] Database ready
```bash
docker logs final_is218_app_db --tail 20
# Should see: "database system is ready to accept connections"
```

- [ ] Network connectivity
```bash
docker network inspect web | grep final_is218_app_web
# Should show the container in the network
```

### HTTP Checks

- [ ] Health endpoint
```bash
curl -f https://calc.gerardherrera.dev/health
# Expected: {"status":"healthy"}
```

- [ ] Homepage (200 OK)
```bash
curl -sI https://calc.gerardherrera.dev/ | grep "200"
```

- [ ] Login page (200 OK)
```bash
curl -sI https://calc.gerardherrera.dev/login | grep "200"
```

- [ ] Queue Insights (200 OK)
```bash
curl -sI https://calc.gerardherrera.dev/queue-insights | grep "200"
```

### Browser Tests

- [ ] Visit https://calc.gerardherrera.dev/
  - Page loads without errors
  - HTTPS certificate valid
  - Login/Register links visible

- [ ] Test existing authentication
  - Login with existing account works
  - Redirects to dashboard
  - Existing calculator features work

- [ ] Test navigation menu
  - Shows "Calculator" link
  - Shows "AI Queue Insights" link
  - Links work and route correctly

- [ ] Test Queue Insights dashboard
  - https://calc.gerardherrera.dev/queue-insights loads
  - Shows "AI Queue Insights" header
  - Shows welcome/instructions
  - "+ New Observation" button visible
  - No JavaScript errors in console

- [ ] Test creating observation
  - Click "+ New Observation"
  - Form loads at /queue-insights/new
  - Fill in form:
    - Department: "Emergency Room"
    - Date/time: current
    - Patients: 15
    - Wait time: 45
    - Notes: "Test observation"
  - Submit form
  - Redirects to dashboard
  - Success message appears
  - Observation appears in table

- [ ] Test insight generation
  - Add 2-3 more observations (vary departments/wait times)
  - Click "Generate Insights" button
  - Insight appears in blue card at top
  - Badge shows "Rule-Based" (if no API key)
  - Insight text is readable and relevant
  - Metadata shows observation count

### User Scoping Test

- [ ] Create observations as User A
- [ ] Logout
- [ ] Login as User B (or register new user)
- [ ] Navigate to /queue-insights
- [ ] Verify User B does NOT see User A's observations
- [ ] Create observations as User B
- [ ] Verify User B only sees own observations

---

## Performance Checks

- [ ] Memory usage acceptable
```bash
docker stats final_is218_app_web --no-stream
# Should be ~150-200MB RAM
```

- [ ] Database size reasonable
```bash
docker exec final_is218_app_db psql -U postgres -d fastapi_db -c "SELECT pg_size_pretty(pg_database_size('fastapi_db'));"
```

- [ ] Logs not filling disk
```bash
docker system df
```

---

## Restart & Reboot Tests

- [ ] Test container restart
```bash
docker restart final_is218_app_web
sleep 10
curl -f https://calc.gerardherrera.dev/health
# Should recover and return healthy
```

- [ ] Test full restart
```bash
docker compose restart
sleep 30
curl -f https://calc.gerardherrera.dev/queue-insights
# Should work without manual intervention
```

- [ ] Verify auto-restart policy
```bash
docker inspect final_is218_app_web | grep -A 5 RestartPolicy
# Should show: "Name": "unless-stopped"
```

- [ ] Test server reboot (if possible)
```bash
sudo reboot
# After reboot:
docker compose ps
curl -f https://calc.gerardherrera.dev/health
# Should auto-start without manual intervention
```

---

## Security Checks

- [ ] HTTPS working
```bash
curl -I https://calc.gerardherrera.dev/ | grep "strict-transport-security"
```

- [ ] HTTP redirects to HTTPS
```bash
curl -I http://calc.gerardherrera.dev/ | grep "301\|308"
```

- [ ] Authentication required for /queue-insights
  - Visit in private/incognito window (not logged in)
  - Should redirect to login or show auth error

- [ ] User data isolation verified (see User Scoping Test above)

- [ ] SQL injection protected (using ORM)

- [ ] XSS protected (Jinja2 auto-escaping)

---

## Optional: Enable AI Mode

- [ ] Get OpenAI API key from https://platform.openai.com/

- [ ] Add to docker-compose.yml
```yaml
environment:
  OPENAI_API_KEY: "sk-your-key-here"
```

- [ ] Restart services
```bash
docker compose down
docker compose up -d
```

- [ ] Test AI insights
  - Generate insights
  - Verify badge shows "AI-Generated"
  - Verify natural language output

---

## Documentation

- [ ] Update internal docs with production URL
- [ ] Share feature announcement with users
- [ ] Document any production-specific configurations
- [ ] Note any deviations from standard setup

---

## Rollback Plan (If Issues)

If deployment fails, rollback:

```bash
# 1. Stop new version
docker compose down

# 2. Revert code
git checkout HEAD~1

# 3. Rebuild old version
docker compose build --no-cache
docker compose up -d

# 4. Verify old version works
curl -f https://calc.gerardherrera.dev/health
```

---

## Post-Deployment

- [ ] Monitor logs for errors
```bash
docker logs -f final_is218_app_web
```

- [ ] Check error rates
```bash
docker logs final_is218_app_web | grep -i error | tail -20
```

- [ ] Verify no performance degradation
```bash
docker stats --no-stream
```

- [ ] Test all major user flows:
  - [ ] User registration
  - [ ] User login
  - [ ] Calculator operations
  - [ ] Queue observations
  - [ ] Insight generation

- [ ] Announce feature to users
  - New feature available at /queue-insights
  - Instructions for use
  - Expected behavior (rule-based by default)

---

## Success Criteria

✅ **Deployment is successful when ALL of these are true:**

- [x] Pre-deployment check passes locally
- [ ] Code pushed to git main
- [ ] All containers running on server
- [ ] Health endpoint returns 200
- [ ] Homepage accessible via HTTPS
- [ ] Login/register works (existing functionality)
- [ ] Calculator works (existing functionality)
- [ ] Queue Insights accessible at /queue-insights
- [ ] Navigation shows "AI Queue Insights" when logged in
- [ ] Can create observations
- [ ] Can generate insights (rule-based or AI)
- [ ] User data is properly scoped
- [ ] No errors in docker logs
- [ ] No errors in browser console
- [ ] Survives container restart
- [ ] Survives server reboot (auto-starts)
- [ ] Memory usage < 300MB total
- [ ] Response times < 2 seconds

---

## Final Sign-Off

- [ ] All checks passed
- [ ] Feature tested by developer
- [ ] Feature tested by another user
- [ ] Documentation updated
- [ ] Users notified

**Deployed By:** ________________  
**Date:** ________________  
**Time:** ________________  
**Status:** ⬜ Success  ⬜ Failed  ⬜ Rolled Back

**Notes:**
_______________________________________________________
_______________________________________________________
_______________________________________________________

---

**Reference Documents:**
- Full deployment guide: `PRODUCTION_DEPLOY.md`
- Quick summary: `DEPLOY_SUMMARY.md`
- Caddy config: `Caddyfile.reference`
- Automated script: `deploy.sh`
- Pre-flight check: `pre-deploy-check.sh`
