from fastapi import FastAPI, APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import requests
import asyncio
import json
import webbrowser
from urllib.parse import urlencode
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Twitch Drops Miner", description="Упрощенная версия для получения дропов")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Twitch API configuration
TWITCH_CLIENT_ID = "ue6666qo983tsx6so1t0vnawi233wa"
TWITCH_API_BASE = "https://api.twitch.tv/helix"
TWITCH_OAUTH_BASE = "https://id.twitch.tv/oauth2"
TWITCH_GQL_BASE = "https://gql.twitch.tv/gql"

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []

# Global monitoring state
monitoring_tasks: Dict[str, asyncio.Task] = {}
monitoring_active = False

# Define Models
class TwitchAccount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    authenticated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # active, error, expired
    last_check: Optional[datetime] = None
    drops_claimed: int = 0

class TwitchAccountCreate(BaseModel):
    username: str

class AuthDeviceCode(BaseModel):
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int

class DropsCampaign(BaseModel):
    id: str
    name: str
    game_name: str
    status: str
    start_at: str
    end_at: str
    drops: List[Dict[str, Any]]
    account_id: str

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    check_interval: int = 60
    auto_claim_drops: bool = True
    watch_time_minutes: int = 30
    language: str = "ru"
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SettingsUpdate(BaseModel):
    check_interval: Optional[int] = None
    auto_claim_drops: Optional[bool] = None
    watch_time_minutes: Optional[int] = None

class MonitoringStatus(BaseModel):
    active: bool
    accounts_count: int
    last_check: Optional[datetime] = None
    next_check: Optional[datetime] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                pass

    async def broadcast_status(self, status: dict):
        await self.send_message({"type": "status_update", "data": status})

manager = ConnectionManager()

# Twitch API helper functions
async def get_device_code() -> Optional[Dict]:
    """Получить device code для авторизации"""
    device_code_url = f"{TWITCH_OAUTH_BASE}/device"
    device_data = {
        "client_id": TWITCH_CLIENT_ID,
        "scope": "user:read:email user:read:follows chat:read"
    }
    
    try:
        response = requests.post(device_code_url, data=device_data)
        
        logger.info(f"Device code request status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Device code created successfully: {result.get('user_code', 'Unknown')}")
            return result
        else:
            logger.error(f"Failed to get device code: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Ошибка получения device code: {str(e)}")
        return None

async def check_device_authorization(device_code: str) -> Optional[Dict]:
    """Проверить статус авторизации device"""
    token_url = f"{TWITCH_OAUTH_BASE}/token"
    token_data = {
        "client_id": TWITCH_CLIENT_ID,
        "device_code": device_code,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
    }
    
    try:
        response = requests.post(token_url, data=token_data)
        result = response.json()
        
        # Логируем ответ для отладки
        logger.info(f"Twitch API response status: {response.status_code}")
        logger.info(f"Twitch API response body: {result}")
        
        # Если статус 200 - успешная авторизация
        if response.status_code == 200:
            return result
        
        # Если статус не 200, обрабатываем ошибки
        # Twitch может возвращать разные форматы ошибок
        if "error" in result:
            # Стандартный формат OAuth2: {"error": "authorization_pending"}
            return result
        elif "message" in result:
            # Альтернативный формат: {"status": 400, "message": "authorization_pending"}
            message = result["message"]
            if message == "authorization_pending":
                return {"error": "authorization_pending"}
            elif message == "slow_down":
                return {"error": "slow_down"}
            elif message == "expired_token":
                return {"error": "expired_token"}
            elif message == "access_denied":
                return {"error": "access_denied"}
            else:
                return {"error": "unknown_error", "error_description": message}
        else:
            logger.error(f"Неожиданный ответ от Twitch API: {result}")
            return {"error": "server_error", "error_description": "Неожиданный ответ от сервера"}
        
    except Exception as e:
        logger.error(f"Ошибка проверки авторизации: {str(e)}")
        return {"error": "server_error", "error_description": str(e)}

async def get_user_info(access_token: str) -> Optional[Dict]:
    """Получить информацию о пользователе"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    
    try:
        response = requests.get(f"{TWITCH_API_BASE}/users", headers=headers)
        if response.status_code == 200:
            users = response.json().get("data", [])
            return users[0] if users else None
        return None
    except Exception as e:
        logger.error(f"Ошибка получения информации о пользователе: {str(e)}")
        return None

async def refresh_access_token(refresh_token: str) -> Optional[Dict]:
    """Обновить access token"""
    refresh_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": TWITCH_CLIENT_ID
    }
    
    try:
        response = requests.post(f"{TWITCH_OAUTH_BASE}/token", data=refresh_data)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Ошибка обновления токена: {str(e)}")
        return None

async def get_drops_campaigns(access_token: str) -> List[Dict]:
    """Получить активные кампании дропов"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": TWITCH_CLIENT_ID
    }
    
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
        response = requests.post(TWITCH_GQL_BASE, json=gql_query, headers=headers)
        if response.status_code == 200:
            data = response.json()
            campaigns = data.get("data", {}).get("currentUser", {}).get("dropCampaigns", [])
            return [c for c in campaigns if c.get("status") == "ACTIVE"]
        return []
    except Exception as e:
        logger.error(f"Ошибка получения кампаний дропов: {str(e)}")
        return []

async def claim_drop(access_token: str, drop_instance_id: str) -> bool:
    """Получить дроп"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Client-Id": TWITCH_CLIENT_ID
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
        response = requests.post(TWITCH_GQL_BASE, json=gql_query, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data.get("data", {}).get("claimDropRewards", {}).get("status")
            return status == "ELIGIBLE_FOR_ALL"
        return False
    except Exception as e:
        logger.error(f"Ошибка получения дропа: {str(e)}")
        return False

# Background task for monitoring drops
async def monitor_drops_for_account(account_id: str):
    """Мониторинг дропов для одного аккаунта"""
    while monitoring_active:
        try:
            # Получить данные аккаунта
            account_data = await db.accounts.find_one({"id": account_id})
            if not account_data:
                break
            
            access_token = account_data.get("access_token")
            username = account_data.get("username")
            
            # Обновить токен если нужно
            if account_data.get("refresh_token"):
                refresh_result = await refresh_access_token(account_data["refresh_token"])
                if refresh_result:
                    access_token = refresh_result["access_token"]
                    await db.accounts.update_one(
                        {"id": account_id},
                        {"$set": {"access_token": access_token}}
                    )
            
            # Получить кампании дропов
            campaigns = await get_drops_campaigns(access_token)
            
            drops_claimed = 0
            for campaign in campaigns:
                campaign_self = campaign.get("self", {})
                if not campaign_self.get("isAccountConnected", False):
                    continue
                
                drops = campaign_self.get("drops", [])
                
                for drop in drops:
                    drop_self = drop.get("self", {})
                    current_minutes = drop_self.get("currentMinutesWatched", 0)
                    required_minutes = drop.get("requiredMinutesWatched", 0)
                    is_claimed = drop_self.get("isClaimed", False)
                    drop_instance_id = drop_self.get("dropInstanceID")
                    
                    if not is_claimed and current_minutes >= required_minutes and drop_instance_id:
                        if await claim_drop(access_token, drop_instance_id):
                            drops_claimed += 1
                            await manager.send_message({
                                "type": "drop_claimed",
                                "data": {
                                    "account": username,
                                    "drop_name": drop.get("name", "Неизвестный дроп"),
                                    "campaign": campaign.get("name", "Неизвестная кампания")
                                }
                            })
            
            # Обновить статистику аккаунта
            await db.accounts.update_one(
                {"id": account_id},
                {
                    "$set": {
                        "last_check": datetime.utcnow(),
                        "status": "active"
                    },
                    "$inc": {"drops_claimed": drops_claimed}
                }
            )
            
            # Получить настройки для интервала
            settings = await db.settings.find_one({}) or {"check_interval": 60}
            check_interval = settings.get("check_interval", 60)
            
            await asyncio.sleep(check_interval)
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга аккаунта {account_id}: {str(e)}")
            await asyncio.sleep(30)

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Twitch Drops Miner API", "version": "1.0"}

# Settings endpoints
@api_router.get("/settings", response_model=Settings)
async def get_settings():
    settings = await db.settings.find_one({})
    if not settings:
        # Создать настройки по умолчанию
        default_settings = Settings()
        await db.settings.insert_one(default_settings.dict())
        return default_settings
    return Settings(**settings)

@api_router.put("/settings", response_model=Settings)
async def update_settings(settings_update: SettingsUpdate):
    current_settings = await db.settings.find_one({})
    if not current_settings:
        current_settings = Settings().dict()
    
    # Обновить только переданные поля
    update_data = settings_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.settings.update_one(
        {"id": current_settings.get("id")},
        {"$set": update_data},
        upsert=True
    )
    
    updated_settings = await db.settings.find_one({})
    return Settings(**updated_settings)

# Account management endpoints
@api_router.get("/accounts", response_model=List[TwitchAccount])
async def get_accounts():
    accounts = await db.accounts.find().to_list(1000)
    return [TwitchAccount(**account) for account in accounts]

@api_router.post("/accounts/device-code", response_model=AuthDeviceCode)
async def get_auth_device_code():
    device_info = await get_device_code()
    if not device_info:
        raise HTTPException(status_code=500, detail="Не удалось получить код авторизации")
    
    return AuthDeviceCode(**device_info)

@api_router.post("/accounts/authorize")
async def authorize_account(device_code: str):
    """Проверить авторизацию и добавить аккаунт"""
    try:
        logger.info(f"Проверка авторизации для device_code: {device_code[:10]}...")
        
        token_result = await check_device_authorization(device_code)
        
        if not token_result:
            logger.error("Не удалось получить результат проверки авторизации")
            raise HTTPException(status_code=500, detail="Ошибка сервера при проверке авторизации")
        
        logger.info(f"Результат проверки авторизации: {token_result}")
        
        if token_result.get("error"):
            error_code = token_result["error"]
            error_description = token_result.get("error_description", "")
            
            logger.info(f"Twitch API error: {error_code} - {error_description}")
            
            if error_code == "authorization_pending":
                raise HTTPException(status_code=202, detail="Ожидание авторизации")
            elif error_code == "slow_down":
                raise HTTPException(status_code=202, detail="Слишком частые запросы, ожидание...")
            elif error_code == "expired_token":
                raise HTTPException(status_code=400, detail="Время авторизации истекло. Попробуйте снова.")
            elif error_code == "access_denied":
                raise HTTPException(status_code=400, detail="Авторизация отклонена пользователем")
            else:
                raise HTTPException(status_code=400, detail=f"Ошибка авторизации: {error_code}")
        
        access_token = token_result.get("access_token")
        refresh_token = token_result.get("refresh_token")
        
        if not access_token:
            logger.error(f"Токен доступа не найден в ответе: {token_result}")
            raise HTTPException(status_code=400, detail="Не удалось получить токен доступа")
        
        logger.info("Получение информации о пользователе...")
        
        # Получить информацию о пользователе
        user_info = await get_user_info(access_token)
        if not user_info:
            logger.error("Не удалось получить информацию о пользователе")
            raise HTTPException(status_code=400, detail="Не удалось получить информацию о пользователе")
        
        logger.info(f"Пользователь: {user_info.get('display_name', 'Unknown')}")
        
        # Проверить, что аккаунт не существует
        existing_account = await db.accounts.find_one({"user_id": user_info["id"]})
        if existing_account:
            logger.warning(f"Аккаунт {user_info['display_name']} уже существует")
            raise HTTPException(status_code=400, detail="Аккаунт уже существует")
        
        # Создать новый аккаунт
        account = TwitchAccount(
            username=user_info["display_name"],
            user_id=user_info["id"],
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        await db.accounts.insert_one(account.dict())
        
        logger.info(f"Аккаунт {user_info['display_name']} успешно добавлен")
        return {"message": "Аккаунт успешно добавлен", "account": account}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка при авторизации: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@api_router.delete("/accounts/{account_id}")
async def delete_account(account_id: str):
    result = await db.accounts.delete_one({"id": account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    return {"message": "Аккаунт удален"}

@api_router.post("/accounts/refresh-tokens")
async def refresh_all_tokens():
    """Обновить токены для всех аккаунтов"""
    accounts = await db.accounts.find().to_list(1000)
    updated_count = 0
    
    for account in accounts:
        if account.get("refresh_token"):
            refresh_result = await refresh_access_token(account["refresh_token"])
            if refresh_result:
                await db.accounts.update_one(
                    {"id": account["id"]},
                    {"$set": {
                        "access_token": refresh_result["access_token"],
                        "refresh_token": refresh_result.get("refresh_token", account["refresh_token"])
                    }}
                )
                updated_count += 1
    
    return {"message": f"Обновлено токенов: {updated_count}"}

# Monitoring endpoints
@api_router.get("/monitoring/status", response_model=MonitoringStatus)
async def get_monitoring_status():
    accounts_count = await db.accounts.count_documents({})
    
    return MonitoringStatus(
        active=monitoring_active,
        accounts_count=accounts_count,
        last_check=datetime.utcnow() if monitoring_active else None
    )

@api_router.post("/monitoring/start")
async def start_monitoring(background_tasks: BackgroundTasks):
    global monitoring_active, monitoring_tasks
    
    if monitoring_active:
        return {"message": "Мониторинг уже запущен"}
    
    accounts = await db.accounts.find().to_list(1000)
    if not accounts:
        raise HTTPException(status_code=400, detail="Нет аккаунтов для мониторинга")
    
    monitoring_active = True
    monitoring_tasks = {}
    
    # Запустить мониторинг для каждого аккаунта
    for account in accounts:
        task = asyncio.create_task(monitor_drops_for_account(account["id"]))
        monitoring_tasks[account["id"]] = task
    
    await manager.broadcast_status({"monitoring_active": True})
    
    return {"message": "Мониторинг запущен", "accounts_count": len(accounts)}

@api_router.post("/monitoring/stop")
async def stop_monitoring():
    global monitoring_active, monitoring_tasks
    
    if not monitoring_active:
        return {"message": "Мониторинг не запущен"}
    
    monitoring_active = False
    
    # Остановить все задачи
    for task in monitoring_tasks.values():
        task.cancel()
    
    monitoring_tasks = {}
    
    await manager.broadcast_status({"monitoring_active": False})
    
    return {"message": "Мониторинг остановлен"}

# Drops endpoints
@api_router.get("/drops/{account_id}")
async def get_account_drops(account_id: str):
    """Получить дропы для конкретного аккаунта"""
    account = await db.accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    campaigns = await get_drops_campaigns(account["access_token"])
    
    return {
        "account": account["username"],
        "campaigns": campaigns,
        "campaigns_count": len(campaigns)
    }

# Statistics endpoints
@api_router.get("/statistics")
async def get_statistics():
    """Получить общую статистику"""
    total_accounts = await db.accounts.count_documents({})
    active_accounts = await db.accounts.count_documents({"status": "active"})
    
    # Безопасно получаем общее количество дропов
    total_drops_claimed = 0
    if total_accounts > 0:
        total_drops_result = await db.accounts.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$drops_claimed"}}}
        ]).to_list(1)
        total_drops_claimed = total_drops_result[0]["total"] if total_drops_result else 0
    
    settings = await db.settings.find_one({}) or {}
    
    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "total_drops_claimed": total_drops_claimed,
        "monitoring_active": monitoring_active,
        "settings": settings
    }

# WebSocket endpoint
@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Эхо для поддержания соединения
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("🎮 Twitch Drops Miner API запущен")

@app.on_event("shutdown")
async def shutdown_db_client():
    global monitoring_active
    monitoring_active = False
    client.close()
    logger.info("🔚 Twitch Drops Miner API остановлен")
