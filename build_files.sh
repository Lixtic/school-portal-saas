#!/bin/bash

echo "=========================================="
echo "Building School Portal SaaS"
echo "=========================================="

# Install dependencies
echo ""
echo "[1/5] Installing dependencies..."
python3 -m pip install -r requirements.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}

# Collect static files
echo ""
echo "[2/5] Collecting static files..."
python3 manage.py collectstatic --noinput --clear || {
    echo "❌ Failed to collect static files"
    exit 1
}

# Run migrations - Public schema first
echo ""
echo "[3/5] Migrating public schema (shared apps)..."
python3 manage.py migrate_schemas --shared || {
    echo "❌ Failed to migrate public schema"
    exit 1
}

# Run migrations - All tenant schemas
echo ""
echo "[4/5] Migrating tenant schemas..."
python3 manage.py migrate_schemas || {
    echo "❌ Failed to migrate tenant schemas"
    exit 1
}

# Setup tenants (public + domains)
echo ""
echo "[5/5] Setting up tenants..."
python3 scripts/setup_tenants.py || {
    echo "⚠️  Warning: Failed to setup tenants (may already exist)"
}

echo ""
echo "=========================================="
echo "✅ Build completed successfully!"
echo "=========================================="