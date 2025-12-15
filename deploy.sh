#!/bin/bash
# Production Deployment Script for AI Queue Insights
# Run this on your production server to deploy the feature

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  AI Queue Insights - Production Deployment Script     ║${NC}"
echo -e "${BLUE}║  Service: calc.gerardherrera.dev                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}⚠️  Warning: Running as root. Consider using a non-root user.${NC}"
fi

# Ensure we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found!${NC}"
    echo "Please cd to the project directory first."
    exit 1
fi

# Step 1: Ensure external network exists
echo -e "${BLUE}[1/9]${NC} Checking Docker network..."
if docker network inspect web >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Network 'web' exists${NC}"
else
    echo -e "${YELLOW}⚡ Creating network 'web'...${NC}"
    docker network create web
    echo -e "${GREEN}✅ Network created${NC}"
fi

# Step 2: Pull latest code
echo ""
echo -e "${BLUE}[2/9]${NC} Pulling latest code from git..."
git pull origin main || {
    echo -e "${YELLOW}⚠️  Git pull failed or no changes${NC}"
}

# Step 3: Stop existing containers
echo ""
echo -e "${BLUE}[3/9]${NC} Stopping existing containers..."
docker compose down

# Step 4: Clean up old images (optional, saves space)
echo ""
echo -e "${BLUE}[4/9]${NC} Cleaning up old images..."
docker image prune -f

# Step 5: Build fresh images
echo ""
echo -e "${BLUE}[5/9]${NC} Building Docker images..."
docker compose build --no-cache

# Step 6: Start services
echo ""
echo -e "${BLUE}[6/9]${NC} Starting services..."
docker compose up -d

# Step 7: Wait for services to be healthy
echo ""
echo -e "${BLUE}[7/9]${NC} Waiting for services to be healthy..."
sleep 5
for i in {1..30}; do
    if docker exec final_is218_app_web curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Services are healthy${NC}"
        break
    fi
    echo -n "."
    sleep 2
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  Health check timeout (but may still be starting)${NC}"
    fi
done

# Step 8: Show service status
echo ""
echo -e "${BLUE}[8/9]${NC} Service status:"
docker compose ps

# Step 9: Reload Caddy
echo ""
echo -e "${BLUE}[9/9]${NC} Reloading Caddy..."
# Try multiple possible Caddy locations
if docker compose -f ../infrastructure/docker-compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null; then
    echo -e "${GREEN}✅ Caddy reloaded (method 1)${NC}"
elif docker exec caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null; then
    echo -e "${GREEN}✅ Caddy reloaded (method 2)${NC}"
else
    echo -e "${YELLOW}⚠️  Could not reload Caddy automatically. Reload manually:${NC}"
    echo "   docker exec caddy caddy reload --config /etc/caddy/Caddyfile"
fi

# Verification
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Running verification checks..."
echo ""

# Test health endpoint
echo -n "Health endpoint: "
if curl -sf https://calc.gerardherrera.dev/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test homepage
echo -n "Homepage:        "
if curl -sI https://calc.gerardherrera.dev/ 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test queue insights
echo -n "Queue Insights:  "
if curl -sI https://calc.gerardherrera.dev/queue-insights 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

# Test login
echo -n "Login page:      "
if curl -sI https://calc.gerardherrera.dev/login 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${RED}❌ FAILED${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "🌐 URLs:"
echo "   Homepage:       https://calc.gerardherrera.dev/"
echo "   Login:          https://calc.gerardherrera.dev/login"
echo "   Queue Insights: https://calc.gerardherrera.dev/queue-insights"
echo ""
echo "📊 Monitoring:"
echo "   Logs:    docker logs -f final_is218_app_web"
echo "   Status:  docker compose ps"
echo "   Health:  curl https://calc.gerardherrera.dev/health"
echo ""
echo "🔧 Next Steps:"
echo "   1. Test login at https://calc.gerardherrera.dev/login"
echo "   2. Click 'AI Queue Insights' in navigation"
echo "   3. Add observations and generate insights"
echo ""
echo -e "${GREEN}✨ Feature is now LIVE!${NC}"
echo ""
