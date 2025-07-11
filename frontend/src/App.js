import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Компонент для добавления аккаунта
const AddAccountModal = ({ isOpen, onClose, onAccountAdded }) => {
  const [step, setStep] = useState(1); // 1: начало, 2: ожидание авторизации
  const [deviceCode, setDeviceCode] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [authInterval, setAuthInterval] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setStep(1);
      setError('');
      setDeviceCode(null);
      if (authInterval) {
        clearInterval(authInterval);
        setAuthInterval(null);
      }
    }
  }, [isOpen]);

  const startAuth = async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const response = await axios.post(`${API}/accounts/device-code`);
      const deviceData = response.data;
      
      setDeviceCode(deviceData);
      setStep(2);
      
      // Открыть страницу авторизации
      window.open(deviceData.verification_uri, '_blank');
      
      // Начать проверку авторизации с увеличенным интервалом
      let attempts = 0;
      const maxAttempts = Math.floor(deviceData.expires_in / deviceData.interval);
      
      const interval = setInterval(async () => {
        attempts++;
        
        try {
          const authResponse = await axios.post(`${API}/accounts/authorize?device_code=${deviceData.device_code}`);
          
          if (authResponse.status === 200) {
            clearInterval(interval);
            setAuthInterval(null);
            
            // Показать сообщение об успехе
            alert(`Аккаунт ${authResponse.data.account.username} успешно добавлен!`);
            
            // Обновить данные
            await onAccountAdded();
            
            // Закрыть модальное окно
            onClose();
          }
        } catch (err) {
          if (err.response?.status === 202) {
            // Продолжаем ожидать
            if (attempts >= maxAttempts) {
              clearInterval(interval);
              setAuthInterval(null);
              setError('Время авторизации истекло. Попробуйте снова.');
              setStep(1);
            }
            return;
          } else {
            clearInterval(interval);
            setAuthInterval(null);
            const errorMessage = err.response?.data?.detail || err.message;
            setError('Ошибка авторизации: ' + errorMessage);
            setStep(1);
          }
        }
      }, Math.max(deviceData.interval * 1000, 3000)); // Минимум 3 секунды между запросами
      
      setAuthInterval(interval);
      
    } catch (err) {
      setError('Ошибка получения кода авторизации: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (authInterval) {
      clearInterval(authInterval);
      setAuthInterval(null);
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">Добавить аккаунт</h2>
          <button
            onClick={handleClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>
        
        {step === 1 && (
          <div>
            <p className="text-gray-600 mb-4">
              Для добавления аккаунта необходимо авторизоваться через Twitch.
            </p>
            
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                {error}
              </div>
            )}
            
            <div className="flex gap-2">
              <button
                onClick={startAuth}
                disabled={isLoading}
                className="flex-1 bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 disabled:opacity-50"
              >
                {isLoading ? 'Загрузка...' : 'Начать авторизацию'}
              </button>
              <button
                onClick={handleClose}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
              >
                Отмена
              </button>
            </div>
          </div>
        )}
        
        {step === 2 && deviceCode && (
          <div>
            <p className="text-gray-600 mb-4">
              Перейдите по ссылке и введите код авторизации:
            </p>
            
            <div className="bg-gray-100 p-4 rounded mb-4">
              <p className="font-semibold">Ссылка: 
                <a 
                  href={deviceCode.verification_uri} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-purple-600 hover:text-purple-800 ml-1"
                >
                  {deviceCode.verification_uri}
                </a>
              </p>
              <p className="font-semibold text-lg mt-2">
                Код: <span className="text-purple-600">{deviceCode.user_code}</span>
              </p>
              <p className="text-sm text-gray-500 mt-2">
                ⏰ Время действия кода: {Math.floor(deviceCode.expires_in / 60)} минут
              </p>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded p-4 mb-4">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                <div>
                  <p className="text-blue-800 font-medium">Ожидание авторизации...</p>
                  <p className="text-blue-600 text-sm">
                    Авторизуйтесь на сайте Twitch, после чего аккаунт будет добавлен автоматически
                  </p>
                </div>
              </div>
            </div>
            
            <div className="text-sm text-gray-600 mb-4">
              <p>📝 <strong>Инструкция:</strong></p>
              <ol className="list-decimal list-inside mt-2 space-y-1">
                <li>Нажмите на ссылку выше (откроется в новой вкладке)</li>
                <li>Введите код: <span className="font-mono font-bold text-purple-600">{deviceCode.user_code}</span></li>
                <li>Нажмите "Продолжить" на сайте Twitch</li>
                <li>Авторизуйтесь в своем аккаунте Twitch</li>
                <li>Разрешите доступ к приложению</li>
              </ol>
            </div>
            
            <button
              onClick={handleClose}
              className="w-full bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
            >
              Отмена
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// Компонент аккаунта
const AccountCard = ({ account, onDelete, loadData, addNotification }) => {
  const [isDeleting, setIsDeleting] = useState(false);
  
  const handleDelete = async () => {
    if (!window.confirm(`Удалить аккаунт ${account.username}?`)) return;
    
    setIsDeleting(true);
    try {
      await axios.delete(`${API}/accounts/${account.id}`);
      
      // Обновить локальное состояние через callback
      onDelete(account.id);
      
      // Обновить данные с сервера
      await loadData();
      
      addNotification('✅ Аккаунт удален!');
    } catch (err) {
      console.error('Ошибка удаления аккаунта:', err);
      addNotification('❌ Ошибка удаления аккаунта: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-800">{account.username}</h3>
          <p className="text-sm text-gray-500">ID: {account.user_id}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-1 rounded text-xs ${
            account.status === 'active' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}>
            {account.status === 'active' ? 'Активный' : 'Ошибка'}
          </span>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="text-red-600 hover:text-red-800 disabled:opacity-50"
          >
            {isDeleting ? '...' : '🗑️'}
          </button>
        </div>
      </div>
      
      <div className="text-sm text-gray-600">
        <p>Дропов получено: <span className="font-semibold">{account.drops_claimed || 0}</span></p>
        <p>Авторизован: {formatDate(account.authenticated_at)}</p>
        {account.last_check && (
          <p>Последняя проверка: {formatDate(account.last_check)}</p>
        )}
      </div>
    </div>
  );
};

// Компонент настроек
const SettingsModal = ({ isOpen, onClose, settings, onSettingsUpdate }) => {
  const [formData, setFormData] = useState(settings);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setFormData(settings);
  }, [settings]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      await axios.put(`${API}/settings`, formData);
      onSettingsUpdate();
      onClose();
    } catch (err) {
      alert('Ошибка сохранения настроек: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">Настройки</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Интервал проверки (секунды)
            </label>
            <input
              type="number"
              min="30"
              value={formData.check_interval || 60}
              onChange={(e) => setFormData({...formData, check_interval: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Время просмотра (минуты)
            </label>
            <input
              type="number"
              min="1"
              value={formData.watch_time_minutes || 30}
              onChange={(e) => setFormData({...formData, watch_time_minutes: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>
          
          <div className="mb-6">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.auto_claim_drops || false}
                onChange={(e) => setFormData({...formData, auto_claim_drops: e.target.checked})}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Автоматически получать дропы</span>
            </label>
          </div>
          
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 disabled:opacity-50"
            >
              {isLoading ? 'Сохранение...' : 'Сохранить'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
            >
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Компонент отображения прогресса дропов
const DropsProgressPanel = ({ isOpen, onClose }) => {
  const [dropsProgress, setDropsProgress] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadDropsProgress();
      // Обновлять прогресс каждые 30 секунд
      const interval = setInterval(loadDropsProgress, 30000);
      return () => clearInterval(interval);
    }
  }, [isOpen]);

  const loadDropsProgress = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/drops/progress`);
      setDropsProgress(response.data);
    } catch (err) {
      console.error('Ошибка загрузки прогресса дропов:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (minutes) => {
    if (minutes < 60) return `${minutes} мин`;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}ч ${mins}мин`;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">Прогресс фарма дропов</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-8">
            <p>Загрузка...</p>
          </div>
        ) : (
          <div className="overflow-y-auto max-h-[70vh]">
            {dropsProgress.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">Нет активных дропов для мониторинга</p>
              </div>
            ) : (
              <div className="space-y-4">
                {dropsProgress.map((drop, index) => (
                  <div key={index} className="border rounded-lg p-4 bg-gray-50">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h3 className="font-semibold text-lg text-gray-900">{drop.drop_name}</h3>
                        <p className="text-sm text-gray-600">{drop.campaign_name}</p>
                        <p className="text-sm text-blue-600 font-medium">{drop.game_name}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">
                          {drop.streamer_name ? `Стример: ${drop.streamer_name}` : 'Нет стримера'}
                        </p>
                        <p className="text-xs text-gray-400">
                          {formatTime(drop.current_minutes)} / {formatTime(drop.required_minutes)}
                        </p>
                      </div>
                    </div>
                    
                    <div className="mb-2">
                      <div className="flex justify-between items-center text-sm mb-1">
                        <span>Прогресс:</span>
                        <span className="font-medium">
                          {Math.round((drop.current_minutes / drop.required_minutes) * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            drop.is_claimed ? 'bg-green-500' : 'bg-blue-500'
                          }`}
                          style={{ 
                            width: `${Math.min(100, (drop.current_minutes / drop.required_minutes) * 100)}%` 
                          }}
                        ></div>
                      </div>
                    </div>
                    
                    <div className="flex justify-between items-center text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        drop.is_claimed 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {drop.is_claimed ? 'Получен' : 'В процессе'}
                      </span>
                      <span className="text-gray-400">
                        Обновлен: {new Date(drop.last_updated).toLocaleString('ru-RU')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Компонент выбора игр
const GameSelectionModal = ({ isOpen, onClose, settings, onSettingsUpdate }) => {
  const [games, setGames] = useState([]);
  const [selectedGames, setSelectedGames] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadGames();
      const monitoredGames = settings?.monitored_games || [];
      setSelectedGames([...monitoredGames]); // Создать копию массива
    }
  }, [isOpen, settings]);

  const loadGames = async () => {
    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/games`);
      setGames(response.data);
    } catch (err) {
      console.error('Ошибка загрузки игр:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const searchGames = async (query) => {
    if (!query || query.length < 2) {
      loadGames();
      return;
    }
    
    setIsSearching(true);
    try {
      const response = await axios.get(`${API}/games/search?q=${encodeURIComponent(query)}`);
      setGames(response.data);
    } catch (err) {
      console.error('Ошибка поиска игр:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    
    // Debounce search
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(() => {
      searchGames(query);
    }, 500);
  };

  const toggleGame = (gameId) => {
    setSelectedGames(prev => 
      prev.includes(gameId) 
        ? prev.filter(id => id !== gameId)
        : [...prev, gameId]
    );
  };

  const handleSave = async () => {
    try {
      await axios.put(`${API}/settings`, { monitored_games: selectedGames });
      onSettingsUpdate();
      onClose();
    } catch (err) {
      alert('Ошибка сохранения настроек: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">Выбор игр для мониторинга</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="mb-4">
          <input
            type="text"
            placeholder="Поиск игр..."
            value={searchQuery}
            onChange={handleSearchChange}
            className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          {isSearching && (
            <p className="text-sm text-gray-500 mt-1">Поиск...</p>
          )}
        </div>

        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Выбрано игр: <span className="font-semibold">{selectedGames.length}</span>
            {selectedGames.length === 0 && <span className="text-orange-600"> (будут мониториться все доступные игры)</span>}
          </p>
        </div>

        <div className="overflow-y-auto max-h-96 mb-4">
          {isLoading ? (
            <div className="text-center py-8">
              <p>Загрузка игр...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {games.map(game => (
                <div 
                  key={game.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    selectedGames.includes(game.id) 
                      ? 'border-purple-500 bg-purple-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => toggleGame(game.id)}
                >
                  <div className="flex items-center gap-3">
                    <img 
                      src={game.box_art_url} 
                      alt={game.name}
                      className="w-16 h-20 object-cover rounded"
                      onError={(e) => {
                        e.target.src = 'https://via.placeholder.com/144x192?text=No+Image';
                      }}
                    />
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{game.name}</h3>
                      {game.has_drops && (
                        <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                          Дропы доступны
                        </span>
                      )}
                    </div>
                    <div className="flex-shrink-0">
                      {selectedGames.includes(game.id) ? (
                        <span className="text-purple-600 text-xl">✓</span>
                      ) : (
                        <span className="text-gray-400 text-xl">○</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="flex-1 bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700"
          >
            Сохранить
          </button>
          <button
            onClick={onClose}
            className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
          >
            Отмена
          </button>
        </div>
      </div>
    </div>
  );
};

// Главный компонент
const App = () => {
  const [accounts, setAccounts] = useState([]);
  const [settings, setSettings] = useState({});
  const [statistics, setStatistics] = useState({});
  const [monitoring, setMonitoring] = useState({ active: false });
  const [isAddAccountModalOpen, setIsAddAccountModalOpen] = useState(false);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isGameSelectionModalOpen, setIsGameSelectionModalOpen] = useState(false);
  const [isDropsProgressModalOpen, setIsDropsProgressModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [websocket, setWebsocket] = useState(null);
  const [notifications, setNotifications] = useState([]);

  // Загрузка данных
  useEffect(() => {
    loadData();
    connectWebSocket();
  }, []);

  const loadData = async () => {
    try {
      console.log('Loading data...');
      
      const [accountsRes, settingsRes, statisticsRes, monitoringRes] = await Promise.all([
        axios.get(`${API}/accounts`),
        axios.get(`${API}/settings`),
        axios.get(`${API}/statistics`),
        axios.get(`${API}/monitoring/status`)
      ]);
      
      console.log('Accounts loaded:', accountsRes.data);
      console.log('Settings loaded:', settingsRes.data);
      console.log('Statistics loaded:', statisticsRes.data);
      console.log('Monitoring loaded:', monitoringRes.data);
      
      setAccounts(accountsRes.data);
      setSettings(settingsRes.data);
      setStatistics(statisticsRes.data);
      setMonitoring(monitoringRes.data);
      
      console.log('Data loaded successfully');
    } catch (err) {
      console.error('Ошибка загрузки данных:', err);
      // Показать уведомление об ошибке
      addNotification('❌ Ошибка загрузки данных: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsLoading(false);
    }
  };

  const connectWebSocket = () => {
    const wsUrl = `${BACKEND_URL.replace('http', 'ws')}/api/ws`;
    const ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'drop_claimed') {
        addNotification(`🎁 Дроп получен: ${data.data.drop_name} (${data.data.account})`);
        loadData(); // Обновить данные
      } else if (data.type === 'status_update') {
        setMonitoring(prev => ({...prev, ...data.data}));
      }
    };
    
    ws.onclose = () => {
      // Переподключение через 5 секунд
      setTimeout(connectWebSocket, 5000);
    };
    
    setWebsocket(ws);
  };

  const addNotification = (message) => {
    const notification = {
      id: Date.now(),
      message,
      timestamp: new Date()
    };
    
    setNotifications(prev => [notification, ...prev.slice(0, 4)]); // Показывать только последние 5
    
    // Убрать через 5 секунд
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const handleStartMonitoring = async () => {
    try {
      await axios.post(`${API}/monitoring/start`);
      setMonitoring(prev => ({...prev, active: true}));
      addNotification('🚀 Мониторинг дропов запущен');
    } catch (err) {
      alert('Ошибка запуска мониторинга: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleStopMonitoring = async () => {
    try {
      await axios.post(`${API}/monitoring/stop`);
      setMonitoring(prev => ({...prev, active: false}));
      addNotification('🛑 Мониторинг дропов остановлен');
    } catch (err) {
      alert('Ошибка остановки мониторинга: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleRefreshTokens = async () => {
    try {
      await axios.post(`${API}/accounts/refresh-tokens`);
      addNotification('🔄 Токены обновлены');
      loadData();
    } catch (err) {
      alert('Ошибка обновления токенов: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Загрузка...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Шапка */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">🎮 Twitch Drops Miner</h1>
              <span className="ml-2 text-sm text-gray-500">v2.0 (веб-версия)</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  monitoring.active 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-gray-100 text-gray-800'
                }`}>
                  {monitoring.active ? '🟢 Мониторинг активен' : '🔴 Мониторинг остановлен'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Уведомления */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className="bg-white shadow-lg border border-gray-200 rounded-lg p-4 max-w-sm animate-fade-in"
          >
            <p className="text-sm text-gray-800">{notification.message}</p>
            <p className="text-xs text-gray-500 mt-1">
              {notification.timestamp.toLocaleTimeString('ru-RU')}
            </p>
          </div>
        ))}
      </div>

      {/* Основной контент */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Статистика */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">👥</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Всего аккаунтов</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.total_accounts || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">✅</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Активных аккаунтов</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.active_accounts || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">🎁</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Дропов получено</p>
                <p className="text-2xl font-semibold text-gray-900">{statistics.total_drops_claimed || 0}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl">⚙️</span>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Интервал проверки</p>
                <p className="text-2xl font-semibold text-gray-900">{settings.check_interval || 60}с</p>
              </div>
            </div>
          </div>
        </div>

        {/* Панель управления */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Панель управления</h2>
          
          <div className="flex flex-wrap gap-4">
            <button
              onClick={() => setIsAddAccountModalOpen(true)}
              className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 flex items-center gap-2"
            >
              <span>👥</span>
              Добавить аккаунт
            </button>
            
            {monitoring.active ? (
              <button
                onClick={handleStopMonitoring}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 flex items-center gap-2"
              >
                <span>🛑</span>
                Остановить мониторинг
              </button>
            ) : (
              <button
                onClick={handleStartMonitoring}
                disabled={accounts.length === 0}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50 flex items-center gap-2"
              >
                <span>🚀</span>
                Запустить мониторинг
              </button>
            )}
            
            <button
              onClick={handleRefreshTokens}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 flex items-center gap-2"
            >
              <span>🔄</span>
              Обновить токены
            </button>
            
            <button
              onClick={() => setIsSettingsModalOpen(true)}
              className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 flex items-center gap-2"
            >
              <span>⚙️</span>
              Настройки
            </button>
            
            <button
              onClick={() => setIsGameSelectionModalOpen(true)}
              className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 flex items-center gap-2"
            >
              <span>🎮</span>
              Выбрать игры
            </button>
          </div>
        </div>

        {/* Аккаунты */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              Аккаунты ({accounts.length}/20)
            </h2>
          </div>
          
          {accounts.length === 0 ? (
            <div className="text-center py-12">
              <span className="text-6xl mb-4 block">👥</span>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Нет добавленных аккаунтов</h3>
              <p className="text-gray-500 mb-4">Добавьте аккаунты для начала работы</p>
              <button
                onClick={() => setIsAddAccountModalOpen(true)}
                className="bg-purple-600 text-white px-6 py-3 rounded hover:bg-purple-700"
              >
                Добавить первый аккаунт
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {accounts.map(account => (
                <AccountCard
                  key={account.id}
                  account={account}
                  onDelete={(id) => setAccounts(prev => prev.filter(a => a.id !== id))}
                  loadData={loadData}
                  addNotification={addNotification}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Модальные окна */}
      <AddAccountModal
        isOpen={isAddAccountModalOpen}
        onClose={() => setIsAddAccountModalOpen(false)}
        onAccountAdded={async () => {
          console.log('Account added callback triggered');
          await loadData();
          addNotification('✅ Аккаунт успешно добавлен!');
        }}
      />
      
      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        settings={settings}
        onSettingsUpdate={async () => {
          await loadData();
          addNotification('✅ Настройки сохранены!');
        }}
      />
      
      <GameSelectionModal
        isOpen={isGameSelectionModalOpen}
        onClose={() => setIsGameSelectionModalOpen(false)}
        settings={settings}
        onSettingsUpdate={async () => {
          await loadData();
          addNotification('🎮 Игры для мониторинга обновлены!');
        }}
      />
    </div>
  );
};

export default App;