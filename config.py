# -*- coding: utf-8 -*-
"""
Конфигурация для Twitch Drop Miner - упрощенная версия
Только для получения дропов Wuthering Waves
"""

# Настройки аккаунтов (5-10 аккаунтов)
ACCOUNTS = [
    {
        "username": "your_username_1",
        "password": "your_password_1",
        "enabled": True
    },
    {
        "username": "your_username_2", 
        "password": "your_password_2",
        "enabled": True
    },
    {
        "username": "your_username_3",
        "password": "your_password_3", 
        "enabled": True
    },
    {
        "username": "your_username_4",
        "password": "your_password_4",
        "enabled": True
    },
    {
        "username": "your_username_5",
        "password": "your_password_5",
        "enabled": True
    },
    # Добавьте больше аккаунтов по необходимости
]

# Настройки для дропов
DROP_SETTINGS = {
    "game_name": "Wuthering Waves",  # Название игры для дропов
    "auto_claim": True,  # Автоматически забирать дропы
    "check_interval": 300,  # Проверять дропы каждые 5 минут
    "claim_from_inventory": True,  # Забирать дропы из инвентаря при запуске
}

# Настройки стримеров 
STREAMER_SETTINGS = {
    "auto_discover": True,  # Автоматически находить стримеров с дропами
    "manual_streamers": [
        # Добавьте конкретных стримеров, если нужно
        # "streamer_name_1",
        # "streamer_name_2",
    ],
    "max_streamers": 50,  # Максимальное количество стримеров для отслеживания
    "priority_streamers": [
        # Приоритетные стримеры (будут выбраны в первую очередь)
        # "priority_streamer_1",
        # "priority_streamer_2",
    ]
}

# Настройки логирования
LOGGING_SETTINGS = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "save_to_file": True,
    "file_path": "./logs/",
    "console_output": True,
    "show_emoji": True,
    "russian_messages": True,
}

# Технические настройки
TECHNICAL_SETTINGS = {
    "request_timeout": 30,  # Таймаут запросов в секундах
    "retry_attempts": 3,  # Количество попыток повторных запросов
    "sleep_between_accounts": 5,  # Пауза между аккаунтами в секундах
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "twitch_client_id": "kimne78kx3ncx6brgo4mv6wki5h1ko",  # Публичный Client ID Twitch
}

# Не изменяйте эти константы
TWITCH_ENDPOINTS = {
    "gql_url": "https://gql.twitch.tv/gql",
    "login_url": "https://www.twitch.tv/login",
    "spade_url": "https://video-weaver.twitch.tv/",
}