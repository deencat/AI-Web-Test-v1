"""Test JWT token creation and decoding."""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from datetime import timedelta
from app.core.security import create_access_token, decode_token
from app.core.config import settings

print("=" * 60)
print("Testing JWT Token Creation and Decoding")
print("=" * 60)

# Create token
print("\n[Step 1] Creating access token...")
access_token = create_access_token(
    data={"sub": "1"},  # Must be string!
    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
)
print(f"Token: {access_token[:80]}...")

# Decode token
print("\n[Step 2] Decoding token...")
payload = decode_token(access_token)
print(f"Payload: {payload}")

if payload:
    print(f"\n[OK] Token creation and decoding works!")
    print(f"User ID: {payload.get('sub')}")
    print(f"Expiration: {payload.get('exp')}")
else:
    print(f"\n[ERROR] Token decoding failed!")

print("\n" + "=" * 60)

