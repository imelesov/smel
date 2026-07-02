import { useEffect, useState } from 'react'
import { Shield, Wifi, WifiOff, Globe, Zap, Clock, Settings, ChevronRight, User, CreditCard, Gift, ArrowLeft, Copy, Check, Crown, Star } from 'lucide-react'
import './App.css'

// Screens
import HomeScreen from './screens/HomeScreen'
import ProfileScreen from './screens/ProfileScreen'
import SubscriptionScreen from './screens/SubscriptionScreen'
import ReferralScreen from './screens/ReferralScreen'

function App() {
  const [currentScreen, setCurrentScreen] = useState('home')
  const [user, setUser] = useState(null)
  const [userData, setUserData] = useState(null)
  const [referralData, setReferralData] = useState(null)
  const [plans, setPlans] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Проверка на наличие Telegram WebApp
    if (!window.Telegram || !window.Telegram.WebApp) {
      console.log('Telegram WebApp не найден, используем тестовый режим')
      // Тестовый режим для локальной разработки
      setUser({ id: 1742568382, first_name: 'Test User', username: 'testuser' })
      fetchData(1742568382)
      applyTheme({
        themeParams: {
          bg_color: '#0f0f0f',
          text_color: '#ffffff',
          hint_color: '#888888',
          link_color: '#3b82f6',
          button_color: '#3b82f6',
          button_text_color: '#ffffff',
          secondary_bg_color: '#1a1a1a'
        }
      })
      setLoading(false)
      return
    }

    const tg = window.Telegram.WebApp
    tg.expand()
    
    if (tg.initDataUnsafe.user) {
      setUser(tg.initDataUnsafe.user)
      fetchData(tg.initDataUnsafe.user.id)
    } else {
      // Если пользователь не авторизован в Telegram, используем тестовый режим
      console.log('Пользователь не авторизован в Telegram, используем тестовый режим')
      setUser({ id: 1742568382, first_name: 'Test User', username: 'testuser' })
      fetchData(1742568382)
    }
    
    applyTheme(tg)
  }, [])

  const applyTheme = (tg) => {
    document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#0f0f0f')
    document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#ffffff')
    document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#888888')
    document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#3b82f6')
    document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#3b82f6')
    document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff')
    document.documentElement.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#1a1a1a')
  }

  const fetchData = async (telegramId) => {
    try {
      const API_BASE = '/api'  // Используем относительный путь для проксирования через Vite
      
      const [userRes, referralRes, plansRes] = await Promise.all([
        fetch(`${API_BASE}/user/${telegramId}`),
        fetch(`${API_BASE}/referrals/${telegramId}`),
        fetch(`${API_BASE}/plans`)
      ])
      
      if (userRes.ok) {
        const userData = await userRes.json()
        setUserData(userData)
      } else {
        console.error('User API error:', userRes.status)
        setUserData({})
      }
      
      if (referralRes.ok) {
        const referralData = await referralRes.json()
        setReferralData(referralData)
      } else {
        console.error('Referral API error:', referralRes.status)
        setReferralData({ invited: 0, connected: 0, balance: 0, ref_link: '' })
      }
      
      if (plansRes.ok) {
        const plansData = await plansRes.json()
        setPlans(plansData)
      } else {
        console.error('Plans API error:', plansRes.status)
        // Fallback данные для планов
        setPlans({
          plans: {
            basic: { "1m": 200, "3m": 540, "6m": 960 },
            standard: { "1m": 400, "3m": 1080, "6m": 1920 },
            family: { "1m": 500, "3m": 1350, "6m": 2400 }
          },
          devices: { basic: 2, standard: 4, family: 6 },
          plan_names: { basic: "Базовый", standard: "Стандарт", family: "Семейный" },
          periods: { "1m": "1 месяц", "3m": "3 месяца", "6m": "6 месяцев" }
        })
      }
    } catch (error) {
      console.error('Error fetching data:', error)
      // Fallback данные при ошибке
      setUserData({})
      setReferralData({ invited: 0, connected: 0, balance: 0, ref_link: '' })
      setPlans({
        plans: {
          basic: { "1m": 200, "3m": 540, "6m": 960 },
          standard: { "1m": 400, "3m": 1080, "6m": 1920 },
          family: { "1m": 500, "3m": 1350, "6m": 2400 }
        },
        devices: { basic: 2, standard: 4, family: 6 },
        plan_names: { basic: "Базовый", standard: "Стандарт", family: "Семейный" },
        periods: { "1m": "1 месяц", "3m": "3 месяца", "6m": "6 месяцев" }
      })
    } finally {
      setLoading(false)
    }
  }

  const navigate = (screen) => {
    setCurrentScreen(screen)
  }

  const refreshData = () => {
    if (user) {
      fetchData(user.id)
    }
  }

  if (loading) {
    return (
      <div className="app">
        <div className="loading-screen">
          <div className="loading-spinner"></div>
          <p>Загрузка...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="app">
      {currentScreen === 'home' && (
        <HomeScreen 
          user={user}
          userData={userData}
          navigate={navigate}
        />
      )}
      
      {currentScreen === 'profile' && (
        <ProfileScreen 
          user={user}
          userData={userData}
          navigate={navigate}
          refreshData={refreshData}
        />
      )}
      
      {currentScreen === 'subscription' && (
        <SubscriptionScreen 
          user={user}
          userData={userData}
          plans={plans}
          navigate={navigate}
          refreshData={refreshData}
        />
      )}
      
      {currentScreen === 'referral' && (
        <ReferralScreen 
          user={user}
          referralData={referralData}
          navigate={navigate}
        />
      )}
    </div>
  )
}

export default App
