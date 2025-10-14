import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mooibanana_project.settings')
django.setup()

from django.conf import settings
from django.urls import get_resolver
from django.contrib import admin

print("="*50)
print("DEBUG MODE:", settings.DEBUG)
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
print("="*50)

print("\nAdmin site registered?", admin.site._registry)
print("\nURL Patterns:")
resolver = get_resolver()
for pattern in resolver.url_patterns:
    print(f"  - {pattern.pattern}")

print("\nTesting URL resolution for '/admin/':")
from django.urls import resolve
try:
    match = resolve('/admin/')
    print(f"  ✓ Resolves to: {match.func}")
except Exception as e:
    print(f"  ✗ Error: {e}")
