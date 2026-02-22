#!/usr/bin/env python
"""
School Registration Flow Debugging Script
Tests the entire signup -> approval -> activation flow
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from django.db import connection
from tenants.models import School, Domain
from django.contrib.auth import get_user_model
from django.utils import timezone
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

print("=" * 70)
print("SCHOOL REGISTRATION FLOW DEBUG")
print("=" * 70)

# Test 1: Check database connection
print("\n[1] Database Connection Test")
print("-" * 70)
try:
    School.objects.count()
    print("✓ Database connection OK")
    print(f"  Current schema: {connection.schema_name}")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    sys.exit(1)

# Test 2: Check School model fields
print("\n[2] School Model Fields Test")
print("-" * 70)
try:
    school = School()
    fields = [f.name for f in School._meta.get_fields()]
    required_fields = [
        'schema_name', 'name', 'approval_status', 'contact_person_email',
        'registration_certificate', 'submitted_for_review_at'
    ]
    missing = [f for f in required_fields if f not in fields]
    
    if missing:
        print(f"✗ Missing required fields: {missing}")
    else:
        print("✓ All required fields present")
        print(f"  Total fields: {len(fields)}")
except Exception as e:
    print(f"✗ Error checking fields: {e}")

# Test 3: Create test tenant
print("\n[3] Tenant Creation Test")
print("-" * 70)
test_schema = f"test_debug_{timezone.now().timestamp()}".replace(".", "_")[:30]
print(f"  Test schema name: {test_schema}")

try:
    # Check if test schema already exists
    existing = School.objects.filter(schema_name=test_schema).first()
    if existing:
        print(f"⚠ Test tenant already exists, using existing")
        test_school = existing
    else:
        # Create test file
        test_file = SimpleUploadedFile(
            "test_cert.pdf",
            b"PDF test content",
            content_type="application/pdf"
        )
        
        test_school = School.objects.create(
            schema_name=test_schema,
            name=f"Debug Test School",
            school_type='basic',
            address="123 Test St",
            phone_number="+233 24 123 4567",
            country="Ghana",
            approval_status='pending',
            contact_person_name="Test Admin",
            contact_person_email="test@debugschool.local",
            contact_person_phone="+233 24 123 4567",
            contact_person_title="Principal",
            registration_certificate=test_file,
            submitted_for_review_at=timezone.now(),
            auto_create_schema=False,  # Don't auto-create yet
            is_active=False
        )
        print(f"✓ Tenant created: {test_school.id}")
        
except Exception as e:
    print(f"✗ Failed to create tenant: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Check Domain creation
print("\n[4] Domain Creation Test")
print("-" * 70)
try:
    domain = Domain.objects.filter(tenant=test_school).first()
    if domain:
        print(f"✓ Domain exists: {domain.domain}")
    else:
        domain = Domain.objects.create(
            domain=f"{test_schema}.local",
            tenant=test_school,
            is_primary=True
        )
        print(f"✓ Domain created: {domain.domain}")
except Exception as e:
    print(f"✗ Failed with domain: {e}")

# Test 5: Check schema creation capability
print("\n[5] Schema Creation Capability Test")
print("-" * 70)
try:
    print(f"  Can create schema: {test_school.auto_create_schema}")
    print(f"  Is active: {test_school.is_active}")
    print(f"  Has schema: {test_school.schema_exists}")
    
    if not test_school.schema_exists:
        print("  → Schema does not exist yet (expected for pending schools)")
    else:
        print("  → Schema already exists")
        
except Exception as e:
    print(f"✗ Error checking schema: {e}")

# Test 6: Test approval flow
print("\n[6] Approval Flow Test")
print("-" * 70)
try:
    print(f"  Current status: {test_school.approval_status}")
    print(f"  Changing to 'approved'...")
    
    # Simulate admin approval
    test_school.approval_status = 'approved'
    test_school.is_active = True
    test_school.auto_create_schema = True
    test_school.reviewed_at = timezone.now()
    
    # Create admin user for testing
    admin_user = User.objects.create_superuser(
        username=f"admin_{test_schema}",
        email=f"admin_{test_schema}@test.local",
        password='testpass123',
        user_type='admin'
    )
    test_school.reviewed_by = admin_user
    test_school.save()
    
    print(f"✓ School marked as approved")
    print(f"  Status: {test_school.approval_status}")
    print(f"  Active: {test_school.is_active}")
    print(f"  Auto-create schema: {test_school.auto_create_schema}")
    
except Exception as e:
    print(f"✗ Approval flow error: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Schema creation
print("\n[7] Schema Creation Test")
print("-" * 70)
try:
    if not test_school.schema_exists:
        print(f"  Creating schema for {test_school.schema_name}...")
        test_school.create_schema(check_if_exists=True, verbosity=2)
        print(f"✓ Schema created successfully")
    else:
        print(f"✓ Schema already exists")
        
    # Verify schema exists
    connection.set_tenant(test_school)
    User.objects.count()
    connection.set_schema_to_public()
    print(f"✓ Can access tenant schema")
    
except Exception as e:
    print(f"✗ Schema creation failed: {e}")
    import traceback
    traceback.print_exc()
    try:
        connection.set_schema_to_public()
    except:
        pass

# Test 8: List all pending schools
print("\n[8] Pending Schools Summary")
print("-" * 70)
try:
    pending = School.objects.filter(approval_status='pending')
    print(f"  Total pending: {pending.count()}")
    for school in pending[:5]:
        print(f"    - {school.name} ({school.schema_name})")
        print(f"      Status: {school.approval_status}, Active: {school.is_active}")
        print(f"      Submitted: {school.submitted_for_review_at}")
except Exception as e:
    print(f"✗ Error listing pending: {e}")

# Test 9: Check approved schools
print("\n[9] Approved Schools Summary")
print("-" * 70)
try:
    approved = School.objects.filter(approval_status='approved', is_active=True)
    print(f"  Total approved & active: {approved.count()}")
    for school in approved[:5]:
        print(f"    - {school.name} ({school.schema_name})")
        print(f"      Schema exists: {school.schema_exists}")
except Exception as e:
    print(f"✗ Error listing approved: {e}")

# Test 10: Check for orphaned tenants
print("\n[10] Orphaned Tenants Check")
print("-" * 70)
try:
    from django.db import connection as django_conn
    from psycopg2 import connect as pg_connect
    
    # List all schemas in PostgreSQL
    cursor = django_conn.cursor()
    cursor.execute("""
        SELECT schema_name FROM information_schema.schemata 
        WHERE schema_name NOT LIKE 'pg_%' 
        AND schema_name NOT IN ('public', 'information_schema')
        ORDER BY schema_name
    """)
    db_schemas = [row[0] for row in cursor.fetchall()]
    
    # Get tenant schemas from Django
    tenant_schemas = set(School.objects.values_list('schema_name', flat=True))
    
    orphaned = set(db_schemas) - tenant_schemas
    missing = tenant_schemas - set(db_schemas)
    
    if orphaned:
        print(f"⚠ Orphaned schemas in DB: {orphaned}")
    else:
        print(f"✓ No orphaned schemas found")
        
    if missing:
        print(f"⚠ Missing schemas for tenants: {missing}")
    else:
        print(f"✓ All tenant schemas exist in DB")
    
    print(f"  Total DB schemas: {len(db_schemas)}")
    print(f"  Total tenant records: {len(tenant_schemas)}")
    
except Exception as e:
    print(f"⚠ Could not check orphaned schemas: {e}")

print("\n" + "=" * 70)
print("DEBUG REPORT COMPLETE")
print("=" * 70)
print("\n✓ Registration flow debugging complete!")
print("\nNEXT STEPS:")
print("  1. Check /admin/tenants/school/ for pending schools")
print("  2. Use /tenants/approval-queue/ to review and approve schools")
print("  3. Check console output above for any ✗ errors")
print("  4. Review logs in school_system/logs/ if available")
