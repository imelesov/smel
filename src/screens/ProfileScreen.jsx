import { useState } from 'react'
import { ArrowLeft, User, Copy, Check, Shield, RefreshCw } from 'lucide-react'
import '../App.css'

function ProfileScreen({ user, userData, navigate, refreshData }) {
  const [copied, setCopied] = useState(false)
  const [regenerating, setRegenerating] = useState(false)

  const vlessLink = userData?.uuid 
    ? `vless://${userData.uuid}@vpn.example.com:443?security=reality&type=tcp&fp=chrome#SmelVPN`
    : ''

  const copyToClipboard = () => {
    navigator.clipboard.writeText(vlessLink)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const regenerateUUID = async () => {
    const tg = window.Telegram?.WebApp
    
    const confirm = () => {
      if (tg) {
        tg.showPopup({
          title: 'Подтверждение',
          message: 'Вы уверены, что хотите перевыпустить ключ? Старый ключ перестанет работать.',
          buttons: [
            { id: 'confirm', text: 'Да', type: 'default' },
            { id: 'cancel', text: 'Отмена', type: 'destructive' }
          ]
        }, handleConfirm)
      } else {
        if (confirm('Вы уверены, что хотите перевыпустить ключ? Старый ключ перестанет работать.')) {
          handleConfirm('confirm')
        }
      }
    }

    const handleConfirm = async (buttonId) => {
      if (buttonId === 'confirm') {
        setRegenerating(true)
        try {
          const API_BASE = '/api'
          const res = await fetch(`${API_BASE}/regenerate-uuid`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: user.id })
          })
          
          if (res.ok) {
            if (tg) {
              tg.showAlert('Ключ успешно перевыпущен')
            } else {
              alert('Ключ успешно перевыпущен')
            }
            refreshData()
          } else {
            if (tg) {
              tg.showAlert('Ошибка при перевыпуске ключа')
            } else {
              alert('Ошибка при перевыпуске ключа')
            }
          }
        } catch (error) {
          if (tg) {
            tg.showAlert('Ошибка соединения')
          } else {
            alert('Ошибка соединения')
          }
        } finally {
          setRegenerating(false)
        }
      }
    }

    confirm()
  }

  return (
    <div className="container">
      <header className="header">
        <button className="back-btn" onClick={() => navigate('home')}>
          <ArrowLeft size={24} />
        </button>
        <h1>Профиль</h1>
        <div className="spacer"></div>
      </header>

      <main className="main">
        <div className="profile-header">
          <div className="profile-avatar">
            <User size={48} />
          </div>
          <div className="profile-info">
            <h2>{user?.first_name}</h2>
            <p>@{user?.username || 'без username'}</p>
          </div>
        </div>

        <div className="info-cards">
          <div className="info-card">
            <Shield size={20} className="info-icon" />
            <div className="info-content">
              <p className="info-label">Тариф</p>
              <p className="info-value">{userData?.plan || 'Нет подписки'}</p>
            </div>
          </div>

          <div className="info-card">
            <User size={20} className="info-icon" />
            <div className="info-content">
              <p className="info-label">Устройства</p>
              <p className="info-value">{userData?.devices || 0}</p>
            </div>
          </div>

          <div className="info-card">
            <Copy size={20} className="info-icon" />
            <div className="info-content">
              <p className="info-label">Подписка до</p>
              <p className="info-value">{userData?.subscription_until || 'Не активна'}</p>
            </div>
          </div>

          <div className="info-card">
            <Copy size={20} className="info-icon" />
            <div className="info-content">
              <p className="info-label">Баланс</p>
              <p className="info-value">{userData?.balance || 0} ₽</p>
            </div>
          </div>
        </div>

        {vlessLink && (
          <div className="vpn-key-section">
            <h3>Ваш VPN ключ</h3>
            <div className="vpn-key-card">
              <code className="vpn-key">{vlessLink}</code>
              <button 
                className="copy-btn"
                onClick={copyToClipboard}
                disabled={copied}
              >
                {copied ? <Check size={20} /> : <Copy size={20} />}
              </button>
            </div>
            <button 
              className="regenerate-btn"
              onClick={regenerateUUID}
              disabled={regenerating}
            >
              <RefreshCw size={18} className={regenerating ? 'spinning' : ''} />
              {regenerating ? 'Перевыпуск...' : 'Перевыпустить ключ'}
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

export default ProfileScreen
