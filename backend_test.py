#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Backend API Testing for Twitch Drops Miner
Tests all API endpoints, OAuth integration, database connectivity, and error handling
"""

import requests
import json
import time
import uuid
from datetime import datetime
import os
import sys

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "http://localhost:8001"

BASE_URL = get_backend_url()
API_URL = f"{BASE_URL}/api"

class TwitchDropsAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.api_url = API_URL
        self.test_results = []
        self.created_accounts = []
        
    def log_test(self, test_name, status, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Twitch Drops Miner" in data["message"]:
                    self.log_test("Server Connectivity", "PASS", 
                                f"Server responding correctly on {self.base_url}")
                    return True
                else:
                    self.log_test("Server Connectivity", "FAIL", 
                                "Server response format incorrect", data)
                    return False
            else:
                self.log_test("Server Connectivity", "FAIL", 
                            f"Server returned status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Server Connectivity", "FAIL", 
                        f"Cannot connect to server: {str(e)}")
            return False
    
    def test_add_account_endpoint(self):
        """Test POST /api/accounts/add endpoint"""
        try:
            response = requests.post(f"{self.api_url}/accounts/add", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["account_id", "user_code", "verification_uri", "expires_in"]
                
                if all(field in data for field in required_fields):
                    # Verify OAuth data format
                    if data["verification_uri"].startswith("https://www.twitch.tv/activate"):
                        self.log_test("Add Account Endpoint", "PASS", 
                                    "Account creation successful with correct OAuth data",
                                    f"User code: {data['user_code']}, Account ID: {data['account_id']}")
                        self.created_accounts.append(data["account_id"])
                        return data
                    else:
                        self.log_test("Add Account Endpoint", "FAIL", 
                                    f"Incorrect verification URI: {data['verification_uri']}")
                        return None
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Add Account Endpoint", "FAIL", 
                                f"Missing required fields: {missing}", data)
                    return None
            else:
                self.log_test("Add Account Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.log_test("Add Account Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
            return None
    
    def test_verify_account_endpoint(self, account_id):
        """Test POST /api/accounts/{account_id}/verify endpoint"""
        try:
            response = requests.post(f"{self.api_url}/accounts/{account_id}/verify", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data:
                    expected_statuses = ["pending", "active", "expired", "error"]
                    if data["status"] in expected_statuses:
                        self.log_test("Verify Account Endpoint", "PASS", 
                                    f"Account verification working, status: {data['status']}")
                        return True
                    else:
                        self.log_test("Verify Account Endpoint", "FAIL", 
                                    f"Invalid status: {data['status']}")
                        return False
                else:
                    self.log_test("Verify Account Endpoint", "FAIL", 
                                "Response missing status field", data)
                    return False
            else:
                self.log_test("Verify Account Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Verify Account Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
            return False
    
    def test_get_accounts_endpoint(self):
        """Test GET /api/accounts endpoint"""
        try:
            response = requests.get(f"{self.api_url}/accounts", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_test("Get Accounts Endpoint", "PASS", 
                                f"Accounts list retrieved successfully ({len(data)} accounts)")
                    return True
                else:
                    self.log_test("Get Accounts Endpoint", "FAIL", 
                                "Response is not a list", type(data))
                    return False
            else:
                self.log_test("Get Accounts Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Get Accounts Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
            return False
    
    def test_delete_account_endpoint(self, account_id):
        """Test DELETE /api/accounts/{account_id} endpoint"""
        try:
            response = requests.delete(f"{self.api_url}/accounts/{account_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Delete Account Endpoint", "PASS", 
                                f"Account deletion successful: {data['message']}")
                    return True
                else:
                    self.log_test("Delete Account Endpoint", "FAIL", 
                                "Response missing message field", data)
                    return False
            elif response.status_code == 404:
                self.log_test("Delete Account Endpoint", "PASS", 
                            "Correctly handles non-existent account (404)")
                return True
            else:
                self.log_test("Delete Account Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Delete Account Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
            return False
    
    def test_get_games_endpoint(self):
        """Test GET /api/games endpoint"""
        try:
            response = requests.get(f"{self.api_url}/games", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "games" in data:
                    if "message" in data and "Нет активных аккаунтов" in data["message"]:
                        self.log_test("Get Games Endpoint", "PASS", 
                                    "Correctly handles no active accounts scenario")
                        return True
                    else:
                        self.log_test("Get Games Endpoint", "PASS", 
                                    f"Games endpoint working ({len(data['games'])} games)")
                        return True
                else:
                    self.log_test("Get Games Endpoint", "FAIL", 
                                "Response missing games field", data)
                    return False
            else:
                self.log_test("Get Games Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Get Games Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
            return False
    
    def test_farming_endpoints(self):
        """Test farming-related endpoints"""
        # Test start farming
        try:
            payload = {
                "account_id": "test_account",
                "game_id": "test_game",
                "game_name": "Test Game"
            }
            response = requests.post(f"{self.api_url}/start-farming", 
                                   json=payload, timeout=10)
            
            if response.status_code == 404:
                self.log_test("Start Farming Endpoint", "PASS", 
                            "Correctly handles non-existent account (404)")
            elif response.status_code == 400:
                self.log_test("Start Farming Endpoint", "PASS", 
                            "Correctly validates request data (400)")
            else:
                self.log_test("Start Farming Endpoint", "WARN", 
                            f"Unexpected response: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Start Farming Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
        
        # Test stop farming
        try:
            payload = {"account_id": "test_account"}
            response = requests.post(f"{self.api_url}/stop-farming", 
                                   json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Stop Farming Endpoint", "PASS", 
                                f"Stop farming working: {data['message']}")
                else:
                    self.log_test("Stop Farming Endpoint", "FAIL", 
                                "Response missing message", data)
            else:
                self.log_test("Stop Farming Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Stop Farming Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
        
        # Test farming status
        try:
            response = requests.get(f"{self.api_url}/farming-status", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "sessions" in data:
                    self.log_test("Farming Status Endpoint", "PASS", 
                                f"Farming status working ({len(data['sessions'])} sessions)")
                else:
                    self.log_test("Farming Status Endpoint", "FAIL", 
                                "Response missing sessions field", data)
            else:
                self.log_test("Farming Status Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Farming Status Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
    
    def test_logs_endpoint(self):
        """Test GET /api/logs endpoint"""
        try:
            response = requests.get(f"{self.api_url}/logs", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "logs" in data:
                    self.log_test("Logs Endpoint", "PASS", 
                                f"Logs endpoint working ({len(data['logs'])} log entries)")
                    return True
                else:
                    self.log_test("Logs Endpoint", "FAIL", 
                                "Response missing logs field", data)
                    return False
            else:
                self.log_test("Logs Endpoint", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log_test("Logs Endpoint", "FAIL", 
                        f"Request failed: {str(e)}")
            return False
    
    def test_oauth_integration(self):
        """Test OAuth integration specifics"""
        account_data = self.test_add_account_endpoint()
        if account_data:
            # Verify OAuth parameters
            user_code = account_data.get("user_code")
            verification_uri = account_data.get("verification_uri")
            expires_in = account_data.get("expires_in")
            
            oauth_valid = True
            issues = []
            
            # Check user code format (should be 8 characters)
            if not user_code or len(user_code) != 8:
                oauth_valid = False
                issues.append(f"Invalid user_code format: {user_code}")
            
            # Check verification URI
            if not verification_uri.startswith("https://www.twitch.tv/activate"):
                oauth_valid = False
                issues.append(f"Wrong verification URI: {verification_uri}")
            
            # Check expires_in is reasonable (should be around 1800 seconds)
            if not expires_in or expires_in < 300 or expires_in > 3600:
                oauth_valid = False
                issues.append(f"Invalid expires_in: {expires_in}")
            
            if oauth_valid:
                self.log_test("OAuth Integration", "PASS", 
                            "OAuth parameters are correctly formatted")
            else:
                self.log_test("OAuth Integration", "FAIL", 
                            "OAuth parameter issues", issues)
    
    def test_database_connectivity(self):
        """Test database operations"""
        # Create account to test DB write
        account_data = self.test_add_account_endpoint()
        if account_data:
            account_id = account_data["account_id"]
            
            # Test DB read by getting accounts
            if self.test_get_accounts_endpoint():
                # Test DB delete
                if self.test_delete_account_endpoint(account_id):
                    self.log_test("Database Connectivity", "PASS", 
                                "Database CRUD operations working correctly")
                else:
                    self.log_test("Database Connectivity", "FAIL", 
                                "Database delete operation failed")
            else:
                self.log_test("Database Connectivity", "FAIL", 
                            "Database read operation failed")
        else:
            self.log_test("Database Connectivity", "FAIL", 
                        "Database write operation failed")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        # Test invalid account ID
        try:
            response = requests.post(f"{self.api_url}/accounts/invalid-id/verify", timeout=10)
            if response.status_code == 404:
                self.log_test("Error Handling - Invalid Account", "PASS", 
                            "Correctly handles invalid account ID (404)")
            else:
                self.log_test("Error Handling - Invalid Account", "FAIL", 
                            f"Unexpected status for invalid account: {response.status_code}")
        except:
            self.log_test("Error Handling - Invalid Account", "FAIL", 
                        "Exception on invalid account request")
        
        # Test malformed JSON
        try:
            response = requests.post(f"{self.api_url}/start-farming", 
                                   data="invalid json", 
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            if response.status_code in [400, 422]:
                self.log_test("Error Handling - Malformed JSON", "PASS", 
                            "Correctly handles malformed JSON")
            else:
                self.log_test("Error Handling - Malformed JSON", "WARN", 
                            f"Unexpected status for malformed JSON: {response.status_code}")
        except:
            self.log_test("Error Handling - Malformed JSON", "FAIL", 
                        "Exception on malformed JSON request")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n🚀 Starting Twitch Drops Miner Backend API Tests")
        print(f"📍 Testing server at: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_server_connectivity():
            print("\n❌ Server not accessible, stopping tests")
            return False
        
        # Core API endpoints
        print("\n📋 Testing Core API Endpoints...")
        self.test_add_account_endpoint()
        self.test_get_accounts_endpoint()
        self.test_logs_endpoint()
        self.test_get_games_endpoint()
        
        # Account management
        print("\n👤 Testing Account Management...")
        if self.created_accounts:
            self.test_verify_account_endpoint(self.created_accounts[0])
        
        # Farming endpoints
        print("\n🎮 Testing Farming Endpoints...")
        self.test_farming_endpoints()
        
        # OAuth and database
        print("\n🔐 Testing OAuth Integration...")
        self.test_oauth_integration()
        
        print("\n💾 Testing Database Connectivity...")
        self.test_database_connectivity()
        
        # Error handling
        print("\n⚠️ Testing Error Handling...")
        self.test_error_handling()
        
        # Cleanup
        print("\n🧹 Cleaning up test accounts...")
        for account_id in self.created_accounts:
            self.test_delete_account_endpoint(account_id)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        warnings = sum(1 for r in self.test_results if r["status"] == "WARN")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Warnings: {warnings}")
        print(f"📈 Total: {len(self.test_results)}")
        
        if failed == 0:
            print("\n🎉 All critical tests passed!")
            return True
        else:
            print(f"\n💥 {failed} critical issues found!")
            print("\nFailed tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test']}: {result['message']}")
            return False

def main():
    """Main test execution"""
    tester = TwitchDropsAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(tester.test_results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: /app/backend_test_results.json")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())