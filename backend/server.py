# -*- coding: utf-8 -*-
import asyncio
import logging
import os
import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import copy
import random
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Константы для Twitch API
CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"
TWITCH_OAUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_API_URL = "https://api.twitch.tv/helix"
TWITCH_GQL_URL = "https://gql.twitch.tv/gql"

# Подключение к MongoDB
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URL)
db = client.twitch_drops_db

app = FastAPI(title="Twitch Drops Miner", version="1.0.0")

# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешить все домены
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Модели данных
class Account(BaseModel):
    username: str
    device_code: Optional[str] = None
    user_code: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None
    user_id: Optional[str] = None
    status: str = "pending"  # pending, active, error

class Game(BaseModel):
    id: str
    name: str
    box_art_url: str
    has_drops: bool = False

class Drop(BaseModel):
    id: str
    name: str
    benefit: str
    minutes_required: int
    current_minutes_watched: int = 0
    percentage_progress: float = 0.0
    is_claimed: bool = False
    is_claimable: bool = False

class Campaign(BaseModel):
    id: str
    game_id: str
    game_name: str
    name: str
    status: str
    drops: List[Drop] = []

class StreamingSession(BaseModel):
    account_id: str
    game_id: str
    game_name: str
    streamer_name: Optional[str] = None
    streamer_id: Optional[str] = None
    status: str = "searching"  # searching, watching, offline, completed
    started_at: Optional[datetime] = None
    drops_progress: List[Drop] = []

# Глобальные переменные для активных сессий
active_sessions: Dict[str, StreamingSession] = {}
background_tasks_running = set()

# Twitch API операции
class TwitchAPI:
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Client-ID": CLIENT_ID,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self.gql_headers = {
            "Client-ID": CLIENT_ID,
            "Authorization": f"OAuth {access_token}",
            "Content-Type": "application/json"
        }

    def get_user_info(self):
        """Получить информацию о пользователе"""
        try:
            response = requests.get(f"{TWITCH_API_URL}/users", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    return data["data"][0]
            return None
        except Exception as e:
            logger.error(f"Ошибка получения информации о пользователе: {e}")
            return None

    def get_games_with_drops(self):
        """Получить игры с активными дропами"""
        try:
            # GraphQL запрос для получения игр с дропами
            query = {
                "operationName": "ViewerDropsDashboard",
                "variables": {},
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": "e8b98b52bbd7ccd37bed1c179b5de4a0e83b743b942f6c5b6e5a9a7f3e1a7a1"
                    }
                }
            }
            
            response = requests.post(TWITCH_GQL_URL, json=query, headers=self.gql_headers)
            if response.status_code == 200:
                data = response.json()
                campaigns = data.get("data", {}).get("currentUser", {}).get("dropCampaigns", [])
                
                games = []
                for campaign in campaigns:
                    if campaign.get("status") == "ACTIVE":
                        game = campaign.get("game", {})
                        if game:
                            games.append({
                                "id": game.get("id"),
                                "name": game.get("displayName"),
                                "box_art_url": game.get("boxArtURL", "").replace("{width}", "285").replace("{height}", "380"),
                                "has_drops": True
                            })
                
                return games
            return []
        except Exception as e:
            logger.error(f"Ошибка получения игр с дропами: {e}")
            return []

    def get_streamers_for_game(self, game_id: str, limit: int = 10):
        """Получить стримеров для игры"""
        try:
            params = {
                "game_id": game_id,
                "first": limit,
                "type": "live"
            }
            
            response = requests.get(f"{TWITCH_API_URL}/streams", params=params, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            return []
        except Exception as e:
            logger.error(f"Ошибка получения стримеров для игры {game_id}: {e}")
            return []

    def get_drop_campaigns(self, game_id: str):
        """Получить кампании дропов для игры"""
        try:
            # Упрощенная версия - возвращаем моковые данные
            # В реальной реализации здесь будет GraphQL запрос
            return [
                {
                    "id": f"campaign_{game_id}",
                    "name": "Кампания дропов",
                    "status": "ACTIVE",
                    "drops": [
                        {
                            "id": f"drop_{game_id}_1",
                            "name": "Первый дроп",
                            "benefit": "Внутриигровые предметы",
                            "minutes_required": 60,
                            "current_minutes_watched": 0,
                            "percentage_progress": 0.0,
                            "is_claimed": False,
                            "is_claimable": False
                        }
                    ]
                }
            ]
        except Exception as e:
            logger.error(f"Ошибка получения кампаний дропов: {e}")
            return []

# Функции для работы с устройством OAuth
def get_device_code():
    """Получить код устройства для авторизации"""
    try:
        data = {
            "client_id": CLIENT_ID,
            "scopes": "user:read:email chat:read"
        }
        
        response = requests.post("https://id.twitch.tv/oauth2/device", data=data)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Ошибка получения кода устройства: {e}")
        return None

def poll_for_token(device_code: str):
    """Опрашивать токен авторизации"""
    try:
        data = {
            "client_id": CLIENT_ID,
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
        }
        
        response = requests.post(TWITCH_OAUTH_URL, data=data)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка опроса токена: {e}")
        return None

# API маршруты
@app.get("/")
async def root():
    return {"message": "Twitch Drops Miner API"}

@app.post("/api/accounts/add")
async def add_account():
    """Добавить новый аккаунт"""
    try:
        device_data = get_device_code()
        if not device_data:
            raise HTTPException(status_code=500, detail="Не удалось получить код устройства")
        
        account_id = str(uuid.uuid4())
        account = {
            "_id": account_id,
            "username": "",
            "device_code": device_data.get("device_code"),
            "user_code": device_data.get("user_code"),
            "verification_uri": device_data.get("verification_uri"),
            "expires_in": device_data.get("expires_in"),
            "access_token": None,
            "refresh_token": None,
            "expires_at": None,
            "user_id": None,
            "status": "pending",
            "created_at": datetime.now()
        }
        
        db.accounts.insert_one(account)
        
        return {
            "account_id": account_id,
            "user_code": device_data.get("user_code"),
            "verification_uri": device_data.get("verification_uri"),
            "expires_in": device_data.get("expires_in")
        }
    except Exception as e:
        logger.error(f"Ошибка добавления аккаунта: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts/{account_id}/verify")
async def verify_account(account_id: str, background_tasks: BackgroundTasks):
    """Проверить авторизацию аккаунта"""
    try:
        account = db.accounts.find_one({"_id": account_id})
        if not account:
            raise HTTPException(status_code=404, detail="Аккаунт не найден")
        
        if account.get("status") == "active":
            return {"status": "active", "username": account.get("username")}
        
        # Попытка получить токен
        token_data = poll_for_token(account["device_code"])
        
        if token_data and "access_token" in token_data:
            # Получаем информацию о пользователе
            api = TwitchAPI(token_data["access_token"])
            user_info = api.get_user_info()
            
            if user_info:
                expires_at = int(time.time()) + token_data.get("expires_in", 3600)
                
                db.accounts.update_one(
                    {"_id": account_id},
                    {"$set": {
                        "access_token": token_data["access_token"],
                        "refresh_token": token_data.get("refresh_token"),
                        "expires_at": expires_at,
                        "user_id": user_info.get("id"),
                        "username": user_info.get("login"),
                        "status": "active"
                    }}
                )
                
                return {"status": "active", "username": user_info.get("login")}
        
        if token_data and "error" in token_data:
            error = token_data["error"]
            if error == "authorization_pending":
                return {"status": "pending"}
            elif error == "expired_token":
                return {"status": "expired"}
            else:
                return {"status": "error", "message": error}
        
        return {"status": "pending"}
        
    except Exception as e:
        logger.error(f"Ошибка проверки аккаунта: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/accounts")
async def get_accounts():
    """Получить список аккаунтов"""
    try:
        accounts = list(db.accounts.find(
            {}, 
            {"_id": 1, "username": 1, "status": 1, "created_at": 1}
        ))
        
        for account in accounts:
            account["id"] = account["_id"]
            del account["_id"]
            
        return accounts
    except Exception as e:
        logger.error(f"Ошибка получения аккаунтов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str):
    """Удалить аккаунт"""
    try:
        # Остановить активную сессию, если есть
        if account_id in active_sessions:
            del active_sessions[account_id]
        
        result = db.accounts.delete_one({"_id": account_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Аккаунт не найден")
        
        return {"message": "Аккаунт удален"}
    except Exception as e:
        logger.error(f"Ошибка удаления аккаунта: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/games")
async def get_games_with_drops():
    """Получить игры с активными дропами"""
    try:
        # Получаем активные аккаунты
        active_accounts = list(db.accounts.find({"status": "active"}, {"access_token": 1}))
        
        if not active_accounts:
            return {"games": [], "message": "Нет активных аккаунтов"}
        
        # Используем первый активный аккаунт для получения игр
        api = TwitchAPI(active_accounts[0]["access_token"])
        games = api.get_games_with_drops()
        
        return {"games": games}
    except Exception as e:
        logger.error(f"Ошибка получения игр: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/start-farming")
async def start_farming(request: dict, background_tasks: BackgroundTasks):
    """Начать фарм дропов"""
    try:
        account_id = request.get("account_id")
        game_id = request.get("game_id")
        game_name = request.get("game_name")
        
        if not all([account_id, game_id, game_name]):
            raise HTTPException(status_code=400, detail="Недостаточно данных")
        
        # Проверяем аккаунт
        account = db.accounts.find_one({"_id": account_id, "status": "active"})
        if not account:
            raise HTTPException(status_code=404, detail="Активный аккаунт не найден")
        
        # Останавливаем предыдущую сессию, если есть
        if account_id in active_sessions:
            del active_sessions[account_id]
        
        # Создаем новую сессию
        session = StreamingSession(
            account_id=account_id,
            game_id=game_id,
            game_name=game_name,
            status="searching",
            started_at=datetime.now()
        )
        
        active_sessions[account_id] = session
        
        # Запускаем фоновую задачу
        background_tasks.add_task(run_farming_session, account_id, account["access_token"])
        
        return {"message": "Фарм дропов запущен", "session_id": account_id}
    except Exception as e:
        logger.error(f"Ошибка запуска фарма: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/stop-farming")
async def stop_farming(request: dict):
    """Остановить фарм дропов"""
    try:
        account_id = request.get("account_id")
        
        if account_id in active_sessions:
            del active_sessions[account_id]
            return {"message": "Фарм дропов остановлен"}
        
        return {"message": "Активная сессия не найдена"}
    except Exception as e:
        logger.error(f"Ошибка остановки фарма: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/farming-status")
async def get_farming_status():
    """Получить статус фарма"""
    try:
        sessions = []
        for account_id, session in active_sessions.items():
            account = db.accounts.find_one({"_id": account_id}, {"username": 1})
            sessions.append({
                "account_id": account_id,
                "username": account.get("username") if account else "Unknown",
                "game_name": session.game_name,
                "streamer_name": session.streamer_name,
                "status": session.status,
                "started_at": session.started_at,
                "drops_progress": session.drops_progress
            })
        
        return {"sessions": sessions}
    except Exception as e:
        logger.error(f"Ошибка получения статуса фарма: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs():
    """Получить логи системы"""
    try:
        # Возвращаем последние 100 записей логов
        logs = list(db.logs.find().sort("timestamp", -1).limit(100))
        
        for log in logs:
            log["id"] = str(log["_id"])
            del log["_id"]
            
        return {"logs": logs[::-1]}  # Возвращаем в хронологическом порядке
    except Exception as e:
        logger.error(f"Ошибка получения логов: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def add_log(level: str, message: str, account_id: str = None):
    """Добавить запись в лог"""
    try:
        log_entry = {
            "timestamp": datetime.now(),
            "level": level,
            "message": message,
            "account_id": account_id
        }
        db.logs.insert_one(log_entry)
    except Exception as e:
        logger.error(f"Ошибка добавления лога: {e}")

async def run_farming_session(account_id: str, access_token: str):
    """Запустить сессию фарма дропов"""
    try:
        if account_id in background_tasks_running:
            return
        
        background_tasks_running.add(account_id)
        api = TwitchAPI(access_token)
        session = active_sessions.get(account_id)
        
        if not session:
            background_tasks_running.discard(account_id)
            return
        
        add_log("INFO", f"Начинаем фарм дропов для игры {session.game_name}", account_id)
        
        while account_id in active_sessions:
            try:
                current_session = active_sessions[account_id]
                
                # Ищем активных стримеров для игры
                streamers = api.get_streamers_for_game(current_session.game_id, 20)
                
                if not streamers:
                    add_log("WARNING", f"Нет активных стримеров для игры {current_session.game_name}", account_id)
                    current_session.status = "no_streamers"
                    await asyncio.sleep(60)  # Ждем минуту и пробуем снова
                    continue
                
                # Выбираем случайного стримера
                streamer = random.choice(streamers)
                current_session.streamer_name = streamer.get("user_name")
                current_session.streamer_id = streamer.get("user_id")
                current_session.status = "watching"
                
                add_log("INFO", f"Начинаем смотреть стримера {current_session.streamer_name}", account_id)
                
                # Симулируем просмотр (в реальности здесь будет отправка minute-watched событий)
                watch_time = 0
                while account_id in active_sessions and watch_time < 3600:  # Максимум час на стримера
                    # Проверяем, что стример все еще онлайн
                    current_streamers = api.get_streamers_for_game(current_session.game_id, 20)
                    streamer_online = any(s.get("user_id") == current_session.streamer_id for s in current_streamers)
                    
                    if not streamer_online:
                        add_log("INFO", f"Стример {current_session.streamer_name} ушел в офлайн", account_id)
                        break
                    
                    # Симулируем просмотр минуты
                    await asyncio.sleep(60)  # В реальности будет отправка запроса к Twitch
                    watch_time += 1
                    
                    # Обновляем прогресс дропов (упрощенная версия)
                    if current_session.drops_progress:
                        for drop in current_session.drops_progress:
                            if drop.current_minutes_watched < drop.minutes_required:
                                drop.current_minutes_watched += 1
                                drop.percentage_progress = (drop.current_minutes_watched / drop.minutes_required) * 100
                                
                                if drop.percentage_progress >= 100:
                                    drop.is_claimable = True
                                    add_log("SUCCESS", f"Дроп {drop.name} готов к получению!", account_id)
                
                # Переходим к следующему стримеру
                add_log("INFO", f"Переключаемся на другого стримера", account_id)
                
            except Exception as e:
                logger.error(f"Ошибка в сессии фарма: {e}")
                add_log("ERROR", f"Ошибка в сессии фарма: {str(e)}", account_id)
                await asyncio.sleep(30)
        
    except Exception as e:
        logger.error(f"Критическая ошибка в фарме: {e}")
        add_log("ERROR", f"Критическая ошибка в фарме: {str(e)}", account_id)
    finally:
        background_tasks_running.discard(account_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)