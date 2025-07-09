# -*- coding: utf-8 -*-
"""
Twitch Drop Miner - упрощенная версия
Только для получения дропов Wuthering Waves
"""

import requests
import time
import random
import logging
import json
import re
import pickle
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('twitch_miner.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class TwitchDropMiner:
    """Основной класс для фарма дропов Twitch"""
    
    def __init__(self, config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config['TECHNICAL_SETTINGS']['user_agent'],
            'Client-ID': config['TECHNICAL_SETTINGS']['twitch_client_id']
        })
        
        # Создаем папки для cookies и логов
        Path("./cookies").mkdir(exist_ok=True)
        Path("./logs").mkdir(exist_ok=True)
        
        self.running = True
        self.accounts_data = {}
        
    def log_info(self, message: str, emoji: str = "ℹ️"):
        """Логирование с эмодзи"""
        if self.config['LOGGING_SETTINGS']['show_emoji']:
            logger.info(f"{emoji} {message}")
        else:
            logger.info(message)
            
    def log_error(self, message: str, emoji: str = "❌"):
        """Логирование ошибок"""
        if self.config['LOGGING_SETTINGS']['show_emoji']:
            logger.error(f"{emoji} {message}")
        else:
            logger.error(message)
            
    def save_cookies(self, username: str, cookies: dict):
        """Сохранение cookies в файл"""
        cookies_file = f"./cookies/{username}.pkl"
        with open(cookies_file, 'wb') as f:
            pickle.dump(cookies, f)
            
    def load_cookies(self, username: str) -> Optional[dict]:
        """Загрузка cookies из файла"""
        cookies_file = f"./cookies/{username}.pkl"
        if os.path.exists(cookies_file):
            try:
                with open(cookies_file, 'rb') as f:
                    return pickle.load(f)
            except:
                return None
        return None
        
    def login_account(self, username: str, password: str) -> bool:
        """Авторизация в аккаунте Twitch"""
        try:
            self.log_info(f"🔐 Авторизация для аккаунта {username}")
            
            # Загружаем cookies если есть
            cookies = self.load_cookies(username)
            if cookies:
                self.session.cookies.update(cookies)
                if self.check_login_status():
                    self.log_info(f"✅ Успешная авторизация через cookies для {username}")
                    return True
                    
            # Если cookies не работают, делаем обычную авторизацию
            login_page = self.session.get("https://www.twitch.tv/login")
            
            # Извлекаем необходимые данные для авторизации
            csrf_token = re.search(r'"csrf_token":"([^"]+)"', login_page.text)
            if not csrf_token:
                self.log_error(f"Не удалось найти CSRF токен для {username}")
                return False
                
            # Данные для авторизации
            login_data = {
                'username': username,
                'password': password,
                'csrf_token': csrf_token.group(1),
                'remember_me': 'true'
            }
            
            # Отправляем запрос авторизации
            response = self.session.post(
                "https://www.twitch.tv/login",
                data=login_data,
                allow_redirects=False
            )
            
            if response.status_code in [200, 302]:
                # Сохраняем cookies
                self.save_cookies(username, dict(self.session.cookies))
                self.log_info(f"✅ Успешная авторизация для {username}")
                return True
            else:
                self.log_error(f"Ошибка авторизации для {username}: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(f"Исключение при авторизации {username}: {str(e)}")
            return False
            
    def check_login_status(self) -> bool:
        """Проверка статуса авторизации"""
        try:
            response = self.session.get("https://www.twitch.tv/settings/profile")
            return response.status_code == 200 and "login" not in response.url
        except:
            return False
            
    def get_auth_token(self) -> Optional[str]:
        """Получение токена авторизации"""
        try:
            response = self.session.get("https://www.twitch.tv/")
            token_match = re.search(r'"authToken":"([^"]+)"', response.text)
            if token_match:
                return token_match.group(1)
            return None
        except:
            return None
            
    def gql_request(self, query: str, variables: dict = None) -> Optional[dict]:
        """Выполнение GraphQL запроса"""
        try:
            auth_token = self.get_auth_token()
            if not auth_token:
                return None
                
            headers = {
                'Authorization': f'OAuth {auth_token}',
                'Client-ID': self.config['TECHNICAL_SETTINGS']['twitch_client_id']
            }
            
            data = {
                'query': query,
                'variables': variables or {}
            }
            
            response = self.session.post(
                self.config['TWITCH_ENDPOINTS']['gql_url'],
                json=data,
                headers=headers,
                timeout=self.config['TECHNICAL_SETTINGS']['request_timeout']
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            self.log_error(f"Ошибка GQL запроса: {str(e)}")
            return None
            
    def get_drops_campaigns(self) -> List[dict]:
        """Получение активных кампаний дропов"""
        query = """
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
                        dropInstanceID
                    }
                    timeBasedDrops {
                        id
                        name
                        description
                        imageURL
                        benefitEdges {
                            benefit {
                                ... on DropBenefit {
                                    id
                                    name
                                }
                            }
                        }
                        preconditions {
                            ... on DropPrecondition {
                                id
                                requiredMinutesWatched
                            }
                        }
                        self {
                            dropInstanceID
                            currentMinutesWatched
                            requiredMinutesWatched
                            isClaimed
                        }
                    }
                }
            }
        }
        """
        
        result = self.gql_request(query)
        if result and 'data' in result:
            campaigns = result['data']['currentUser']['dropCampaigns']
            # Фильтруем только активные кампании для Wuthering Waves
            wuthering_campaigns = []
            for campaign in campaigns:
                if (campaign['status'] == 'ACTIVE' and 
                    campaign['game']['displayName'] == self.config['DROP_SETTINGS']['game_name']):
                    wuthering_campaigns.append(campaign)
            return wuthering_campaigns
        return []
        
    def get_streamers_with_drops(self) -> List[dict]:
        """Получение стримеров с активными дропами"""
        query = """
        query DirectoryPage_Game($name: String!) {
            game(name: $name) {
                streams(first: 50, options: {includeRestricted: ["SUB_ONLY_VIDEOS"]}) {
                    edges {
                        node {
                            id
                            broadcaster {
                                login
                                displayName
                            }
                            game {
                                displayName
                            }
                            viewersCount
                            tags {
                                id
                                localizedName
                            }
                        }
                    }
                }
            }
        }
        """
        
        result = self.gql_request(query, {"name": self.config['DROP_SETTINGS']['game_name']})
        if result and 'data' in result and result['data']['game']:
            streams = result['data']['game']['streams']['edges']
            streamers = []
            
            for stream in streams:
                node = stream['node']
                # Проверяем, что у стримера есть теги дропов
                has_drops = any(
                    tag['localizedName'] and 'drops' in tag['localizedName'].lower() 
                    for tag in node['tags']
                )
                
                if has_drops:
                    streamers.append({
                        'login': node['broadcaster']['login'],
                        'display_name': node['broadcaster']['displayName'],
                        'viewers': node['viewersCount'],
                        'stream_id': node['id']
                    })
                    
            return sorted(streamers, key=lambda x: x['viewers'], reverse=True)
        return []
        
    def watch_stream(self, streamer_login: str, duration_minutes: int = 1):
        """Симуляция просмотра стрима"""
        try:
            # Получаем информацию о стриме
            query = """
            query {
                user(login: "%s") {
                    stream {
                        id
                        game {
                            displayName
                        }
                        viewersCount
                    }
                }
            }
            """ % streamer_login
            
            result = self.gql_request(query)
            if not result or not result['data']['user']['stream']:
                return False
                
            stream_id = result['data']['user']['stream']['id']
            
            # Отправляем events просмотра
            for minute in range(duration_minutes):
                event_data = {
                    'event': 'minute-watched',
                    'properties': {
                        'channel_id': stream_id,
                        'broadcast_id': stream_id,
                        'player': 'site',
                        'game': self.config['DROP_SETTINGS']['game_name']
                    }
                }
                
                # Отправляем событие просмотра
                spade_url = f"https://video-weaver.twitch.tv/v1/segment/telemetry"
                response = self.session.post(spade_url, json=event_data)
                
                if response.status_code == 204:
                    self.log_info(f"📺 Просмотр {streamer_login} - минута {minute + 1}/{duration_minutes}")
                else:
                    self.log_error(f"Ошибка отправки события просмотра: {response.status_code}")
                    
                time.sleep(60)  # Ждем 1 минуту
                
            return True
            
        except Exception as e:
            self.log_error(f"Ошибка при просмотре стрима {streamer_login}: {str(e)}")
            return False
            
    def claim_drops(self) -> int:
        """Забираем доступные дропы"""
        claimed_count = 0
        
        try:
            campaigns = self.get_drops_campaigns()
            
            for campaign in campaigns:
                for drop in campaign['timeBasedDrops']:
                    drop_self = drop['self']
                    if (drop_self['currentMinutesWatched'] >= drop_self['requiredMinutesWatched'] and
                        not drop_self['isClaimed']):
                        
                        # Забираем дроп
                        claim_query = """
                        mutation ClaimDropRewards($input: ClaimDropRewardsInput!) {
                            claimDropRewards(input: $input) {
                                status
                                errors {
                                    code
                                    message
                                }
                            }
                        }
                        """
                        
                        variables = {
                            'input': {
                                'dropInstanceID': drop_self['dropInstanceID']
                            }
                        }
                        
                        result = self.gql_request(claim_query, variables)
                        if result and 'data' in result:
                            status = result['data']['claimDropRewards']['status']
                            if status == 'ELIGIBLE_FOR_ALL':
                                self.log_info(f"🎁 Получен дроп: {drop['name']}")
                                claimed_count += 1
                            else:
                                self.log_error(f"Ошибка получения дропа {drop['name']}: {status}")
                                
        except Exception as e:
            self.log_error(f"Ошибка при получении дропов: {str(e)}")
            
        return claimed_count
        
    def get_drop_progress(self) -> List[dict]:
        """Получение прогресса дропов"""
        try:
            campaigns = self.get_drops_campaigns()
            progress = []
            
            for campaign in campaigns:
                for drop in campaign['timeBasedDrops']:
                    drop_self = drop['self']
                    progress.append({
                        'name': drop['name'],
                        'current_minutes': drop_self['currentMinutesWatched'],
                        'required_minutes': drop_self['requiredMinutesWatched'],
                        'is_claimed': drop_self['isClaimed'],
                        'progress_percent': (drop_self['currentMinutesWatched'] / drop_self['requiredMinutesWatched']) * 100
                    })
                    
            return progress
            
        except Exception as e:
            self.log_error(f"Ошибка получения прогресса дропов: {str(e)}")
            return []
            
    def run_account(self, account_config: dict):
        """Запуск фарма для одного аккаунта"""
        username = account_config['username']
        password = account_config['password']
        
        if not account_config['enabled']:
            return
            
        self.log_info(f"🚀 Запуск фарма для аккаунта {username}")
        
        # Авторизация
        if not self.login_account(username, password):
            self.log_error(f"Не удалось авторизоваться для {username}")
            return
            
        # Получаем стримеров с дропами
        streamers = self.get_streamers_with_drops()
        if not streamers:
            self.log_error(f"Не найдены стримеры с дропами для {username}")
            return
            
        self.log_info(f"📋 Найдено {len(streamers)} стримеров с дропами")
        
        # Основной цикл фарма
        while self.running:
            try:
                # Выбираем стримера с наибольшим количеством зрителей
                current_streamer = streamers[0]
                
                self.log_info(f"👀 Начинаем просмотр {current_streamer['display_name']} ({current_streamer['viewers']} зрителей)")
                
                # Смотрим стрим 10 минут
                self.watch_stream(current_streamer['login'], 10)
                
                # Проверяем прогресс дропов
                progress = self.get_drop_progress()
                for drop in progress:
                    self.log_info(f"📊 {drop['name']}: {drop['current_minutes']}/{drop['required_minutes']} минут ({drop['progress_percent']:.1f}%)")
                
                # Забираем доступные дропы
                claimed = self.claim_drops()
                if claimed > 0:
                    self.log_info(f"🎉 Получено {claimed} дропов!")
                    
                # Обновляем список стримеров
                streamers = self.get_streamers_with_drops()
                
                # Пауза перед следующим циклом
                time.sleep(random.uniform(30, 60))
                
            except KeyboardInterrupt:
                self.log_info("⏹️ Остановка по запросу пользователя")
                self.running = False
                break
            except Exception as e:
                self.log_error(f"Ошибка в основном цикле: {str(e)}")
                time.sleep(60)  # Ждем минуту перед повторной попыткой
                
    def run_all_accounts(self):
        """Запуск фарма для всех аккаунтов"""
        import threading
        
        self.log_info("🌟 Запуск Twitch Drop Miner для Wuthering Waves")
        
        threads = []
        for account in self.config['ACCOUNTS']:
            if account['enabled']:
                thread = threading.Thread(target=self.run_account, args=(account,))
                thread.daemon = True
                threads.append(thread)
                thread.start()
                
                # Пауза между запуском аккаунтов
                time.sleep(self.config['TECHNICAL_SETTINGS']['sleep_between_accounts'])
                
        try:
            # Ждем завершения всех потоков
            for thread in threads:
                thread.join()
        except KeyboardInterrupt:
            self.log_info("⏹️ Остановка всех аккаунтов")
            self.running = False