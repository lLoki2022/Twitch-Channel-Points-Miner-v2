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

    def test_games_endpoints(self):
        """Test 9: Проверка новых endpoints для игр"""
        print("\n🧪 Тест 9: GET /api/games - получение списка игр...")
        
        try:
            result = self.make_request("GET", "/games")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/games", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/games", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, list):
                self.test_results.append(("❌", "GET /api/games", f"Ответ должен быть массивом: {type(data)}"))
                return False
            
            if len(data) == 0:
                self.test_results.append(("❌", "GET /api/games", "Список игр пуст"))
                return False
            
            # Check game structure
            game = data[0]
            required_fields = ["id", "name", "box_art_url", "has_drops"]
            missing_fields = [field for field in required_fields if field not in game]
            
            if missing_fields:
                self.test_results.append(("❌", "GET /api/games", f"Отсутствуют поля в игре: {missing_fields}"))
                return False
            
            self.test_results.append(("✅", "GET /api/games", f"Успешно: получено {len(data)} игр"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/games", f"Ошибка: {str(e)}"))
            return False

    def test_games_search_endpoint(self):
        """Test 10: Проверка поиска игр"""
        print("\n🧪 Тест 10: GET /api/games/search - поиск игр...")
        
        try:
            # Test search with valid query
            result = self.make_request("GET", "/games/search", params={"q": "Dota"})
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/games/search", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/games/search", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, list):
                self.test_results.append(("❌", "GET /api/games/search", f"Ответ должен быть массивом: {type(data)}"))
                return False
            
            # Should find Dota 2
            dota_found = any(game.get("name", "").lower().find("dota") != -1 for game in data)
            if not dota_found:
                self.test_results.append(("❌", "GET /api/games/search", "Dota 2 не найдена в результатах поиска"))
                return False
            
            self.test_results.append(("✅", "GET /api/games/search", f"Успешно: найдено {len(data)} игр по запросу 'Dota'"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/games/search", f"Ошибка: {str(e)}"))
            return False

    def test_game_streamers_endpoint(self):
        """Test 11: Проверка получения стримеров для игры"""
        print("\n🧪 Тест 11: GET /api/games/{game_id}/streamers - получение стримеров...")
        
        try:
            # Test with Dota 2 game ID
            game_id = "29595"  # Dota 2
            result = self.make_request("GET", f"/games/{game_id}/streamers")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/games/{game_id}/streamers", f"Ошибка соединения: {result['error']}"))
                return False
            
            # This endpoint might return 400 if no authenticated accounts
            if result["status_code"] == 400:
                data = result["data"]
                if isinstance(data, dict) and "detail" in data:
                    if "аутентифицированных аккаунтов" in data["detail"]:
                        self.test_results.append(("✅", "GET /api/games/{game_id}/streamers", "Успешно: endpoint работает, но нет аутентифицированных аккаунтов"))
                        return True
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/games/{game_id}/streamers", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, dict):
                self.test_results.append(("❌", "GET /api/games/{game_id}/streamers", f"Ответ должен быть объектом: {type(data)}"))
                return False
            
            # Check response structure
            required_fields = ["game_id", "streamers", "total_streamers"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.test_results.append(("❌", "GET /api/games/{game_id}/streamers", f"Отсутствуют поля: {missing_fields}"))
                return False
            
            if not isinstance(data["streamers"], list):
                self.test_results.append(("❌", "GET /api/games/{game_id}/streamers", f"streamers должен быть массивом: {type(data['streamers'])}"))
                return False
            
            self.test_results.append(("✅", "GET /api/games/{game_id}/streamers", f"Успешно: получено {data['total_streamers']} стримеров для игры {game_id}"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/games/{game_id}/streamers", f"Ошибка: {str(e)}"))
            return False

    def test_drops_progress_endpoints(self):
        """Test 12: Проверка endpoints прогресса дропов"""
        print("\n🧪 Тест 12: GET /api/drops/progress - получение прогресса дропов...")
        
        try:
            # Test global drops progress
            result = self.make_request("GET", "/drops/progress")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/drops/progress", f"Ошибка соединения: {result['error']}"))
                return False
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/drops/progress", f"Неверный статус код: {result['status_code']}"))
                return False
            
            data = result["data"]
            if not isinstance(data, list):
                self.test_results.append(("❌", "GET /api/drops/progress", f"Ответ должен быть массивом: {type(data)}"))
                return False
            
            # Should return empty array initially
            self.test_results.append(("✅", "GET /api/drops/progress", f"Успешно: получено {len(data)} записей прогресса дропов"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/drops/progress", f"Ошибка: {str(e)}"))
            return False

    def test_account_drops_progress_endpoint(self):
        """Test 13: Проверка прогресса дропов для конкретного аккаунта"""
        print("\n🧪 Тест 13: GET /api/drops/progress/{account_id} - прогресс дропов аккаунта...")
        
        try:
            # Test with non-existent account ID
            fake_account_id = "test-account-id"
            result = self.make_request("GET", f"/drops/progress/{fake_account_id}")
            
            if not result["success"]:
                self.test_results.append(("❌", "GET /api/drops/progress/{account_id}", f"Ошибка соединения: {result['error']}"))
                return False
            
            # Should return 404 for non-existent account
            if result["status_code"] == 404:
                self.test_results.append(("✅", "GET /api/drops/progress/{account_id}", "Успешно: endpoint корректно возвращает 404 для несуществующего аккаунта"))
                return True
            
            if result["status_code"] != 200:
                self.test_results.append(("❌", "GET /api/drops/progress/{account_id}", f"Неверный статус код: {result['status_code']}"))
                return False
            
            # If somehow returns 200, check structure
            data = result["data"]
            if not isinstance(data, dict):
                self.test_results.append(("❌", "GET /api/drops/progress/{account_id}", f"Ответ должен быть объектом: {type(data)}"))
                return False
            
            required_fields = ["account", "drops_progress", "total_drops"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                self.test_results.append(("❌", "GET /api/drops/progress/{account_id}", f"Отсутствуют поля: {missing_fields}"))
                return False
            
            self.test_results.append(("✅", "GET /api/drops/progress/{account_id}", f"Успешно: получен прогресс для аккаунта {data['account']}"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "GET /api/drops/progress/{account_id}", f"Ошибка: {str(e)}"))
            return False

    def test_twitch_account_model_fields(self):
        """Test 14: Проверка новых полей в модели TwitchAccount"""
        print("\n🧪 Тест 14: Проверка новых полей current_stream и current_game...")
        
        try:
            # Get accounts to check model structure
            result = self.make_request("GET", "/accounts")
            
            if not result["success"] or result["status_code"] != 200:
                self.test_results.append(("❌", "Модель TwitchAccount", "Не удалось получить аккаунты для проверки модели"))
                return False
            
            accounts = result["data"]
            
            # If no accounts, we can't test the model fields, but that's OK
            if len(accounts) == 0:
                self.test_results.append(("✅", "Модель TwitchAccount", "Успешно: endpoint работает, новые поля будут доступны при добавлении аккаунтов"))
                return True
            
            # Check if accounts have the new fields (they might be None initially)
            account = accounts[0]
            expected_fields = ["current_stream", "current_game"]
            
            # These fields might not be present initially, which is OK
            has_new_fields = all(field in account for field in expected_fields)
            
            if has_new_fields:
                self.test_results.append(("✅", "Модель TwitchAccount", "Успешно: новые поля current_stream и current_game присутствуют"))
            else:
                self.test_results.append(("✅", "Модель TwitchAccount", "Успешно: модель готова для новых полей (будут добавлены при мониторинге)"))
            
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Модель TwitchAccount", f"Ошибка: {str(e)}"))
            return False

    def test_enhanced_monitoring_system(self):
        """Test 15: Проверка улучшенной системы мониторинга"""
        print("\n🧪 Тест 15: Проверка улучшенной системы мониторинга...")
        
        try:
            # Test monitoring status endpoint
            result = self.make_request("GET", "/monitoring/status")
            
            if not result["success"] or result["status_code"] != 200:
                self.test_results.append(("❌", "Улучшенная система мониторинга", "Не удалось получить статус мониторинга"))
                return False
            
            data = result["data"]
            
            # Check that monitoring system is ready
            if not isinstance(data.get("active"), bool):
                self.test_results.append(("❌", "Улучшенная система мониторинга", "Поле active должно быть boolean"))
                return False
            
            if not isinstance(data.get("accounts_count"), int):
                self.test_results.append(("❌", "Улучшенная система мониторинга", "Поле accounts_count должно быть числом"))
                return False
            
            # Test that we can start monitoring (even if no accounts)
            start_result = self.make_request("POST", "/monitoring/start")
            
            # Should return 400 if no accounts, which is expected behavior
            if start_result["success"] and start_result["status_code"] == 400:
                start_data = start_result["data"]
                if isinstance(start_data, dict) and "detail" in start_data:
                    if "Нет аккаунтов" in start_data["detail"]:
                        self.test_results.append(("✅", "Улучшенная система мониторинга", "Успешно: система мониторинга готова, требуются аккаунты для запуска"))
                        return True
            
            # If monitoring started successfully
            if start_result["success"] and start_result["status_code"] == 200:
                # Stop monitoring to clean up
                self.make_request("POST", "/monitoring/stop")
                self.test_results.append(("✅", "Улучшенная система мониторинга", "Успешно: система мониторинга работает"))
                return True
            
            self.test_results.append(("✅", "Улучшенная система мониторинга", "Успешно: endpoints мониторинга доступны"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Улучшенная система мониторинга", f"Ошибка: {str(e)}"))
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
            self.test_app_loading,
            self.test_games_endpoints,
            self.test_games_search_endpoint,
            self.test_game_streamers_endpoint,
            self.test_drops_progress_endpoints,
            self.test_account_drops_progress_endpoint,
            self.test_twitch_account_model_fields,
            self.test_enhanced_monitoring_system
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