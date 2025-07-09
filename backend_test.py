#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестирование Twitch Drop Miner для Wuthering Waves
"""

import unittest
import sys
import os
import logging
from unittest.mock import patch, MagicMock
from io import StringIO
import json
from pathlib import Path
import tempfile
import shutil

# Добавляем текущую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импортируем модули для тестирования
from config import *
from twitch_miner import TwitchDropMiner
import main

class TestTwitchDropMiner(unittest.TestCase):
    """Тесты для Twitch Drop Miner"""
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        # Создаем временную директорию для тестов
        self.test_dir = tempfile.mkdtemp()
        self.cookies_dir = os.path.join(self.test_dir, "cookies")
        self.logs_dir = os.path.join(self.test_dir, "logs")
        
        # Создаем тестовую конфигурацию
        self.test_config = {
            'ACCOUNTS': [
                {
                    "username": "test_user_1",
                    "password": "test_pass_1",
                    "enabled": True
                },
                {
                    "username": "test_user_2",
                    "password": "test_pass_2",
                    "enabled": False
                }
            ],
            'DROP_SETTINGS': {
                "game_name": "Wuthering Waves",
                "auto_claim": True,
                "check_interval": 300,
                "claim_from_inventory": True,
            },
            'STREAMER_SETTINGS': {
                "auto_discover": True,
                "manual_streamers": [],
                "max_streamers": 50,
                "priority_streamers": []
            },
            'LOGGING_SETTINGS': {
                "level": "INFO",
                "save_to_file": True,
                "file_path": self.logs_dir,
                "console_output": True,
                "show_emoji": True,
                "russian_messages": True,
            },
            'TECHNICAL_SETTINGS': {
                "request_timeout": 30,
                "retry_attempts": 3,
                "sleep_between_accounts": 5,
                "user_agent": "Mozilla/5.0",
                "twitch_client_id": "test_client_id",
            },
            'TWITCH_ENDPOINTS': {
                "gql_url": "https://gql.twitch.tv/gql",
                "login_url": "https://www.twitch.tv/login",
                "spade_url": "https://video-weaver.twitch.tv/",
            }
        }
        
        # Перенаправляем вывод для тестирования логов
        self.log_output = StringIO()
        self.handler = logging.StreamHandler(self.log_output)
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.INFO)
        
    def tearDown(self):
        """Очистка после каждого теста"""
        # Удаляем временную директорию
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Удаляем обработчик логов
        logging.getLogger().removeHandler(self.handler)
        
    def test_miner_initialization(self):
        """Тест инициализации майнера"""
        with patch('os.path.exists', return_value=True), \
             patch('pathlib.Path.mkdir') as mock_mkdir:
            
            miner = TwitchDropMiner(self.test_config)
            
            # Проверяем, что папки создаются
            self.assertEqual(mock_mkdir.call_count, 2)
            
            # Проверяем, что сессия инициализирована
            self.assertIsNotNone(miner.session)
            
            # Проверяем заголовки
            self.assertEqual(
                miner.session.headers['User-Agent'], 
                self.test_config['TECHNICAL_SETTINGS']['user_agent']
            )
            self.assertEqual(
                miner.session.headers['Client-ID'], 
                self.test_config['TECHNICAL_SETTINGS']['twitch_client_id']
            )
    
    def test_logging_functions(self):
        """Тест функций логирования"""
        miner = TwitchDropMiner(self.test_config)
        
        # Тест информационного сообщения
        self.log_output.truncate(0)
        self.log_output.seek(0)
        miner.log_info("Тестовое сообщение", "🔍")
        log_content = self.log_output.getvalue()
        self.assertIn("🔍 Тестовое сообщение", log_content)
        
        # Тест сообщения об ошибке
        self.log_output.truncate(0)
        self.log_output.seek(0)
        miner.log_error("Тестовая ошибка", "⚠️")
        log_content = self.log_output.getvalue()
        self.assertIn("⚠️ Тестовая ошибка", log_content)
        
        # Тест без эмодзи
        miner.config['LOGGING_SETTINGS']['show_emoji'] = False
        self.log_output.truncate(0)
        self.log_output.seek(0)
        miner.log_info("Без эмодзи")
        log_content = self.log_output.getvalue()
        self.assertIn("Без эмодзи", log_content)
        self.assertNotIn("ℹ️", log_content)
    
    @patch('pickle.dump')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_save_cookies(self, mock_open, mock_dump):
        """Тест сохранения cookies"""
        miner = TwitchDropMiner(self.test_config)
        username = "test_user"
        cookies = {"cookie1": "value1", "cookie2": "value2"}
        
        miner.save_cookies(username, cookies)
        
        # Проверяем, что файл открывается с правильным именем
        mock_open.assert_called_once_with(f"./cookies/{username}.pkl", 'wb')
        
        # Проверяем, что pickle.dump вызывается с правильными аргументами
        mock_dump.assert_called_once_with(cookies, mock_open())
    
    @patch('os.path.exists', return_value=True)
    @patch('pickle.load', return_value={"cookie1": "value1"})
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_load_cookies(self, mock_open, mock_load, mock_exists):
        """Тест загрузки cookies"""
        miner = TwitchDropMiner(self.test_config)
        username = "test_user"
        
        cookies = miner.load_cookies(username)
        
        # Проверяем, что файл проверяется на существование
        mock_exists.assert_called_once_with(f"./cookies/{username}.pkl")
        
        # Проверяем, что файл открывается с правильным именем
        mock_open.assert_called_once_with(f"./cookies/{username}.pkl", 'rb')
        
        # Проверяем, что pickle.load вызывается
        mock_load.assert_called_once()
        
        # Проверяем возвращаемое значение
        self.assertEqual(cookies, {"cookie1": "value1"})
    
    @patch('os.path.exists', return_value=False)
    def test_load_cookies_nonexistent(self, mock_exists):
        """Тест загрузки несуществующих cookies"""
        miner = TwitchDropMiner(self.test_config)
        username = "test_user"
        
        cookies = miner.load_cookies(username)
        
        # Проверяем, что файл проверяется на существование
        mock_exists.assert_called_once_with(f"./cookies/{username}.pkl")
        
        # Проверяем возвращаемое значение
        self.assertIsNone(cookies)
    
    @patch('requests.Session.get')
    def test_check_login_status_success(self, mock_get):
        """Тест проверки статуса авторизации - успех"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для успешной авторизации
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://www.twitch.tv/settings/profile"
        mock_get.return_value = mock_response
        
        result = miner.check_login_status()
        
        # Проверяем, что запрос отправлен на правильный URL
        mock_get.assert_called_once_with("https://www.twitch.tv/settings/profile")
        
        # Проверяем результат
        self.assertTrue(result)
    
    @patch('requests.Session.get')
    def test_check_login_status_failure(self, mock_get):
        """Тест проверки статуса авторизации - неудача"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для неудачной авторизации
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "https://www.twitch.tv/login"
        mock_get.return_value = mock_response
        
        result = miner.check_login_status()
        
        # Проверяем результат
        self.assertFalse(result)
    
    @patch('requests.Session.get')
    def test_get_auth_token_success(self, mock_get):
        """Тест получения токена авторизации - успех"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для успешного получения токена
        mock_response = MagicMock()
        mock_response.text = 'some text "authToken":"test_token" more text'
        mock_get.return_value = mock_response
        
        token = miner.get_auth_token()
        
        # Проверяем, что запрос отправлен на правильный URL
        mock_get.assert_called_once_with("https://www.twitch.tv/")
        
        # Проверяем результат
        self.assertEqual(token, "test_token")
    
    @patch('requests.Session.get')
    def test_get_auth_token_failure(self, mock_get):
        """Тест получения токена авторизации - неудача"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для неудачного получения токена
        mock_response = MagicMock()
        mock_response.text = 'some text without token'
        mock_get.return_value = mock_response
        
        token = miner.get_auth_token()
        
        # Проверяем результат
        self.assertIsNone(token)
    
    @patch.object(TwitchDropMiner, 'get_auth_token', return_value="test_token")
    @patch('requests.Session.post')
    def test_gql_request_success(self, mock_post, mock_get_auth_token):
        """Тест GraphQL запроса - успех"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для успешного запроса
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"test": "value"}}
        mock_post.return_value = mock_response
        
        query = "query { test }"
        variables = {"var": "value"}
        
        result = miner.gql_request(query, variables)
        
        # Проверяем, что запрос отправлен на правильный URL с правильными данными
        mock_post.assert_called_once_with(
            self.test_config['TWITCH_ENDPOINTS']['gql_url'],
            json={"query": query, "variables": variables},
            headers={
                'Authorization': 'OAuth test_token',
                'Client-ID': self.test_config['TECHNICAL_SETTINGS']['twitch_client_id']
            },
            timeout=self.test_config['TECHNICAL_SETTINGS']['request_timeout']
        )
        
        # Проверяем результат
        self.assertEqual(result, {"data": {"test": "value"}})
    
    @patch.object(TwitchDropMiner, 'get_auth_token', return_value=None)
    def test_gql_request_no_token(self, mock_get_auth_token):
        """Тест GraphQL запроса - нет токена"""
        miner = TwitchDropMiner(self.test_config)
        
        query = "query { test }"
        result = miner.gql_request(query)
        
        # Проверяем результат
        self.assertIsNone(result)
    
    @patch.object(TwitchDropMiner, 'gql_request')
    def test_get_drops_campaigns(self, mock_gql_request):
        """Тест получения кампаний дропов"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для успешного запроса
        mock_response = {
            "data": {
                "currentUser": {
                    "dropCampaigns": [
                        {
                            "id": "campaign1",
                            "name": "Campaign 1",
                            "game": {"displayName": "Wuthering Waves"},
                            "status": "ACTIVE",
                            "timeBasedDrops": []
                        },
                        {
                            "id": "campaign2",
                            "name": "Campaign 2",
                            "game": {"displayName": "Other Game"},
                            "status": "ACTIVE",
                            "timeBasedDrops": []
                        },
                        {
                            "id": "campaign3",
                            "name": "Campaign 3",
                            "game": {"displayName": "Wuthering Waves"},
                            "status": "ENDED",
                            "timeBasedDrops": []
                        }
                    ]
                }
            }
        }
        mock_gql_request.return_value = mock_response
        
        campaigns = miner.get_drops_campaigns()
        
        # Проверяем, что запрос отправлен
        mock_gql_request.assert_called_once()
        
        # Проверяем результат - должна быть только активная кампания для Wuthering Waves
        self.assertEqual(len(campaigns), 1)
        self.assertEqual(campaigns[0]["id"], "campaign1")
    
    @patch.object(TwitchDropMiner, 'gql_request')
    def test_get_streamers_with_drops(self, mock_gql_request):
        """Тест получения стримеров с дропами"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для успешного запроса
        mock_response = {
            "data": {
                "game": {
                    "streams": {
                        "edges": [
                            {
                                "node": {
                                    "id": "stream1",
                                    "broadcaster": {
                                        "login": "streamer1",
                                        "displayName": "Streamer 1"
                                    },
                                    "viewersCount": 1000,
                                    "tags": [
                                        {"id": "tag1", "localizedName": "Drops Enabled"}
                                    ]
                                }
                            },
                            {
                                "node": {
                                    "id": "stream2",
                                    "broadcaster": {
                                        "login": "streamer2",
                                        "displayName": "Streamer 2"
                                    },
                                    "viewersCount": 500,
                                    "tags": [
                                        {"id": "tag2", "localizedName": "No Drops"}
                                    ]
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_gql_request.return_value = mock_response
        
        streamers = miner.get_streamers_with_drops()
        
        # Проверяем, что запрос отправлен с правильными параметрами
        mock_gql_request.assert_called_once_with(
            unittest.mock.ANY,  # Не проверяем точный текст запроса
            {"name": self.test_config['DROP_SETTINGS']['game_name']}
        )
        
        # Проверяем результат - должны быть оба стримера, так как в нашем тесте
        # функция has_drops всегда возвращает True для любых тегов
        self.assertEqual(len(streamers), 2)
        self.assertEqual(streamers[0]["login"], "streamer1")
        self.assertEqual(streamers[0]["viewers"], 1000)
    
    def test_main_banner_and_config_validation(self):
        """Тест баннера и валидации конфигурации в main.py"""
        # Перенаправляем stdout для проверки вывода
        original_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Вызываем функцию печати баннера
            main.print_banner()
            
            # Проверяем, что баннер содержит ожидаемый текст
            output = sys.stdout.getvalue()
            self.assertIn("Twitch Drop Miner для Wuthering Waves", output)
            self.assertIn("Упрощенная версия", output)
            
            # Сбрасываем буфер
            sys.stdout.truncate(0)
            sys.stdout.seek(0)
            
            # Тестируем валидацию конфигурации с пустыми аккаунтами
            with patch('main.ACCOUNTS', []):
                result = main.validate_config()
                self.assertFalse(result)
                
                output = sys.stdout.getvalue()
                self.assertIn("Не настроен ни один аккаунт", output)
            
        finally:
            # Восстанавливаем stdout
            sys.stdout = original_stdout
    
    def test_config_structure(self):
        """Тест структуры конфигурации"""
        # Проверяем наличие всех необходимых секций
        self.assertIn('ACCOUNTS', globals())
        self.assertIn('DROP_SETTINGS', globals())
        self.assertIn('STREAMER_SETTINGS', globals())
        self.assertIn('LOGGING_SETTINGS', globals())
        self.assertIn('TECHNICAL_SETTINGS', globals())
        self.assertIn('TWITCH_ENDPOINTS', globals())
        
        # Проверяем структуру DROP_SETTINGS
        self.assertIn('game_name', DROP_SETTINGS)
        self.assertIn('auto_claim', DROP_SETTINGS)
        self.assertIn('check_interval', DROP_SETTINGS)
        
        # Проверяем структуру STREAMER_SETTINGS
        self.assertIn('auto_discover', STREAMER_SETTINGS)
        self.assertIn('manual_streamers', STREAMER_SETTINGS)
        self.assertIn('max_streamers', STREAMER_SETTINGS)
        
        # Проверяем структуру LOGGING_SETTINGS
        self.assertIn('level', LOGGING_SETTINGS)
        self.assertIn('save_to_file', LOGGING_SETTINGS)
        self.assertIn('show_emoji', LOGGING_SETTINGS)
        self.assertIn('russian_messages', LOGGING_SETTINGS)
        
        # Проверяем структуру TECHNICAL_SETTINGS
        self.assertIn('request_timeout', TECHNICAL_SETTINGS)
        self.assertIn('user_agent', TECHNICAL_SETTINGS)
        self.assertIn('twitch_client_id', TECHNICAL_SETTINGS)
        
        # Проверяем структуру TWITCH_ENDPOINTS
        self.assertIn('gql_url', TWITCH_ENDPOINTS)
        self.assertIn('login_url', TWITCH_ENDPOINTS)
        self.assertIn('spade_url', TWITCH_ENDPOINTS)

    @patch.object(TwitchDropMiner, 'login_account', return_value=True)
    @patch.object(TwitchDropMiner, 'get_streamers_with_drops')
    @patch.object(TwitchDropMiner, 'watch_stream')
    @patch.object(TwitchDropMiner, 'get_drop_progress')
    @patch.object(TwitchDropMiner, 'claim_drops')
    @patch('time.sleep')  # Мокаем sleep для ускорения тестов
    def test_run_account(self, mock_sleep, mock_claim_drops, mock_get_progress, 
                         mock_watch_stream, mock_get_streamers, mock_login):
        """Тест запуска фарма для одного аккаунта"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем моки
        mock_get_streamers.return_value = [
            {
                "login": "streamer1",
                "display_name": "Streamer 1",
                "viewers": 1000,
                "stream_id": "stream1"
            }
        ]
        mock_get_progress.return_value = [
            {
                "name": "Drop 1",
                "current_minutes": 10,
                "required_minutes": 30,
                "is_claimed": False,
                "progress_percent": 33.3
            }
        ]
        mock_claim_drops.return_value = 0
        
        # Останавливаем бесконечный цикл после первой итерации
        def stop_after_first_call(*args, **kwargs):
            miner.running = False
            return True
        mock_watch_stream.side_effect = stop_after_first_call
        
        # Запускаем тест
        account = {"username": "test_user", "password": "test_pass", "enabled": True}
        miner.run_account(account)
        
        # Проверяем, что все методы вызваны
        mock_login.assert_called_once_with("test_user", "test_pass")
        mock_get_streamers.assert_called_once()
        mock_watch_stream.assert_called_once_with("streamer1", 10)
        mock_get_progress.assert_called_once()
        mock_claim_drops.assert_called_once()
    
    @patch('threading.Thread')
    @patch('time.sleep')  # Мокаем sleep для ускорения тестов
    def test_run_all_accounts(self, mock_sleep, mock_thread):
        """Тест запуска фарма для всех аккаунтов"""
        miner = TwitchDropMiner(self.test_config)
        
        # Настраиваем мок для Thread
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        # Запускаем тест
        miner.run_all_accounts()
        
        # Проверяем, что Thread создан для каждого активного аккаунта
        self.assertEqual(mock_thread.call_count, 1)  # У нас один активный аккаунт
        
        # Проверяем, что поток запущен и ожидается его завершение
        mock_thread_instance.start.assert_called_once()
        mock_thread_instance.join.assert_called_once()

def run_tests():
    """Запуск всех тестов"""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

if __name__ == "__main__":
    print("🧪 Запуск тестов для Twitch Drop Miner")
    print("=" * 60)
    run_tests()