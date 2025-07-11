#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitch Drops Miner - Упрощенная версия для автоматического получения дропов
Автор: AI Assistant
Версия: 1.0
"""

import json
import time
import requests
import threading
from datetime import datetime
from typing import Dict, List, Optional
import uuid
import webbrowser
from urllib.parse import urlencode

class TwitchDropsMiner:
    """Основной класс для получения дропов с Twitch"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.accounts = {}
        self.running = False
        
        # Twitch API endpoints
        self.twitch_api_base = "https://api.twitch.tv/helix"
        self.twitch_oauth_base = "https://id.twitch.tv/oauth2"
        self.twitch_gql_base = "https://gql.twitch.tv/gql"
        
        # Client ID (публичный, для TV приложений)
        self.client_id = "ue6666qo983tsx6so1t0vnawi233wa"
        
        print("🎮 Twitch Drops Miner запущен!")
        print("📝 Версия: 1.0 (упрощенная)")
        print("🎯 Фокус: получение дропов\n")
    
    def load_config(self) -> Dict:
        """Загружает конфигурацию из файла"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"📁 Файл конфигурации {self.config_file} не найден.")
            return self.create_default_config()
    
    def create_default_config(self) -> Dict:
        """Создает конфигурацию по умолчанию"""
        config = {
            "accounts": [],
            "settings": {
                "check_interval": 60,  # секунды
                "auto_claim_drops": True,
                "watch_time_minutes": 30,
                "language": "ru"
            }
        }
        self.save_config(config)
        print("✅ Создан файл конфигурации по умолчанию")
        return config
    
    def save_config(self, config: Dict = None):
        """Сохраняет конфигурацию в файл"""
        if config is None:
            config = self.config
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def authenticate_account(self, username: str) -> Optional[Dict]:
        """Авторизует аккаунт через twitch.tv/activate"""
        print(f"\n🔐 Авторизация аккаунта: {username}")
        
        # Шаг 1: Получить device code
        device_code_url = f"{self.twitch_oauth_base}/device"
        device_data = {
            "client_id": self.client_id,
            "scope": "user:read:email user:read:follows chat:read"
        }
        
        try:
            response = requests.post(device_code_url, data=device_data)
            if response.status_code != 200:
                print(f"❌ Ошибка получения device code: {response.status_code}")
                return None
            
            device_info = response.json()
            device_code = device_info.get("device_code")
            user_code = device_info.get("user_code")
            verification_uri = device_info.get("verification_uri")
            expires_in = device_info.get("expires_in", 1800)
            interval = device_info.get("interval", 5)
            
            print(f"📱 Перейдите по ссылке: {verification_uri}")
            print(f"🔑 Введите код: {user_code}")
            print(f"⏰ Код действует {expires_in} секунд")
            print("🌐 Открываю браузер...")
            
            # Открыть браузер
            webbrowser.open(verification_uri)
            
            # Шаг 2: Ожидание авторизации
            print("⏳ Ожидаю авторизации...")
            start_time = time.time()
            
            while time.time() - start_time < expires_in:
                time.sleep(interval)
                
                # Проверка статуса авторизации
                token_url = f"{self.twitch_oauth_base}/token"
                token_data = {
                    "client_id": self.client_id,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
                
                token_response = requests.post(token_url, data=token_data)
                token_result = token_response.json()
                
                if token_response.status_code == 200:
                    access_token = token_result.get("access_token")
                    refresh_token = token_result.get("refresh_token")
                    
                    # Получить информацию о пользователе
                    user_info = self.get_user_info(access_token)
                    if user_info:
                        account_data = {
                            "username": user_info.get("display_name", username),
                            "user_id": user_info.get("id"),
                            "access_token": access_token,
                            "refresh_token": refresh_token,
                            "authenticated_at": datetime.now().isoformat()
                        }
                        
                        print(f"✅ Авторизация успешна: {account_data['username']}")
                        return account_data
                
                elif token_result.get("error") == "authorization_pending":
                    continue
                else:
                    print(f"❌ Ошибка авторизации: {token_result.get('error')}")
                    break
            
            print("⏰ Время авторизации истекло")
            return None
            
        except Exception as e:
            print(f"❌ Ошибка авторизации: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Получает информацию о пользователе"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-Id": self.client_id
        }
        
        try:
            response = requests.get(f"{self.twitch_api_base}/users", headers=headers)
            if response.status_code == 200:
                users = response.json().get("data", [])
                return users[0] if users else None
            return None
        except Exception as e:
            print(f"❌ Ошибка получения информации о пользователе: {str(e)}")
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """Обновляет access token"""
        refresh_data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id
        }
        
        try:
            response = requests.post(f"{self.twitch_oauth_base}/token", data=refresh_data)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Ошибка обновления токена: {str(e)}")
            return None
    
    def get_drops_campaigns(self, access_token: str) -> List[Dict]:
        """Получает активные кампании дропов"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-Id": self.client_id
        }
        
        # GraphQL запрос для получения кампаний дропов
        gql_query = {
            "query": """
                query ViewerDropsDashboard {
                    currentUser {
                        dropCampaigns {
                            id
                            name
                            game {
                                displayName
                            }
                            status
                            startAt
                            endAt
                            detailsURL
                            accountLinkURL
                            self {
                                isAccountConnected
                                drops {
                                    id
                                    name
                                    imageURL
                                    benefitEdges {
                                        benefit {
                                            name
                                        }
                                    }
                                    requiredMinutesWatched
                                    self {
                                        dropInstanceID
                                        isEligibleForDrop
                                        currentMinutesWatched
                                        isClaimed
                                    }
                                }
                            }
                        }
                    }
                }
            """
        }
        
        try:
            response = requests.post(self.twitch_gql_base, json=gql_query, headers=headers)
            if response.status_code == 200:
                data = response.json()
                campaigns = data.get("data", {}).get("currentUser", {}).get("dropCampaigns", [])
                return [c for c in campaigns if c.get("status") == "ACTIVE"]
            return []
        except Exception as e:
            print(f"❌ Ошибка получения кампаний дропов: {str(e)}")
            return []
    
    def claim_drop(self, access_token: str, drop_instance_id: str) -> bool:
        """Получает дроп"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-Id": self.client_id
        }
        
        gql_query = {
            "query": """
                mutation DropsPage_ClaimDropRewards($input: ClaimDropRewardsInput!) {
                    claimDropRewards(input: $input) {
                        status
                        errors {
                            code
                        }
                    }
                }
            """,
            "variables": {
                "input": {
                    "dropInstanceID": drop_instance_id
                }
            }
        }
        
        try:
            response = requests.post(self.twitch_gql_base, json=gql_query, headers=headers)
            if response.status_code == 200:
                data = response.json()
                status = data.get("data", {}).get("claimDropRewards", {}).get("status")
                return status == "ELIGIBLE_FOR_ALL"
            return False
        except Exception as e:
            print(f"❌ Ошибка получения дропа: {str(e)}")
            return False
    
    def watch_stream(self, access_token: str, channel_login: str, minutes: int = 30):
        """Имитирует просмотр стрима"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-Id": self.client_id
        }
        
        print(f"📺 Начинаю просмотр канала: {channel_login} ({minutes} минут)")
        
        # Получить информацию о канале
        channel_response = requests.get(
            f"{self.twitch_api_base}/users",
            headers=headers,
            params={"login": channel_login}
        )
        
        if channel_response.status_code != 200:
            print(f"❌ Канал {channel_login} не найден")
            return
        
        channel_data = channel_response.json().get("data", [])
        if not channel_data:
            print(f"❌ Канал {channel_login} не найден")
            return
        
        channel_id = channel_data[0]["id"]
        
        # Проверить, что канал стримит
        stream_response = requests.get(
            f"{self.twitch_api_base}/streams",
            headers=headers,
            params={"user_id": channel_id}
        )
        
        if stream_response.status_code == 200:
            streams = stream_response.json().get("data", [])
            if streams:
                print(f"✅ Канал {channel_login} онлайн: {streams[0]['game_name']}")
                
                # Имитация просмотра
                watch_intervals = minutes * 60 // 30  # каждые 30 секунд
                for i in range(watch_intervals):
                    if not self.running:
                        break
                    time.sleep(30)
                    progress = (i + 1) * 30 / (minutes * 60) * 100
                    print(f"⏱️  Прогресс просмотра: {progress:.1f}%")
                
                print(f"✅ Просмотр завершен: {channel_login}")
            else:
                print(f"❌ Канал {channel_login} не стримит")
        else:
            print(f"❌ Ошибка проверки стрима: {stream_response.status_code}")
    
    def process_account_drops(self, account_data: Dict):
        """Обрабатывает дропы для одного аккаунта"""
        username = account_data["username"]
        access_token = account_data["access_token"]
        
        print(f"\n🔄 Проверка дропов для: {username}")
        
        # Получить активные кампании
        campaigns = self.get_drops_campaigns(access_token)
        
        if not campaigns:
            print(f"📭 Нет активных кампаний дропов для {username}")
            return
        
        print(f"📋 Найдено {len(campaigns)} активных кампаний")
        
        for campaign in campaigns:
            campaign_name = campaign.get("name", "Неизвестная кампания")
            game_name = campaign.get("game", {}).get("displayName", "Неизвестная игра")
            
            print(f"\n🎮 Кампания: {campaign_name} ({game_name})")
            
            campaign_self = campaign.get("self", {})
            if not campaign_self.get("isAccountConnected", False):
                print("❌ Аккаунт не подключен к кампании")
                continue
            
            drops = campaign_self.get("drops", [])
            
            for drop in drops:
                drop_name = drop.get("name", "Неизвестный дроп")
                required_minutes = drop.get("requiredMinutesWatched", 0)
                
                drop_self = drop.get("self", {})
                current_minutes = drop_self.get("currentMinutesWatched", 0)
                is_claimed = drop_self.get("isClaimed", False)
                drop_instance_id = drop_self.get("dropInstanceID")
                
                print(f"💎 Дроп: {drop_name}")
                print(f"⏰ Прогресс: {current_minutes}/{required_minutes} минут")
                
                if is_claimed:
                    print("✅ Дроп уже получен")
                elif current_minutes >= required_minutes and drop_instance_id:
                    print("🎁 Дроп готов к получению!")
                    if self.claim_drop(access_token, drop_instance_id):
                        print("✅ Дроп успешно получен!")
                    else:
                        print("❌ Ошибка получения дропа")
                else:
                    remaining_minutes = required_minutes - current_minutes
                    print(f"⏳ Осталось смотреть: {remaining_minutes} минут")
    
    def run_drops_monitoring(self):
        """Запускает мониторинг дропов для всех аккаунтов"""
        print("\n🚀 Запуск мониторинга дропов...")
        self.running = True
        
        check_interval = self.config.get("settings", {}).get("check_interval", 60)
        
        while self.running:
            try:
                print(f"\n📊 Проверка дропов - {datetime.now().strftime('%H:%M:%S')}")
                
                for account_data in self.config.get("accounts", []):
                    if not self.running:
                        break
                    
                    # Проверить токен и обновить если нужно
                    if account_data.get("refresh_token"):
                        refresh_result = self.refresh_token(account_data["refresh_token"])
                        if refresh_result:
                            account_data["access_token"] = refresh_result["access_token"]
                    
                    self.process_account_drops(account_data)
                    
                    # Небольшая пауза между аккаунтами
                    time.sleep(2)
                
                # Сохранить обновленную конфигурацию
                self.save_config()
                
                if self.running:
                    print(f"\n💤 Следующая проверка через {check_interval} секунд...")
                    time.sleep(check_interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Получен сигнал остановки...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Ошибка мониторинга: {str(e)}")
                time.sleep(30)
        
        print("🔚 Мониторинг дропов остановлен")
    
    def add_account(self, username: str):
        """Добавляет новый аккаунт"""
        print(f"\n➕ Добавление аккаунта: {username}")
        
        # Проверить, что аккаунт не существует
        existing_accounts = [acc["username"] for acc in self.config.get("accounts", [])]
        if username in existing_accounts:
            print(f"❌ Аккаунт {username} уже существует")
            return False
        
        # Авторизовать аккаунт
        account_data = self.authenticate_account(username)
        if not account_data:
            print(f"❌ Не удалось авторизовать аккаунт {username}")
            return False
        
        # Добавить в конфигурацию
        if "accounts" not in self.config:
            self.config["accounts"] = []
        
        self.config["accounts"].append(account_data)
        self.save_config()
        
        print(f"✅ Аккаунт {username} успешно добавлен")
        return True
    
    def remove_account(self, username: str):
        """Удаляет аккаунт"""
        print(f"\n➖ Удаление аккаунта: {username}")
        
        accounts = self.config.get("accounts", [])
        initial_count = len(accounts)
        
        self.config["accounts"] = [acc for acc in accounts if acc["username"] != username]
        
        if len(self.config["accounts"]) < initial_count:
            self.save_config()
            print(f"✅ Аккаунт {username} удален")
            return True
        else:
            print(f"❌ Аккаунт {username} не найден")
            return False
    
    def list_accounts(self):
        """Показывает список аккаунтов"""
        accounts = self.config.get("accounts", [])
        
        if not accounts:
            print("📭 Нет добавленных аккаунтов")
            return
        
        print(f"\n👥 Список аккаунтов ({len(accounts)}):")
        for i, account in enumerate(accounts, 1):
            username = account.get("username", "Неизвестный")
            auth_date = account.get("authenticated_at", "Неизвестно")
            print(f"{i}. {username} (авторизован: {auth_date[:10]})")
    
    def show_menu(self):
        """Показывает главное меню"""
        print("\n" + "="*50)
        print("🎮 TWITCH DROPS MINER - ГЛАВНОЕ МЕНЮ")
        print("="*50)
        print("1. 👥 Управление аккаунтами")
        print("2. 🚀 Запустить мониторинг дропов")
        print("3. ⚙️  Настройки")
        print("4. 📊 Статистика")
        print("5. ❌ Выход")
        print("="*50)
    
    def show_accounts_menu(self):
        """Показывает меню управления аккаунтами"""
        print("\n" + "="*50)
        print("👥 УПРАВЛЕНИЕ АККАУНТАМИ")
        print("="*50)
        print("1. ➕ Добавить аккаунт")
        print("2. ➖ Удалить аккаунт")
        print("3. 📋 Показать все аккаунты")
        print("4. 🔄 Обновить токены")
        print("5. 🔙 Назад")
        print("="*50)
    
    def show_settings_menu(self):
        """Показывает меню настроек"""
        settings = self.config.get("settings", {})
        
        print("\n" + "="*50)
        print("⚙️  НАСТРОЙКИ")
        print("="*50)
        print(f"1. Интервал проверки: {settings.get('check_interval', 60)} секунд")
        print(f"2. Автоматическое получение дропов: {'Да' if settings.get('auto_claim_drops', True) else 'Нет'}")
        print(f"3. Время просмотра: {settings.get('watch_time_minutes', 30)} минут")
        print("4. 🔙 Назад")
        print("="*50)
    
    def run(self):
        """Главный цикл программы"""
        print("🎯 Добро пожаловать в Twitch Drops Miner!")
        print("📝 Упрощенная версия для автоматического получения дропов")
        
        while True:
            try:
                self.show_menu()
                choice = input("➡️  Выберите действие (1-5): ").strip()
                
                if choice == "1":
                    self.manage_accounts()
                elif choice == "2":
                    accounts = self.config.get("accounts", [])
                    if not accounts:
                        print("❌ Нет добавленных аккаунтов. Добавьте аккаунты сначала.")
                        continue
                    self.run_drops_monitoring()
                elif choice == "3":
                    self.manage_settings()
                elif choice == "4":
                    self.show_statistics()
                elif choice == "5":
                    print("👋 До свидания!")
                    break
                else:
                    print("❌ Неверный выбор. Попробуйте еще раз.")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Программа остановлена пользователем")
                break
            except Exception as e:
                print(f"❌ Ошибка: {str(e)}")
                time.sleep(2)
    
    def manage_accounts(self):
        """Управление аккаунтами"""
        while True:
            try:
                self.show_accounts_menu()
                choice = input("➡️  Выберите действие (1-5): ").strip()
                
                if choice == "1":
                    username = input("📝 Введите имя пользователя: ").strip()
                    if username:
                        if len(self.config.get("accounts", [])) >= 20:
                            print("❌ Максимальное количество аккаунтов: 20")
                        else:
                            self.add_account(username)
                    else:
                        print("❌ Имя пользователя не может быть пустым")
                        
                elif choice == "2":
                    self.list_accounts()
                    username = input("📝 Введите имя пользователя для удаления: ").strip()
                    if username:
                        self.remove_account(username)
                    else:
                        print("❌ Имя пользователя не может быть пустым")
                        
                elif choice == "3":
                    self.list_accounts()
                    input("\n⏎ Нажмите Enter для продолжения...")
                    
                elif choice == "4":
                    self.refresh_all_tokens()
                    
                elif choice == "5":
                    break
                else:
                    print("❌ Неверный выбор. Попробуйте еще раз.")
                    
            except KeyboardInterrupt:
                print("\n🔙 Возврат в главное меню...")
                break
    
    def manage_settings(self):
        """Управление настройками"""
        while True:
            try:
                self.show_settings_menu()
                choice = input("➡️  Выберите настройку (1-4): ").strip()
                
                if choice == "1":
                    try:
                        interval = int(input("📝 Введите интервал проверки (секунды): ").strip())
                        if interval >= 30:
                            self.config["settings"]["check_interval"] = interval
                            self.save_config()
                            print("✅ Настройка сохранена")
                        else:
                            print("❌ Минимальный интервал: 30 секунд")
                    except ValueError:
                        print("❌ Введите число")
                        
                elif choice == "2":
                    current = self.config.get("settings", {}).get("auto_claim_drops", True)
                    new_value = not current
                    self.config["settings"]["auto_claim_drops"] = new_value
                    self.save_config()
                    print(f"✅ Автоматическое получение дропов: {'Включено' if new_value else 'Выключено'}")
                    
                elif choice == "3":
                    try:
                        minutes = int(input("📝 Введите время просмотра (минуты): ").strip())
                        if minutes >= 1:
                            self.config["settings"]["watch_time_minutes"] = minutes
                            self.save_config()
                            print("✅ Настройка сохранена")
                        else:
                            print("❌ Минимальное время: 1 минута")
                    except ValueError:
                        print("❌ Введите число")
                        
                elif choice == "4":
                    break
                else:
                    print("❌ Неверный выбор. Попробуйте еще раз.")
                    
            except KeyboardInterrupt:
                print("\n🔙 Возврат в главное меню...")
                break
    
    def refresh_all_tokens(self):
        """Обновляет токены для всех аккаунтов"""
        print("\n🔄 Обновление токенов...")
        
        accounts = self.config.get("accounts", [])
        if not accounts:
            print("❌ Нет аккаунтов для обновления")
            return
        
        updated_count = 0
        for account in accounts:
            username = account.get("username", "Неизвестный")
            refresh_token = account.get("refresh_token")
            
            if refresh_token:
                print(f"🔄 Обновление токена для {username}...")
                refresh_result = self.refresh_token(refresh_token)
                
                if refresh_result:
                    account["access_token"] = refresh_result["access_token"]
                    if "refresh_token" in refresh_result:
                        account["refresh_token"] = refresh_result["refresh_token"]
                    updated_count += 1
                    print(f"✅ Токен обновлен для {username}")
                else:
                    print(f"❌ Не удалось обновить токен для {username}")
            else:
                print(f"❌ Нет refresh token для {username}")
        
        if updated_count > 0:
            self.save_config()
            print(f"✅ Обновлено токенов: {updated_count}")
        else:
            print("❌ Не удалось обновить ни одного токена")
    
    def show_statistics(self):
        """Показывает статистику"""
        accounts = self.config.get("accounts", [])
        
        print("\n" + "="*50)
        print("📊 СТАТИСТИКА")
        print("="*50)
        print(f"👥 Всего аккаунтов: {len(accounts)}")
        print(f"⚙️  Интервал проверки: {self.config.get('settings', {}).get('check_interval', 60)} сек")
        print(f"🎁 Автоматическое получение: {'Да' if self.config.get('settings', {}).get('auto_claim_drops', True) else 'Нет'}")
        print(f"⏰ Время просмотра: {self.config.get('settings', {}).get('watch_time_minutes', 30)} мин")
        print("="*50)
        
        if accounts:
            print("📋 Аккаунты:")
            for i, account in enumerate(accounts, 1):
                username = account.get("username", "Неизвестный")
                auth_date = account.get("authenticated_at", "Неизвестно")
                print(f"{i}. {username} (авторизован: {auth_date[:16]})")
        
        input("\n⏎ Нажмите Enter для продолжения...")


def main():
    """Главная функция"""
    try:
        miner = TwitchDropsMiner()
        miner.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Программа остановлена пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        print("🔧 Обратитесь к разработчику")


if __name__ == "__main__":
    main()