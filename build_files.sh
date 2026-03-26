#!/bin/bash

# Build script for Vercel deployment with tenant migrations
echo "=========================================="
echo "Building Portals"
echo "=========================================="

# Install dependencies
echo ""
echo "[1/7] Installing dependencies..."
python3 -m pip install -r requirements.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}

# Collect static files
echo ""
echo "[2/7] Collecting static files..."
python3 manage.py collectstatic --noinput --clear || {
    echo "❌ Failed to collect static files"
    exit 1
}

# Validate admin static/css reachability before migrations
echo ""
echo "[3/7] Verifying Django admin static assets..."
python3 scripts/check_admin_static.py || {
    echo "❌ Admin static verification failed"
    exit 1
}

# Run migrations - Public schema first
echo ""
echo "[4/7] Migrating public schema (shared apps)..."
python3 manage.py migrate_schemas --shared || {
    echo "❌ Failed to migrate public schema"
    exit 1
}

# Remove stale content types so post_migrate doesn't violate FK constraints
# Fixes: "insert or update on table auth_permission violates foreign key
#         constraint ... Key (content_type_id)=(N) is not present in
#         table django_content_type"
echo ""
echo "[5/7] Removing stale content types across all tenant schemas..."
python3 scripts/fix_contenttypes.py || {
    echo "⚠️  Warning: fix_contenttypes returned non-zero (safe to ignore on fresh DB)"
}

# Run migrations - All tenant schemas
echo ""
echo "[6/7] Migrating tenant schemas..."
python3 manage.py migrate_schemas || {
    echo "❌ Failed to migrate tenant schemas"
    exit 1
}

# Setup tenants (public + domains)
echo ""
echo "[7/7] Setting up tenants..."
python3 scripts/setup_tenants.py || {
    echo "⚠️  Warning: Failed to setup tenants (may already exist)"
}

echo ""
echo "=========================================="
echo "✅ Build completed successfully!"
echo "=========================================="