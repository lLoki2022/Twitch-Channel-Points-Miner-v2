#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Test Suite for Twitch Drops Miner
Tests basic functionality without requiring real API calls or user interaction
"""

import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import importlib.util

# Add the app directory to Python path
sys.path.insert(0, '/app')

class TwitchDropsMinerTest:
    """Test suite for Twitch Drops Miner functionality"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        self.original_config_file = None
        
    def setup_test_environment(self):
        """Setup isolated test environment"""
        print("🔧 Настройка тестовой среды...")
        
        # Create temporary directory for test config
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, "test_config.json")
        
        print(f"📁 Временная директория: {self.temp_dir}")
        return True
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print("🧹 Тестовая среда очищена")
    
    def test_script_import(self):
        """Test 1: Проверка импорта скрипта без ошибок"""
        print("\n🧪 Тест 1: Импорт скрипта...")
        
        try:
            # Import the main script
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(twitch_module)
            
            # Check if main classes exist
            assert hasattr(twitch_module, 'TwitchDropsMiner'), "Класс TwitchDropsMiner не найден"
            assert hasattr(twitch_module, 'main'), "Функция main не найдена"
            
            self.test_results.append(("✅", "Импорт скрипта", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Импорт скрипта", f"Ошибка: {str(e)}"))
            return False
    
    def test_class_initialization(self):
        """Test 2: Проверка инициализации класса"""
        print("\n🧪 Тест 2: Инициализация класса...")
        
        try:
            # Import and initialize with test config
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            
            # Mock print to capture output
            with patch('builtins.print') as mock_print:
                spec.loader.exec_module(twitch_module)
                miner = twitch_module.TwitchDropsMiner(self.test_config_path)
            
            # Check initialization
            assert hasattr(miner, 'config'), "Атрибут config не найден"
            assert hasattr(miner, 'accounts'), "Атрибут accounts не найден"
            assert hasattr(miner, 'running'), "Атрибут running не найден"
            assert hasattr(miner, 'client_id'), "Атрибут client_id не найден"
            
            # Check if initialization messages were printed
            print_calls = [str(call) for call in mock_print.call_args_list]
            startup_messages = [call for call in print_calls if "Twitch Drops Miner" in call]
            assert len(startup_messages) > 0, "Сообщения запуска не найдены"
            
            self.test_results.append(("✅", "Инициализация класса", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Инициализация класса", f"Ошибка: {str(e)}"))
            return False
    
    def test_config_creation(self):
        """Test 3: Проверка создания конфигурации"""
        print("\n🧪 Тест 3: Создание конфигурации...")
        
        try:
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            
            with patch('builtins.print'):
                spec.loader.exec_module(twitch_module)
                miner = twitch_module.TwitchDropsMiner(self.test_config_path)
            
            # Check if config file was created
            assert os.path.exists(self.test_config_path), "Файл конфигурации не создан"
            
            # Check config content
            with open(self.test_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validate config structure
            assert "accounts" in config, "Секция accounts отсутствует"
            assert "settings" in config, "Секция settings отсутствует"
            assert isinstance(config["accounts"], list), "accounts должен быть списком"
            assert isinstance(config["settings"], dict), "settings должен быть словарем"
            
            # Check default settings
            settings = config["settings"]
            assert "check_interval" in settings, "check_interval отсутствует"
            assert "auto_claim_drops" in settings, "auto_claim_drops отсутствует"
            assert "watch_time_minutes" in settings, "watch_time_minutes отсутствует"
            assert "language" in settings, "language отсутствует"
            assert settings["language"] == "ru", "Язык должен быть русским"
            
            self.test_results.append(("✅", "Создание конфигурации", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Создание конфигурации", f"Ошибка: {str(e)}"))
            return False
    
    def test_menu_methods(self):
        """Test 4: Проверка методов отображения меню"""
        print("\n🧪 Тест 4: Методы отображения меню...")
        
        try:
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            
            with patch('builtins.print'):
                spec.loader.exec_module(twitch_module)
                miner = twitch_module.TwitchDropsMiner(self.test_config_path)
            
            # Test main menu
            with patch('builtins.print') as mock_print:
                miner.show_menu()
            
            menu_output = [str(call) for call in mock_print.call_args_list]
            menu_text = ' '.join(menu_output)
            
            # Check for Russian menu items
            assert "ГЛАВНОЕ МЕНЮ" in menu_text, "Главное меню не найдено"
            assert "Управление аккаунтами" in menu_text, "Пункт управления аккаунтами не найден"
            assert "Запустить мониторинг" in menu_text, "Пункт мониторинга не найден"
            assert "Настройки" in menu_text, "Пункт настроек не найден"
            assert "Статистика" in menu_text, "Пункт статистики не найден"
            assert "Выход" in menu_text, "Пункт выхода не найден"
            
            # Test accounts menu
            with patch('builtins.print') as mock_print:
                miner.show_accounts_menu()
            
            accounts_output = [str(call) for call in mock_print.call_args_list]
            accounts_text = ' '.join(accounts_output)
            
            assert "УПРАВЛЕНИЕ АККАУНТАМИ" in accounts_text, "Меню управления аккаунтами не найдено"
            assert "Добавить аккаунт" in accounts_text, "Пункт добавления аккаунта не найден"
            assert "Удалить аккаунт" in accounts_text, "Пункт удаления аккаунта не найден"
            
            # Test settings menu
            with patch('builtins.print') as mock_print:
                miner.show_settings_menu()
            
            settings_output = [str(call) for call in mock_print.call_args_list]
            settings_text = ' '.join(settings_output)
            
            assert "НАСТРОЙКИ" in settings_text, "Меню настроек не найдено"
            assert "Интервал проверки" in settings_text, "Настройка интервала не найдена"
            assert "Автоматическое получение" in settings_text, "Настройка автополучения не найдена"
            
            self.test_results.append(("✅", "Методы отображения меню", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Методы отображения меню", f"Ошибка: {str(e)}"))
            return False
    
    def test_config_operations(self):
        """Test 5: Проверка операций с конфигурацией"""
        print("\n🧪 Тест 5: Операции с конфигурацией...")
        
        try:
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            
            with patch('builtins.print'):
                spec.loader.exec_module(twitch_module)
                miner = twitch_module.TwitchDropsMiner(self.test_config_path)
            
            # Test config loading
            original_config = miner.config.copy()
            
            # Test config modification
            miner.config["settings"]["check_interval"] = 120
            miner.config["settings"]["auto_claim_drops"] = False
            
            # Test config saving
            miner.save_config()
            
            # Verify changes were saved
            with open(self.test_config_path, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
            
            assert saved_config["settings"]["check_interval"] == 120, "Изменение интервала не сохранено"
            assert saved_config["settings"]["auto_claim_drops"] == False, "Изменение автополучения не сохранено"
            
            # Test config reloading
            new_miner = twitch_module.TwitchDropsMiner(self.test_config_path)
            assert new_miner.config["settings"]["check_interval"] == 120, "Конфигурация не загружена корректно"
            
            self.test_results.append(("✅", "Операции с конфигурацией", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Операции с конфигурацией", f"Ошибка: {str(e)}"))
            return False
    
    def test_account_management_methods(self):
        """Test 6: Проверка методов управления аккаунтами"""
        print("\n🧪 Тест 6: Методы управления аккаунтами...")
        
        try:
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            
            with patch('builtins.print'):
                spec.loader.exec_module(twitch_module)
                miner = twitch_module.TwitchDropsMiner(self.test_config_path)
            
            # Test list_accounts with empty list
            with patch('builtins.print') as mock_print:
                miner.list_accounts()
            
            output = [str(call) for call in mock_print.call_args_list]
            output_text = ' '.join(output)
            assert "Нет добавленных аккаунтов" in output_text, "Сообщение о пустом списке не найдено"
            
            # Test remove_account with non-existent account
            with patch('builtins.print') as mock_print:
                result = miner.remove_account("nonexistent")
            
            assert result == False, "Удаление несуществующего аккаунта должно возвращать False"
            
            # Test statistics display
            with patch('builtins.print') as mock_print:
                miner.show_statistics()
            
            stats_output = [str(call) for call in mock_print.call_args_list]
            stats_text = ' '.join(stats_output)
            
            assert "СТАТИСТИКА" in stats_text, "Заголовок статистики не найден"
            assert "Всего аккаунтов: 0" in stats_text, "Счетчик аккаунтов не найден"
            
            self.test_results.append(("✅", "Методы управления аккаунтами", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Методы управления аккаунтами", f"Ошибка: {str(e)}"))
            return False
    
    def test_error_handling(self):
        """Test 7: Проверка обработки ошибок"""
        print("\n🧪 Тест 7: Обработка ошибок...")
        
        try:
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            
            with patch('builtins.print'):
                spec.loader.exec_module(twitch_module)
            
            # Test loading non-existent config
            non_existent_path = os.path.join(self.temp_dir, "non_existent.json")
            
            with patch('builtins.print') as mock_print:
                miner = twitch_module.TwitchDropsMiner(non_existent_path)
            
            # Should create default config
            assert os.path.exists(non_existent_path), "Конфигурация по умолчанию не создана"
            
            # Test invalid JSON handling by creating corrupted config
            corrupted_path = os.path.join(self.temp_dir, "corrupted.json")
            with open(corrupted_path, 'w') as f:
                f.write("invalid json content")
            
            # This should handle the error gracefully
            try:
                with patch('builtins.print'):
                    miner = twitch_module.TwitchDropsMiner(corrupted_path)
                # If we get here, it handled the error
                error_handled = True
            except json.JSONDecodeError:
                # If JSON error propagates, that's also acceptable
                error_handled = True
            except Exception:
                error_handled = False
            
            assert error_handled, "Ошибка JSON не обработана корректно"
            
            self.test_results.append(("✅", "Обработка ошибок", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Обработка ошибок", f"Ошибка: {str(e)}"))
            return False
    
    def test_russian_interface(self):
        """Test 8: Проверка русского интерфейса"""
        print("\n🧪 Тест 8: Русский интерфейс...")
        
        try:
            spec = importlib.util.spec_from_file_location("twitch_drops_miner", "/app/twitch_drops_miner.py")
            twitch_module = importlib.util.module_from_spec(spec)
            
            with patch('builtins.print'):
                spec.loader.exec_module(twitch_module)
                miner = twitch_module.TwitchDropsMiner(self.test_config_path)
            
            # Collect all text output from various methods
            all_output = []
            
            # Capture menu outputs
            with patch('builtins.print') as mock_print:
                miner.show_menu()
                miner.show_accounts_menu()
                miner.show_settings_menu()
                miner.show_statistics()
                miner.list_accounts()
            
            all_output.extend([str(call) for call in mock_print.call_args_list])
            
            # Check for Russian text
            russian_text = ' '.join(all_output)
            
            # Check for key Russian words/phrases
            russian_phrases = [
                "ГЛАВНОЕ МЕНЮ",
                "Управление аккаунтами",
                "Настройки",
                "Статистика",
                "Выход",
                "Добавить аккаунт",
                "Удалить аккаунт",
                "Интервал проверки",
                "Автоматическое получение",
                "Всего аккаунтов",
                "Нет добавленных аккаунтов"
            ]
            
            missing_phrases = []
            for phrase in russian_phrases:
                if phrase not in russian_text:
                    missing_phrases.append(phrase)
            
            assert len(missing_phrases) == 0, f"Отсутствуют русские фразы: {missing_phrases}"
            
            # Check config language setting
            assert miner.config["settings"]["language"] == "ru", "Язык в настройках не русский"
            
            self.test_results.append(("✅", "Русский интерфейс", "Успешно"))
            return True
            
        except Exception as e:
            self.test_results.append(("❌", "Русский интерфейс", f"Ошибка: {str(e)}"))
            return False
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("🚀 Запуск тестирования Twitch Drops Miner...")
        print("=" * 60)
        
        # Setup test environment
        if not self.setup_test_environment():
            print("❌ Не удалось настроить тестовую среду")
            return False
        
        try:
            # Run all tests
            tests = [
                self.test_script_import,
                self.test_class_initialization,
                self.test_config_creation,
                self.test_menu_methods,
                self.test_config_operations,
                self.test_account_management_methods,
                self.test_error_handling,
                self.test_russian_interface
            ]
            
            passed = 0
            total = len(tests)
            
            for test in tests:
                if test():
                    passed += 1
            
            # Print results
            print("\n" + "=" * 60)
            print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
            print("=" * 60)
            
            for status, test_name, result in self.test_results:
                print(f"{status} {test_name}: {result}")
            
            print("=" * 60)
            print(f"✅ Пройдено: {passed}/{total}")
            print(f"❌ Провалено: {total - passed}/{total}")
            print(f"📈 Успешность: {(passed/total)*100:.1f}%")
            
            return passed == total
            
        finally:
            self.cleanup_test_environment()


def main():
    """Главная функция тестирования"""
    print("🎮 Тестирование Twitch Drops Miner")
    print("📝 Версия тестов: 1.0")
    print("🎯 Фокус: базовый функционал без API запросов\n")
    
    tester = TwitchDropsMinerTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Все тесты пройдены успешно!")
        return 0
    else:
        print("\n⚠️  Некоторые тесты провалены. Проверьте детали выше.")
        return 1


if __name__ == "__main__":
    exit(main())