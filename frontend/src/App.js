import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { 
  User, 
  Plus, 
  Trash2, 
  Play, 
  Square, 
  Monitor, 
  Gamepad2,
  Clock,
  Gift,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  Settings,
  RefreshCw,
  ExternalLink
} from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [activeTab, setActiveTab] = useState('accounts');
  const [accounts, setAccounts] = useState([]);
  const [games, setGames] = useState([]);
  const [farmingSessions, setFarmingSessions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddAccountModal, setShowAddAccountModal] = useState(false);
  const [selectedGame, setSelectedGame] = useState(null);
  const [selectedAccount, setSelectedAccount] = useState(null);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadAccounts();
    loadGames();
    loadFarmingSessions();
    loadLogs();
    
    // Автообновление данных каждые 30 секунд
    const interval = setInterval(() => {
      loadFarmingSessions();
      loadLogs();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/accounts`);
      setAccounts(response.data);
    } catch (error) {
      console.error('Ошибка загрузки аккаунтов:', error);
    }
  };

  const loadGames = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/games`);
      setGames(response.data.games || []);
    } catch (error) {
      console.error('Ошибка загрузки игр:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFarmingSessions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/farming-status`);
      setFarmingSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Ошибка загрузки статуса фарма:', error);
    }
  };

  const loadLogs = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/logs`);
      setLogs(response.data.logs || []);
    } catch (error) {
      console.error('Ошибка загрузки логов:', error);
    }
  };

  const addAccount = async () => {
    try {
      setLoading(true);
      setShowAddAccountModal(true);
      // Данные для верификации получаем в модальном окне
      await loadAccounts();
    } catch (error) {
      console.error('Ошибка добавления аккаунта:', error);
      alert('Ошибка добавления аккаунта: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteAccount = async (accountId) => {
    if (!window.confirm('Вы уверены, что хотите удалить этот аккаунт?')) {
      return;
    }

    try {
      await axios.delete(`${API_BASE_URL}/api/accounts/${accountId}`);
      await loadAccounts();
    } catch (error) {
      console.error('Ошибка удаления аккаунта:', error);
      alert('Ошибка удаления аккаунта: ' + error.message);
    }
  };

  const startFarming = async () => {
    if (!selectedAccount || !selectedGame) {
      alert('Выберите аккаунт и игру');
      return;
    }

    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/api/start-farming`, {
        account_id: selectedAccount.id,
        game_id: selectedGame.id,
        game_name: selectedGame.name
      });
      
      // Обновляем статус
      await loadFarmingSessions();
      
      // Переключаемся на вкладку мониторинга
      setActiveTab('monitoring');
    } catch (error) {
      console.error('Ошибка запуска фарма:', error);
      alert('Ошибка запуска фарма: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const stopFarming = async (accountId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/stop-farming`, {
        account_id: accountId
      });
      
      await loadFarmingSessions();
    } catch (error) {
      console.error('Ошибка остановки фарма:', error);
      alert('Ошибка остановки фарма: ' + error.message);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active':
        return 'Активен';
      case 'pending':
        return 'Ожидает';
      case 'error':
        return 'Ошибка';
      default:
        return 'Неизвестно';
    }
  };

  const getSessionStatusText = (status) => {
    switch (status) {
      case 'searching':
        return 'Поиск стримера';
      case 'watching':
        return 'Смотрит стрим';
      case 'offline':
        return 'Стример офлайн';
      case 'completed':
        return 'Завершено';
      default:
        return status;
    }
  };

  const formatLogLevel = (level) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return 'error';
      case 'WARNING':
        return 'warning';
      case 'SUCCESS':
        return 'success';
      default:
        return 'info';
    }
  };

  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleString('ru-RU');
    } catch {
      return dateString;
    }
  };

  const AddAccountModal = () => {
    const [verificationData, setVerificationData] = useState(null);
    const [isVerifying, setIsVerifying] = useState(false);
    const [isLoadingVerification, setIsLoadingVerification] = useState(false);
    const [error, setError] = useState(null);
    const [debugInfo, setDebugInfo] = useState(null);

    const startVerification = async () => {
      setIsLoadingVerification(true);
      setError(null);
      setDebugInfo(null);
      
      try {
        console.log('🚀 Начинаем процесс верификации...');
        console.log('📡 API_BASE_URL:', API_BASE_URL);
        
        const response = await axios.post(`${API_BASE_URL}/api/accounts/add`, {}, {
          timeout: 15000,
          headers: {
            'Content-Type': 'application/json',
          }
        });
        
        console.log('✅ Успешный ответ API:', response.data);
        setVerificationData(response.data);
        setDebugInfo({
          status: 'success',
          url: `${API_BASE_URL}/api/accounts/add`,
          response: response.data
        });
        
        // Начинаем проверку авторизации
        const accountId = response.data.account_id;
        let pollCount = 0;
        const maxPolls = 120; // 10 минут (5 секунд * 120)
        
        const pollInterval = setInterval(async () => {
          pollCount++;
          
          try {
            console.log(`🔄 Проверка авторизации #${pollCount}...`);
            const verifyResponse = await axios.post(`${API_BASE_URL}/api/accounts/${accountId}/verify`, {}, {
              timeout: 10000
            });
            
            console.log('📝 Статус верификации:', verifyResponse.data);
            
            if (verifyResponse.data.status === 'active') {
              clearInterval(pollInterval);
              setShowAddAccountModal(false);
              setVerificationData(null);
              setError(null);
              await loadAccounts();
              alert(`🎉 Аккаунт ${verifyResponse.data.username} успешно добавлен!`);
            } else if (verifyResponse.data.status === 'expired') {
              clearInterval(pollInterval);
              setError('⏰ Время авторизации истекло. Попробуйте еще раз.');
            } else if (verifyResponse.data.status === 'error') {
              clearInterval(pollInterval);
              setError('❌ Ошибка авторизации: ' + (verifyResponse.data.message || 'Неизвестная ошибка'));
            }
          } catch (pollError) {
            console.error('❌ Ошибка проверки авторизации:', pollError);
            if (pollCount >= maxPolls) {
              clearInterval(pollInterval);
              setError('⏰ Превышено время ожидания авторизации');
            }
          }
        }, 5000);

        // Останавливаем проверку через 10 минут
        setTimeout(() => {
          clearInterval(pollInterval);
          setIsVerifying(false);
          if (!error) {
            setError('⏰ Время авторизации истекло');
          }
        }, 600000);
        
      } catch (error) {
        console.error('❌ Ошибка начала верификации:', error);
        
        let errorMessage = 'Неизвестная ошибка';
        let debugDetails = {
          status: 'error',
          url: `${API_BASE_URL}/api/accounts/add`,
          error: error.message
        };
        
        if (error.code === 'ECONNABORTED') {
          errorMessage = 'Превышено время ожидания. Проверьте соединение с интернетом.';
        } else if (error.response) {
          errorMessage = `Ошибка сервера: ${error.response.status} - ${error.response.data?.detail || error.response.statusText}`;
          debugDetails.response = error.response.data;
          debugDetails.status_code = error.response.status;
        } else if (error.request) {
          errorMessage = 'Не удалось связаться с сервером. Проверьте подключение к интернету.';
          debugDetails.request_details = 'No response received';
        }
        
        setError(errorMessage);
        setDebugInfo(debugDetails);
      } finally {
        setIsLoadingVerification(false);
      }
    };

    useEffect(() => {
      if (showAddAccountModal) {
        startVerification();
      }
    }, [showAddAccountModal]);

    const retryVerification = () => {
      setError(null);
      setVerificationData(null);
      setDebugInfo(null);
      startVerification();
    };

    return (
      <div className="modal">
        <div className="modal-content">
          <h3>🔗 Добавление нового аккаунта Twitch</h3>
          
          {isLoadingVerification && (
            <div className="loading">
              <div className="spinner"></div>
              <span style={{marginLeft: '10px'}}>Получение кода активации...</span>
            </div>
          )}
          
          {error && (
            <div className="network-error">
              <h4>⚠️ Ошибка подключения</h4>
              <p>{error}</p>
              <button className="retry-button" onClick={retryVerification}>
                <RefreshCw size={16} style={{marginRight: '8px'}} />
                Попробовать снова
              </button>
              
              {debugInfo && (
                <div className="debug-info">
                  <h5>🔍 Отладочная информация:</h5>
                  <div>URL: {debugInfo.url}</div>
                  <div>Статус: {debugInfo.status}</div>
                  {debugInfo.status_code && <div>HTTP статус: {debugInfo.status_code}</div>}
                  {debugInfo.error && <div>Ошибка: {debugInfo.error}</div>}
                  {debugInfo.response && <div>Ответ: {JSON.stringify(debugInfo.response, null, 2)}</div>}
                </div>
              )}
            </div>
          )}
          
          {!isLoadingVerification && !error && verificationData && (
            <div className="verification-code">
              <div className="success-message">
                <h4>✅ Код активации получен!</h4>
              </div>
              
              <div className="code-display">
                <div className="code-text">
                  {verificationData.user_code}
                </div>
              </div>
              
              <div style={{backgroundColor: '#16213e', padding: '20px', borderRadius: '12px', marginBottom: '20px'}}>
                <h4 style={{color: '#9146ff', marginBottom: '15px'}}>📋 Инструкция по активации:</h4>
                
                <div className="instruction-step">
                  <strong>1.</strong> Откройте новую вкладку в браузере
                </div>
                
                <div className="instruction-step">
                  <strong>2.</strong> Перейдите по ссылке:
                  <a href="https://www.twitch.tv/activate" target="_blank" rel="noopener noreferrer" className="twitch-link">
                    <ExternalLink size={16} style={{marginRight: '8px'}} />
                    https://www.twitch.tv/activate
                  </a>
                </div>
                
                <div className="instruction-step">
                  <strong>3.</strong> Введите код активации: <span style={{color: '#9146ff', fontWeight: 'bold'}}>{verificationData.user_code}</span>
                </div>
                
                <div className="instruction-step">
                  <strong>4.</strong> Войдите в свой аккаунт Twitch
                </div>
                
                <div className="instruction-step">
                  <strong>5.</strong> Подтвердите авторизацию приложения
                </div>
                
                <div className="instruction-step" style={{borderColor: '#2ed573', color: '#2ed573'}}>
                  <strong>6.</strong> Вернитесь сюда - окно автоматически закроется!
                </div>
              </div>
              
              <div className="waiting-animation pulse">
                <div className="spinner"></div>
                <span style={{marginLeft: '10px', fontWeight: 'bold'}}>Ожидание авторизации на Twitch...</span>
              </div>
            </div>
          )}

          <div style={{display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px'}}>
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setShowAddAccountModal(false);
                setVerificationData(null);
                setError(null);
                setDebugInfo(null);
              }}
            >
              Отменить
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="container">
      <div className="header">
        <h1>🎮 Twitch Drops Miner</h1>
        <p>Автоматический сбор дропов с Twitch</p>
      </div>

      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'accounts' ? 'active' : ''}`}
          onClick={() => setActiveTab('accounts')}
        >
          <User className="w-4 h-4" />
          Аккаунты
        </button>
        <button 
          className={`tab ${activeTab === 'games' ? 'active' : ''}`}
          onClick={() => setActiveTab('games')}
        >
          <Gamepad2 className="w-4 h-4" />
          Игры
        </button>
        <button 
          className={`tab ${activeTab === 'monitoring' ? 'active' : ''}`}
          onClick={() => setActiveTab('monitoring')}
        >
          <Monitor className="w-4 h-4" />
          Мониторинг
        </button>
        <button 
          className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          <Settings className="w-4 h-4" />
          Логи
        </button>
      </div>

      {activeTab === 'accounts' && (
        <div className="card">
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
            <h2>Управление аккаунтами</h2>
            <button className="btn" onClick={addAccount} disabled={loading}>
              <Plus className="w-4 h-4" />
              Добавить аккаунт
            </button>
          </div>

          {accounts.length === 0 ? (
            <div className="alert info">
              <p>У вас нет добавленных аккаунтов. Добавьте аккаунт для начала работы.</p>
            </div>
          ) : (
            <div className="grid">
              {accounts.map(account => (
                <div key={account.id} className="account-item">
                  <div className="account-info">
                    <h4>{account.username || 'Неизвестный пользователь'}</h4>
                    <p>Добавлен: {formatDate(account.created_at)}</p>
                    <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginTop: '5px'}}>
                      {getStatusIcon(account.status)}
                      <span className={`status ${account.status}`}>
                        {getStatusText(account.status)}
                      </span>
                    </div>
                  </div>
                  <button 
                    className="btn btn-danger"
                    onClick={() => deleteAccount(account.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                    Удалить
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'games' && (
        <div className="card">
          <h2>Выбор игры для фарма дропов</h2>
          
          {accounts.filter(acc => acc.status === 'active').length === 0 && (
            <div className="alert warning">
              <p>Добавьте и активируйте хотя бы один аккаунт для просмотра игр</p>
            </div>
          )}

          {selectedAccount && (
            <div className="alert info">
              <p>Выбран аккаунт: <strong>{selectedAccount.username}</strong></p>
            </div>
          )}

          {accounts.filter(acc => acc.status === 'active').length > 0 && (
            <>
              <div style={{marginBottom: '20px'}}>
                <h3>Выберите аккаунт:</h3>
                <div className="grid grid-3" style={{marginBottom: '20px'}}>
                  {accounts.filter(acc => acc.status === 'active').map(account => (
                    <div 
                      key={account.id} 
                      className={`game-card ${selectedAccount?.id === account.id ? 'selected' : ''}`}
                      onClick={() => setSelectedAccount(account)}
                    >
                      <h4>{account.username}</h4>
                      <p>Активен</p>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{marginBottom: '20px'}}>
                <h3>Выберите игру:</h3>
                {loading ? (
                  <div className="loading">
                    <div className="spinner"></div>
                    <span>Загрузка игр...</span>
                  </div>
                ) : games.length === 0 ? (
                  <div className="alert warning">
                    <p>Нет доступных игр с дропами</p>
                  </div>
                ) : (
                  <div className="grid grid-3">
                    {games.map(game => (
                      <div 
                        key={game.id} 
                        className={`game-card ${selectedGame?.id === game.id ? 'selected' : ''}`}
                        onClick={() => setSelectedGame(game)}
                      >
                        <img src={game.box_art_url} alt={game.name} />
                        <h4>{game.name}</h4>
                        <p>Дропы доступны</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {selectedAccount && selectedGame && (
                <div style={{textAlign: 'center', marginTop: '20px'}}>
                  <button 
                    className="btn btn-success"
                    onClick={startFarming}
                    disabled={loading}
                  >
                    <Play className="w-4 h-4" />
                    Начать фарм дропов
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'monitoring' && (
        <div className="card">
          <h2>Мониторинг фарма дропов</h2>
          
          {farmingSessions.length === 0 ? (
            <div className="alert info">
              <p>Нет активных сессий фарма. Запустите фарм во вкладке "Игры".</p>
            </div>
          ) : (
            <div className="grid">
              {farmingSessions.map(session => (
                <div key={session.account_id} className="session-card">
                  <div className="session-header">
                    <div className="session-info">
                      <h4>{session.username}</h4>
                      <p>Игра: {session.game_name}</p>
                      <p>Стример: {session.streamer_name || 'Поиск...'}</p>
                      <p>Запущен: {formatDate(session.started_at)}</p>
                    </div>
                    <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                      <span className={`session-status ${session.status}`}>
                        {getSessionStatusText(session.status)}
                      </span>
                      <button 
                        className="btn btn-danger"
                        onClick={() => stopFarming(session.account_id)}
                      >
                        <Square className="w-4 h-4" />
                        Остановить
                      </button>
                    </div>
                  </div>

                  {session.drops_progress && session.drops_progress.length > 0 && (
                    <div className="drops-progress">
                      <h4>Прогресс дропов:</h4>
                      {session.drops_progress.map(drop => (
                        <div key={drop.id} className="drop-item">
                          <h5>{drop.name}</h5>
                          <p>{drop.benefit}</p>
                          <div className="progress-bar">
                            <div 
                              className="progress-fill"
                              style={{width: `${drop.percentage_progress}%`}}
                            >
                              {drop.percentage_progress.toFixed(1)}%
                            </div>
                          </div>
                          <p>
                            {drop.current_minutes_watched} / {drop.minutes_required} минут
                            {drop.is_claimable && (
                              <span style={{color: '#2ed573', marginLeft: '10px'}}>
                                <Gift className="w-4 h-4" style={{display: 'inline'}} />
                                Готов к получению!
                              </span>
                            )}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="card">
          <h2>Логи системы</h2>
          
          <div className="log-container">
            {logs.length === 0 ? (
              <div className="alert info">
                <p>Логи пусты</p>
              </div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className={`log-entry ${formatLogLevel(log.level)}`}>
                  <span className="log-timestamp">
                    {formatDate(log.timestamp)}
                  </span>
                  <span>{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {showAddAccountModal && <AddAccountModal />}
    </div>
  );
}

export default App;