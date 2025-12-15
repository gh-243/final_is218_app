#!/bin/bash
# Quick validation script for web authentication refactoring

echo "🔍 Validating Web Authentication Refactoring..."
echo ""

# Check that all necessary files exist
echo "1. Checking file existence..."
if [ -f "app/auth/dependencies.py" ]; then
    echo "   ✅ app/auth/dependencies.py exists"
else
    echo "   ❌ app/auth/dependencies.py missing"
    exit 1
fi

if [ -f "app/routers/queue_insights.py" ]; then
    echo "   ✅ app/routers/queue_insights.py exists"
else
    echo "   ❌ app/routers/queue_insights.py missing"
    exit 1
fi

# Check that get_current_web_user function exists
echo ""
echo "2. Checking get_current_web_user function..."
if grep -q "def get_current_web_user" app/auth/dependencies.py; then
    echo "   ✅ get_current_web_user function defined"
else
    echo "   ❌ get_current_web_user function not found"
    exit 1
fi

# Check that queue_insights router imports the new dependency
echo ""
echo "3. Checking queue_insights imports..."
if grep -q "from app.auth.dependencies import.*get_current_web_user" app/routers/queue_insights.py; then
    echo "   ✅ get_current_web_user imported in queue_insights router"
else
    echo "   ❌ get_current_web_user not imported in queue_insights router"
    exit 1
fi

# Check that web routes use try-except with get_current_web_user
echo ""
echo "4. Checking web route authentication patterns..."

# Count how many routes call get_current_web_user
web_user_calls=$(grep -c "get_current_web_user(request)" app/routers/queue_insights.py)
if [ "$web_user_calls" -ge 4 ]; then
    echo "   ✅ Found $web_user_calls calls to get_current_web_user (expected 4)"
else
    echo "   ❌ Only found $web_user_calls calls to get_current_web_user (expected 4)"
    exit 1
fi

# Check that RedirectResponse is used for redirects
redirect_count=$(grep -c "RedirectResponse(url=\"/login\"" app/routers/queue_insights.py)
if [ "$redirect_count" -ge 4 ]; then
    echo "   ✅ Found $redirect_count RedirectResponse to /login (expected 4)"
else
    echo "   ❌ Only found $redirect_count RedirectResponse to /login (expected 4)"
    exit 1
fi

# Check that API routes still use get_current_active_user
echo ""
echo "5. Checking API routes still use correct authentication..."
api_auth_count=$(grep -c "Depends(get_current_active_user)" app/routers/queue_insights.py)
if [ "$api_auth_count" -ge 2 ]; then
    echo "   ✅ Found $api_auth_count API routes using get_current_active_user"
else
    echo "   ❌ API routes may have been modified incorrectly"
    exit 1
fi

# Check that the dependency function checks cookies
echo ""
echo "6. Checking cookie support in get_current_web_user..."
if grep -q "request.cookies.get" app/auth/dependencies.py; then
    echo "   ✅ Cookie authentication implemented"
else
    echo "   ❌ Cookie authentication not found"
    exit 1
fi

# Check that Authorization header is also checked
if grep -q "request.headers.get.*Authorization" app/auth/dependencies.py; then
    echo "   ✅ Authorization header check implemented"
else
    echo "   ❌ Authorization header check not found"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "✅ All validation checks passed!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Summary of changes:"
echo "  • Created get_current_web_user() dependency function"
echo "  • Updated 4 web routes to use web authentication"
echo "  • Preserved 2 API routes with API authentication"
echo "  • Added cookie and header token checking"
echo "  • Implemented redirect to /login for unauthenticated users"
echo ""
echo "Next steps:"
echo "  1. Review the changes in WEB_AUTH_REFACTORING.md"
echo "  2. Test locally with: docker-compose up --build"
echo "  3. Commit: git add . && git commit -m 'refactor: Add web auth for Queue Insights'"
echo "  4. Deploy: git push origin main && ./deploy.sh (on server)"
echo ""
