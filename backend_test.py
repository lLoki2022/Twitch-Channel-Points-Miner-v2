#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API Test Suite for Twitch Drops Miner
Tests FastAPI endpoints to ensure they are working correctly
"""

import sys
import os
import json
import requests
import time
from typing import Dict, Any

# Add the app directory to Python path
sys.path.insert(0, '/app')

class TwitchDropsMinerAPITest:
    """Test suite for Twitch Drops Miner FastAPI endpoints"""
    
    def __init__(self):
        self.test_results = []
        self.base_url = self.get_backend_url()
        self.session = requests.Session()
        self.session.timeout = 10
        
    def get_backend_url(self) -> str:
        """Get backend URL from frontend .env file"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        url = line.split('=', 1)[1].strip()
                        return f"{url}/api"
            return "http://localhost:8001/api"
        except Exception as e:
            print(f"⚠️ Не удалось прочитать URL из .env: {e}")
            return "http://localhost:8001/api"
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
                "headers": dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": None,
                "data": None
            }
        except json.JSONDecodeError as e:
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.text,
                "json_error": str(e)
            }
    
    def test_api_root(self):
        """Test 1: Проверка корневого API endpoint"""
        print("\n🧪 Тест 1: GET /api/ - корневой endpoint...")
        
        try:
            result = self.make_request("GET", "/")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, dict) or "message" not in data:
                self.test_results.append(("❌", "GET /api/", f"Неверный формат ответа: {data}"))
                return False
            
            self.test_results.append(("✅", "GET /api/", f"Успешно: {data['message']}"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/", f"Ошибка: {str(e)}"))
            return False
    
    def test_accounts_endpoint(self):
        """Test 2: Проверка endpoint аккаунтов"""
        print("\n🧪 Тест 2: GET /api/accounts - список аккаунтов...")
        
        try:
            result = self.make_request("GET", "/accounts")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/accounts", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/accounts", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, list):
                self.test_results.append(("❌", "GET /api/accounts", f"Ответ должен быть массивом: {type(data)}"))
                return False
            
            # Should return empty array initially
            if len(data) == 0:
                self.test_results.append(("✅", "GET /api/accounts", "Успешно: пустой массив аккаунтов"))
            else:
                self.test_results.append(("✅", "GET /api/accounts", f"Успешно: {len(data)} аккаунтов"))
            
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/accounts", f"Ошибка: {str(e)}"))
            return False
    
    def test_settings_endpoint(self):
        """Test 3: Проверка endpoint настроек"""
        print("\n🧪 Тест 3: GET /api/settings - настройки...")
        
        try:
            result = self.make_request("GET", "/settings")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/settings", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/settings", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, dict):
                self.test_results.append(("❌", "GET /api/settings", f"Ответ должен быть объектом: {type(data)}"))
                return False
            
            # Check required fields
            required_fields = ["id", "check_interval", "auto_claim_drops", "watch_time_minutes", "language"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.test_results.append(("❌", "GET /api/settings", f"Отсутствуют поля: {missing_fields}"))
                return False
            
            # Check language is Russian
            if data.get("language") != "ru":
                self.test_results.append(("⚠️", "GET /api/settings", f"Язык не русский: {data.get('language')}"))
            
            self.test_results.append(("✅", "GET /api/settings", "Успешно: настройки получены"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/settings", f"Ошибка: {str(e)}"))
            return False
    
    def test_statistics_endpoint(self):
        """Test 4: Проверка endpoint статистики"""
        print("\n🧪 Тест 4: GET /api/statistics - статистика...")
        
        try:
            result = self.make_request("GET", "/statistics")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/statistics", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/statistics", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, dict):
                self.test_results.append(("❌", "GET /api/statistics", f"Ответ должен быть объектом: {type(data)}"))
                return False
            
            # Check required fields
            required_fields = ["total_accounts", "active_accounts", "total_drops_claimed", "monitoring_active"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.test_results.append(("❌", "GET /api/statistics", f"Отсутствуют поля: {missing_fields}"))
                return False
            
            # Validate data types
            if not isinstance(data["total_accounts"], int):
                self.test_results.append(("❌", "GET /api/statistics", f"total_accounts должно быть числом: {type(data['total_accounts'])}"))
                return False
            
            if not isinstance(data["monitoring_active"], bool):
                self.test_results.append(("❌", "GET /api/statistics", f"monitoring_active должно быть boolean: {type(data['monitoring_active'])}"))
                return False
            
            self.test_results.append(("✅", "GET /api/statistics", f"Успешно: {data['total_accounts']} аккаунтов, {data['total_drops_claimed']} дропов"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/statistics", f"Ошибка: {str(e)}"))
            return False
    
    def test_monitoring_status_endpoint(self):
        """Test 5: Проверка endpoint статуса мониторинга"""
        print("\n🧪 Тест 5: GET /api/monitoring/status - статус мониторинга...")
        
        try:
            result = self.make_request("GET", "/monitoring/status")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/monitoring/status", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/monitoring/status", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, dict):
                self.test_results.append(("❌", "GET /api/monitoring/status", f"Ответ должен быть объектом: {type(data)}"))
                return False
            
            # Check required fields
            required_fields = ["active", "accounts_count"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.test_results.append(("❌", "GET /api/monitoring/status", f"Отсутствуют поля: {missing_fields}"))
                return False
            
            # Validate data types
            if not isinstance(data["active"], bool):
                self.test_results.append(("❌", "GET /api/monitoring/status", f"active должно быть boolean: {type(data['active'])}"))
                return False
            
            if not isinstance(data["accounts_count"], int):
                self.test_results.append(("❌", "GET /api/monitoring/status", f"accounts_count должно быть числом: {type(data['accounts_count'])}"))
                return False
            
            self.test_results.append(("✅", "GET /api/monitoring/status", f"Успешно: активен={data['active']}, аккаунтов={data['accounts_count']}"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/monitoring/status", f"Ошибка: {str(e)}"))
            return False
    
    def test_device_code_endpoint(self):
        """Test 6: Проверка endpoint получения device code"""
        print("\n🧪 Тест 6: POST /api/accounts/device-code - получение device code...")
        
        try:
            result = self.make_request("POST", "/accounts/device-code")
            
            if not result["success"]:
                self.test_results.append(("❌", "POST /api/accounts/device-code", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "POST /api/accounts/device-code", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, dict):
                self.test_results.append(("❌", "POST /api/accounts/device-code", f"Ответ должен быть объектом: {type(data)}"))
                return False
            
            # Check required fields for device code response
            required_fields = ["device_code", "user_code", "verification_uri", "expires_in", "interval"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.test_results.append(("❌", "POST /api/accounts/device-code", f"Отсутствуют поля: {missing_fields}"))
                return False
            
            # Validate field types and values
            if not isinstance(data["expires_in"], int) or data["expires_in"] <= 0:
                self.test_results.append(("❌", "POST /api/accounts/device-code", f"expires_in должно быть положительным числом: {data['expires_in']}"))
                return False
            
            if not isinstance(data["interval"], int) or data["interval"] <= 0:
                self.test_results.append(("❌", "POST /api/accounts/device-code", f"interval должно быть положительным числом: {data['interval']}"))
                return False
            
            if not data["verification_uri"].startswith("https://"):
                self.test_results.append(("❌", "POST /api/accounts/device-code", f"verification_uri должен быть HTTPS URL: {data['verification_uri']}"))
                return False
            
            self.test_results.append(("✅", "POST /api/accounts/device-code", f"Успешно: код={data['user_code']}, URI={data['verification_uri']}"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "POST /api/accounts/device-code", f"Ошибка: {str(e)}"))
            return False
    
    def test_objectid_serialization(self):
        """Test 7: Проверка отсутствия ошибок сериализации ObjectId"""
        print("\n🧪 Тест 7: Проверка сериализации ObjectId во всех endpoints...")
        
        try:
            endpoints_to_test = [
                ("GET", "/accounts"),
                ("GET", "/settings"),
                ("GET", "/statistics"),
                ("GET", "/monitoring/status")
            ]
            
            objectid_errors = []
            
            for method, endpoint in endpoints_to_test:
                result = self.make_request(method, endpoint)
                
                if result["success"] and result["status_code"] == 200:
                    # Check if response contains any ObjectId serialization errors
                    response_str = json.dumps(result["data"]) if isinstance(result["data"], (dict, list)) else str(result["data"])
                    
                    if "ObjectId" in response_str:
                        objectid_errors.append(f"{method} {endpoint}: содержит ObjectId в ответе")
                    
                    if "not JSON serializable" in response_str:
                        objectid_errors.append(f"{method} {endpoint}: ошибка сериализации JSON")
            
            if objectid_errors:
                self.test_results.append(("❌", "Сериализация ObjectId", f"Найдены ошибки: {objectid_errors}"))
                return False
            
            self.test_results.append(("✅", "Сериализация ObjectId", "Успешно: все endpoints корректно сериализуют данные"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Сериализация ObjectId", f"Ошибка: {str(e)}"))
            return False
    
    def test_app_loading(self):
        """Test 8: Проверка загрузки приложения без Network Error"""
        print("\n🧪 Тест 8: Проверка загрузки приложения...")
        
        try:
            # Test all critical endpoints that frontend needs on startup
            critical_endpoints = [
                ("GET", "/accounts", "аккаунты"),
                ("GET", "/settings", "настройки"),
                ("GET", "/statistics", "статистика"),
                ("GET", "/monitoring/status", "статус мониторинга")
            ]
            
            failed_endpoints = []
            
            for method, endpoint, description in critical_endpoints:
                result = self.make_request(method, endpoint)
                
                if not result["success"]:
                    failed_endpoints.append(f"{description} ({method} {endpoint}): {result['error']}")
                elif result["status_code"] != 200:
                    failed_endpoints.append(f"{description} ({method} {endpoint}): статус {result['status_code']}")
            
            if failed_endpoints:
                self.test_results.append(("❌", "Загрузка приложения", f"Ошибки: {failed_endpoints}"))
                return False
            
            self.test_results.append(("✅", "Загрузка приложения", "Успешно: все критические endpoints доступны"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Загрузка приложения", f"Ошибка: {str(e)}"))
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск тестирования Twitch Drops Miner API...")
        print(f"🌐 Backend URL: {self.base_url}")
        print("=" * 70)
        
        # Run all tests
        tests = [
            self.test_api_root,
            self.test_accounts_endpoint,
            self.test_settings_endpoint,
            self.test_statistics_endpoint,
            self.test_monitoring_status_endpoint,
            self.test_device_code_endpoint,
            self.test_objectid_serialization,
            self.test_app_loading
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        # Print results
        print("\n" + "=" * 70)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ API")
        print("=" * 70)
        
        for status, test_name, result in self.test_results:
            print(f"{status} {test_name}: {result}")
        
        print("=" * 70)
        print(f"✅ Пройдено: {passed}/{total}")
        print(f"❌ Провалено: {total - passed}/{total}")
        print(f"📈 Успешность: {(passed/total)*100:.1f}%")
        
        return passed == total


def main():
    """Главная функция тестирования"""
    print("🎮 Тестирование Twitch Drops Miner API")
    print("📝 Версия тестов: 2.0")
    print("🎯 Фокус: FastAPI endpoints и исправление ObjectId ошибок\n")
    
    tester = TwitchDropsMinerAPITest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("\n⚠️  Некоторые тесты провалены. Проверьте детали выше.")
        return 1


if __name__ == "__main__":
    exit(main())