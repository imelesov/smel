import { Shield, Wifi, WifiOff, User, CreditCard, Gift, ChevronRight, Crown } from 'lucide-react'
import '../App.css'

function HomeScreen({ user, userData, navigate }) {
  const isSubscribed = userData?.subscription_until && userData?.plan
  const subscriptionActive = isSubscribed && new Date(userData.subscription_until.split('.').reverse().join('-')) > new Date()

  const handleConnectVPN = () => {
    if (!subscriptionActive) {
      const tg = window.Telegram?.WebApp
      if (tg) {
        tg.showAlert('Сначала оформите подписку')
      } else {
        alert('Сначала оформите подписку')
      }
      navigate('subscription')
      return
    }
    
    // Открываем сайт VPN
    const vpnUrl = 'https://vpn.example.com' // Замени на реальный URL твоего VPN сайта
    const tg = window.Telegram?.WebApp
    
    if (tg) {
      tg.openLink(vpnUrl)
    } else {
      window.open(vpnUrl, '_blank')
    }
  }

  return (
    <div className="container">
      <header className="header">
        <div className="logo">
          <Shield className="logo-icon" size={32} />
          <h1>Smel VPN</h1>
        </div>
        {user && <div className="user-badge">{user.first_name}</div>}
      </header>

      <main className="main">
        <div className={`status-card ${subscriptionActive ? 'connected' : 'disconnected'}`}>
          <div className="status-icon">
            {subscriptionActive ? <Wifi size={48} /> : <WifiOff size={48} />}
          </div>
          <div className="status-content">
            <h2 className="status-title">
              {subscriptionActive ? 'Подключено' : 'Отключено'}
            </h2>
            <p className="status-subtitle">
              {subscriptionActive 
                ? `Подписка до: ${userData?.subscription_until}` 
                : 'Оформите подписку для подключения'}
            </p>
          </div>
        </div>

        {subscriptionActive && (
          <button className="connect-btn" onClick={handleConnectVPN}>
            <Wifi size={20} />
            Подключить VPN
          </button>
        )}

        <div className="stats-grid">
          <div className="stat-card" onClick={() => navigate('profile')}>
            <User size={24} className="stat-icon" />
            <div className="stat-content">
              <p className="stat-label">Профиль</p>
              <p className="stat-value">{userData?.plan || 'Нет подписки'}</p>
            </div>
            <ChevronRight size={20} className="stat-arrow" />
          </div>

          <div className="stat-card" onClick={() => navigate('subscription')}>
            <CreditCard size={24} className="stat-icon" />
            <div className="stat-content">
              <p className="stat-label">Подписка</p>
              <p className="stat-value">{userData?.subscription_until || 'Не активна'}</p>
            </div>
            <ChevronRight size={20} className="stat-arrow" />
          </div>

          <div className="stat-card" onClick={() => navigate('referral')}>
            <Gift size={24} className="stat-icon" />
            <div className="stat-content">
              <p className="stat-label">Рефералы</p>
              <p className="stat-value">{userData?.balance || 0} ₽</p>
            </div>
            <ChevronRight size={20} className="stat-arrow" />
          </div>
        </div>

        {!subscriptionActive && (
          <div className="promo-card">
            <Crown size={32} className="promo-icon" />
            <h3>Оформите подписку</h3>
            <p>Получите доступ к VPN и начните пользоваться уже сегодня</p>
            <button className="promo-btn" onClick={() => navigate('subscription')}>
              Выбрать тариф
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default HomeScreen
