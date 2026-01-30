#!/usr/bin/env python3
"""Test signup locally to see the real error"""
import asyncio
import sys
sys.path.insert(0, '/Users/melihcanodacioglu/Desktop/panel/backend')

from services.auth_service import signup

async def test():
    result = await signup(
        email="localtest@example.com",
        password="test123",
        full_name="Local Test",
        ip_address="127.0.0.1",
        user_agent="Test Agent"
    )
    
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Error Code: {result.error_code}")
    if result.success:
        print(f"User ID: {result.user_id}")
        print(f"Referral Code: {result.referral_code}")

if __name__ == "__main__":
    asyncio.run(test())
