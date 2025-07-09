#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitch Drop Miner - Упрощенная версия для Wuthering Waves
Автор: AI Assistant
Версия: 1.0

Использование:
    python main.py

Описание:
    Упрощенная версия Twitch-Channel-Points-Miner-v2 специально для фарма дропов Wuthering Waves.
    Поддерживает несколько аккаунтов одновременно.
    
    Основные функции:
    - Авторизация через логин/пароль
    - Автоматический поиск стримеров с дропами
    - Просмотр стримов для получения дропов
    - Автоматическое получение дропов
    - Поддержка нескольких аккаунтов
    - Логирование на русском языке
"""

import sys
import os
import time
import signal
from datetime import datetime

# Добавляем текущую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import *
from twitch_miner import TwitchDropMiner

def print_banner():
    """Выводит баннер программы"""
    banner = """
    ╔══════════════════════════════════════════════════════════════════════════════════════╗
    ║                          🎮 Twitch Drop Miner для Wuthering Waves 🎮                ║
    ║                                   Упрощенная версия                                  ║
    ║                                                                                      ║
    ║  Функции:                                                                            ║
    ║  ✅ Авторизация через логин/пароль                                                   ║
    ║  ✅ Автоматический поиск стримеров с дропами                                        ║
    ║  ✅ Просмотр стримов для получения дропов                                           ║
    ║  ✅ Автоматическое получение дропов                                                 ║
    ║  ✅ Поддержка нескольких аккаунтов                                                  ║
    ║  ✅ Логирование на русском языке                                                    ║
    ║                                                                                      ║
    ║  Внимание: Убедитесь, что настроили аккаунты в config.py!                          ║
    ╚══════════════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def validate_config():
    """Проверка конфигурации"""
    errors = []
    
    # Проверяем наличие аккаунтов
    if not ACCOUNTS:
        errors.append("❌ Не настроен ни один аккаунт в config.py")
    
    # Проверяем аккаунты
    enabled_accounts = [acc for acc in ACCOUNTS if acc['enabled']]
    if not enabled_accounts:
        errors.append("❌ Нет активных аккаунтов (enabled=True)")
    
    for i, account in enumerate(enabled_accounts):
        if not account.get('username') or not account.get('password'):
            errors.append(f"❌ Аккаунт {i+1}: не указан username или password")
    
    # Проверяем настройки игры
    if not DROP_SETTINGS.get('game_name'):
        errors.append("❌ Не указано название игры в DROP_SETTINGS")
    
    if errors:
        print("\n🚨 Ошибки в конфигурации:")
        for error in errors:
            print(f"  {error}")
        print("\nПожалуйста, исправьте ошибки в config.py и запустите снова.")
        return False
    
    return True

def print_config_info():
    """Выводит информацию о конфигурации"""
    enabled_accounts = [acc for acc in ACCOUNTS if acc['enabled']]
    
    print(f"\n📋 Конфигурация:")
    print(f"  🎮 Игра: {DROP_SETTINGS['game_name']}")
    print(f"  👥 Активных аккаунтов: {len(enabled_accounts)}")
    print(f"  🔄 Автоматический поиск стримеров: {'Да' if STREAMER_SETTINGS['auto_discover'] else 'Нет'}")
    print(f"  📦 Автоматическое получение дропов: {'Да' if DROP_SETTINGS['auto_claim'] else 'Нет'}")
    print(f"  📁 Логи сохраняются в: {LOGGING_SETTINGS['file_path']}")
    
    print(f"\n👤 Аккаунты:")
    for i, account in enumerate(enabled_accounts):
        print(f"  {i+1}. {account['username']}")

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print("\n\n⏹️ Получен сигнал завершения. Останавливаем фарм...")
    sys.exit(0)

def main():
    """Основная функция"""
    # Обработка сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Выводим баннер
    print_banner()
    
    # Проверяем конфигурацию
    if not validate_config():
        sys.exit(1)
    
    # Выводим информацию о конфигурации
    print_config_info()
    
    # Подтверждение запуска
    print(f"\n🚀 Запуск через 5 секунд...")
    print("   Нажмите Ctrl+C для отмены")
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        print("\n❌ Запуск отменен пользователем")
        sys.exit(0)
    
    # Создаем конфигурацию
    config = {
        'ACCOUNTS': ACCOUNTS,
        'DROP_SETTINGS': DROP_SETTINGS,
        'STREAMER_SETTINGS': STREAMER_SETTINGS,
        'LOGGING_SETTINGS': LOGGING_SETTINGS,
        'TECHNICAL_SETTINGS': TECHNICAL_SETTINGS,
        'TWITCH_ENDPOINTS': TWITCH_ENDPOINTS
    }
    
    # Создаем и запускаем майнер
    miner = TwitchDropMiner(config)
    
    try:
        print(f"\n🌟 Начинаем фарм дропов {DROP_SETTINGS['game_name']}!")
        print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        miner.run_all_accounts()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Фарм остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {str(e)}")
        sys.exit(1)
    finally:
        print(f"\n⏰ Время завершения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("👋 Спасибо за использование Twitch Drop Miner!")

if __name__ == "__main__":
    main()