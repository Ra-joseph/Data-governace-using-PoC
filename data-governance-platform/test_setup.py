#!/usr/bin/env python3
"""
Test Setup Script for Data Governance Platform
Validates installation and basic functionality with colored output.
"""

import sys
import json
import requests
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

BASE_URL = "http://localhost:8000"

def print_header(text):
    """Print section header."""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{text}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")

def print_success(text):
    """Print success message."""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    """Print error message."""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_warning(text):
    """Print warning message."""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

def print_info(text):
    """Print info message."""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")

def test_health_check():
    """Test 1: Health check endpoint."""
    print_header("Test 1: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is healthy: {data['service']} v{data['version']}")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Could not connect to API: {e}")
        print_info("Make sure the backend is running: cd backend && uvicorn app.main:app --reload")
        return False

def test_postgres_connection():
    """Test 2: PostgreSQL connection."""
    print_header("Test 2: PostgreSQL Connection")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/datasets/postgres/tables", timeout=5)
        if response.status_code == 200:
            tables = response.json()
            print_success(f"Connected to PostgreSQL - Found {len(tables)} tables")
            for table in tables:
                print(f"  • {table['table_name']} ({table['table_type']})")
            return True
        else:
            print_error(f"Failed to connect to PostgreSQL (status {response.status_code})")
            print_info("Make sure PostgreSQL is running: docker-compose up -d")
            return False
    except Exception as e:
        print_error(f"PostgreSQL connection test failed: {e}")
        return False

def test_schema_import():
    """Test 3: Schema import from customer_accounts table."""
    print_header("Test 3: Schema Import")
    try:
        payload = {
            "source_type": "postgres",
            "table_name": "customer_accounts",
            "schema_name": "public"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/datasets/import-schema",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Imported schema for '{data['table_name']}'")
            print_info(f"  Description: {data['description']}")
            print_info(f"  Contains PII: {data['metadata']['contains_pii']}")
            print_info(f"  Suggested Classification: {data['metadata']['suggested_classification']}")
            print_info(f"  Fields: {len(data['schema_definition'])} columns")
            print_info(f"  Primary Keys: {data['metadata']['primary_keys']}")
            print_info(f"  Row Count: {data['metadata']['row_count']}")
            return True
        else:
            print_error(f"Schema import failed (status {response.status_code})")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Schema import test failed: {e}")
        return False

def test_dataset_registration():
    """Test 4: Dataset registration with validation."""
    print_header("Test 4: Dataset Registration & Validation")
    try:
        # Load example payload
        with open('examples/register_customer_accounts.json', 'r') as f:
            payload = json.load(f)
        
        response = requests.post(
            f"{BASE_URL}/api/v1/datasets/",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"Dataset '{data['name']}' registered successfully")
            print_info(f"  ID: {data['id']}")
            print_info(f"  Status: {data['status']}")
            print_info(f"  Classification: {data['classification']}")
            print_info(f"  Contains PII: {data['contains_pii']}")
            
            # Check if there are validation warnings
            if data['status'] == 'draft':
                print_warning("Dataset in DRAFT status - validation found policy violations")
                print_info("Check contract validation results for details")
            else:
                print_success("Dataset PUBLISHED - all validations passed")
            
            return True
        elif response.status_code == 400:
            error = response.json()
            if "already exists" in error.get('detail', ''):
                print_warning("Dataset already exists - this is OK for repeated tests")
                return True
            print_error(f"Registration failed: {error.get('detail', 'Unknown error')}")
            return False
        else:
            print_error(f"Registration failed (status {response.status_code})")
            print_error(response.text)
            return False
    except Exception as e:
        print_error(f"Dataset registration test failed: {e}")
        return False

def test_list_datasets():
    """Test 5: List all datasets."""
    print_header("Test 5: List Datasets")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/datasets/", timeout=5)
        
        if response.status_code == 200:
            datasets = response.json()
            print_success(f"Found {len(datasets)} dataset(s)")
            
            for ds in datasets:
                status_color = Fore.GREEN if ds['status'] == 'published' else Fore.YELLOW
                pii_marker = f"{Fore.RED}[PII]{Style.RESET_ALL}" if ds['contains_pii'] else ""
                print(f"  • {ds['name']} - {status_color}{ds['status'].upper()}{Style.RESET_ALL} "
                      f"({ds['classification']}) {pii_marker}")
            
            return True
        else:
            print_error(f"Failed to list datasets (status {response.status_code})")
            return False
    except Exception as e:
        print_error(f"List datasets test failed: {e}")
        return False

def main():
    """Run all tests."""
    print(f"\n{Fore.MAGENTA}{'=' * 70}")
    print(f"{Fore.MAGENTA}Data Governance Platform - Setup Validation")
    print(f"{Fore.MAGENTA}{'=' * 70}{Style.RESET_ALL}\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("PostgreSQL Connection", test_postgres_connection),
        ("Schema Import", test_schema_import),
        ("Dataset Registration", test_dataset_registration),
        ("List Datasets", test_list_datasets)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Print summary
    print_header("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed{Style.RESET_ALL}")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{'=' * 70}")
        print(f"{Fore.GREEN}🎉 All tests passed! Setup is complete.")
        print(f"{Fore.GREEN}{'=' * 70}{Style.RESET_ALL}\n")
        print_info("Next steps:")
        print("  1. Visit http://localhost:8000/api/docs for API documentation")
        print("  2. Check backend/contracts/ for generated contract files")
        print("  3. Review validation results in the API responses")
        return 0
    else:
        print(f"\n{Fore.RED}{'=' * 70}")
        print(f"{Fore.RED}❌ Some tests failed. Please check the errors above.")
        print(f"{Fore.RED}{'=' * 70}{Style.RESET_ALL}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
