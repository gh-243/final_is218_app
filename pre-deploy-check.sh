#!/bin/bash
# Pre-Deployment Checklist Script
# Run this BEFORE deploying to catch issues early

echo "🔍 Pre-Deployment Checklist for AI Queue Insights"
echo "=================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check and report
check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
        ERRORS=$((ERRORS + 1))
    fi
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    WARNINGS=$((WARNINGS + 1))
}

info() {
    echo -e "ℹ️  $1"
}

echo "1️⃣  Checking Required Files"
echo "----------------------------"

# Check router file exists
if [ -f "app/routers/queue_insights.py" ]; then
    check 0 "Router file exists"
else
    check 1 "Router file missing: app/routers/queue_insights.py"
fi

# Check model file exists
if [ -f "app/models/queue_observation.py" ]; then
    check 0 "Model file exists"
else
    check 1 "Model file missing: app/models/queue_observation.py"
fi

# Check schema file exists
if [ -f "app/schemas/queue_observation.py" ]; then
    check 0 "Schema file exists"
else
    check 1 "Schema file missing: app/schemas/queue_observation.py"
fi

# Check service file exists
if [ -f "app/services/queue_insights.py" ]; then
    check 0 "Service file exists"
else
    check 1 "Service file missing: app/services/queue_insights.py"
fi

# Check templates exist
if [ -f "templates/queue_list.html" ]; then
    check 0 "Dashboard template exists"
else
    check 1 "Template missing: templates/queue_list.html"
fi

if [ -f "templates/queue_form.html" ]; then
    check 0 "Form template exists"
else
    check 1 "Template missing: templates/queue_form.html"
fi

echo ""
echo "2️⃣  Checking Code Integration"
echo "------------------------------"

# Check router is imported in main.py
if grep -q "from app.routers import queue_insights" app/main.py; then
    check 0 "Router imported in main.py"
else
    check 1 "Router NOT imported in main.py"
fi

# Check router is registered
if grep -q "app.include_router(queue_insights.router)" app/main.py; then
    check 0 "Router registered in main.py"
else
    check 1 "Router NOT registered in main.py"
fi

# Check models are imported
if grep -q "from app.models.queue_observation import" app/main.py; then
    check 0 "Models imported in main.py"
else
    warn "Models not imported in main.py (may be OK if imported elsewhere)"
fi

# Check User model has relationships
if grep -q "queue_observations" app/models/user.py; then
    check 0 "User model has queue_observations relationship"
else
    check 1 "User model missing queue_observations relationship"
fi

# Check navigation menu updated
if grep -q "queue-insights" templates/layout.html; then
    check 0 "Navigation menu includes queue insights link"
else
    check 1 "Navigation menu missing queue insights link"
fi

echo ""
echo "3️⃣  Checking Docker Configuration"
echo "----------------------------------"

# Check docker-compose.yml exists
if [ -f "docker-compose.yml" ]; then
    check 0 "docker-compose.yml exists"
    
    # Check no --reload flag
    if grep -v "^[[:space:]]*#" docker-compose.yml | grep -q "\-\-reload"; then
        check 1 "docker-compose.yml still has --reload flag (dev mode)"
    else
        check 0 "Production mode enabled (no --reload)"
    fi
    
    # Check restart policy
    if grep -q "restart: unless-stopped" docker-compose.yml; then
        check 0 "Restart policy configured"
    else
        warn "No restart policy found (containers won't auto-restart)"
    fi
    
    # Check external network
    if grep -q "external: true" docker-compose.yml; then
        check 0 "External 'web' network configured"
    else
        check 1 "External 'web' network NOT configured"
    fi
    
    # Check container name
    if grep -q "container_name: final_is218_app_web" docker-compose.yml; then
        check 0 "Container name set for Caddy routing"
    else
        warn "Container name not set (may cause routing issues)"
    fi
else
    check 1 "docker-compose.yml missing"
fi

echo ""
echo "4️⃣  Checking Dependencies"
echo "-------------------------"

# Check requirements.txt includes openai
if [ -f "requirements.txt" ]; then
    if grep -q "openai" requirements.txt; then
        check 0 "OpenAI package in requirements.txt"
    else
        warn "OpenAI package not in requirements.txt (will use rule-based fallback)"
    fi
else
    check 1 "requirements.txt missing"
fi

echo ""
echo "5️⃣  Checking Documentation"
echo "--------------------------"

# Check deployment docs exist
if [ -f "PRODUCTION_DEPLOY.md" ]; then
    check 0 "Deployment documentation exists"
else
    warn "PRODUCTION_DEPLOY.md missing (nice to have)"
fi

if [ -f "AI_QUEUE_INSIGHTS.md" ]; then
    check 0 "Feature documentation exists"
else
    warn "AI_QUEUE_INSIGHTS.md missing (nice to have)"
fi

if [ -f "QUICKSTART.md" ]; then
    check 0 "Quick start guide exists"
else
    warn "QUICKSTART.md missing (nice to have)"
fi

echo ""
echo "6️⃣  Environment Check"
echo "---------------------"

# Check if .env exists
if [ -f ".env" ]; then
    info ".env file exists"
    
    # Check for critical env vars
    if grep -q "DATABASE_URL" .env 2>/dev/null || grep -q "DATABASE_URL" docker-compose.yml; then
        check 0 "DATABASE_URL configured"
    else
        warn "DATABASE_URL not found (may be using defaults)"
    fi
    
    if grep -q "JWT_SECRET_KEY" .env 2>/dev/null || grep -q "JWT_SECRET_KEY" docker-compose.yml; then
        check 0 "JWT_SECRET_KEY configured"
    else
        check 1 "JWT_SECRET_KEY not configured"
    fi
    
    if grep -q "OPENAI_API_KEY" .env 2>/dev/null; then
        info "OPENAI_API_KEY found (AI mode enabled)"
    else
        info "OPENAI_API_KEY not found (will use rule-based fallback)"
    fi
else
    warn ".env file not found (using docker-compose.yml env vars)"
fi

echo ""
echo "=================================================="
echo "📊 Summary"
echo "=================================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED!${NC}"
    echo "Ready for deployment 🚀"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS WARNING(S)${NC}"
    echo "Deployment possible but review warnings"
    exit 0
else
    echo -e "${RED}❌ $ERRORS ERROR(S), $WARNINGS WARNING(S)${NC}"
    echo "Fix errors before deploying!"
    exit 1
fi
