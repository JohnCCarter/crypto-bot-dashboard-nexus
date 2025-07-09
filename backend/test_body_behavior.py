#!/usr/bin/env python3
"""Test script to understand FastAPI Body(...) behavior."""

from fastapi import FastAPI, Body
from pydantic import BaseModel
from fastapi.testclient import TestClient

# Create a simple test app
app = FastAPI()

class TestModel(BaseModel):
    name: str
    value: int

# Test 1: Without Body(...)
@app.post("/test1")
async def test1(data: TestModel):
    return {"received": data.dict()}

# Test 2: With Body(...)
@app.post("/test2")
async def test2(data: TestModel = Body(...)):
    return {"received": data.dict()}

# Test 3: With Body(..., embed=False)
@app.post("/test3")
async def test3(data: TestModel = Body(..., embed=False)):
    return {"received": data.dict()}

# Test 4: With Body(..., embed=True)
@app.post("/test4")
async def test4(data: TestModel = Body(..., embed=True)):
    return {"received": data.dict()}

def test_body_behavior():
    """Test different Body(...) behaviors."""
    client = TestClient(app)
    
    test_data = {"name": "test", "value": 42}
    
    print("=== Testing FastAPI Body(...) behavior ===\n")
    
    # Test 1: Without Body(...)
    print("Test 1: Without Body(...)")
    print(f"  Sending: {test_data}")
    try:
        response = client.post("/test1", json=test_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 2: With Body(...)
    print("Test 2: With Body(...)")
    print(f"  Sending: {test_data}")
    try:
        response = client.post("/test2", json=test_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 3: With Body(..., embed=False)
    print("Test 3: With Body(..., embed=False)")
    print(f"  Sending: {test_data}")
    try:
        response = client.post("/test3", json=test_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 4: With Body(..., embed=True)
    print("Test 4: With Body(..., embed=True)")
    print(f"  Sending: {test_data}")
    try:
        response = client.post("/test4", json=test_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    print()
    
    # Test 4b: With Body(..., embed=True) and wrapped data
    print("Test 4b: With Body(..., embed=True) and wrapped data")
    wrapped_data = {"data": test_data}
    print(f"  Sending: {wrapped_data}")
    try:
        response = client.post("/test4", json=wrapped_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

if __name__ == "__main__":
    test_body_behavior() 