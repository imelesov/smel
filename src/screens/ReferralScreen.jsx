import { ArrowLeft, Gift, Users, Copy, Check, Share2 } from 'lucide-react'
import { useState } from 'react'
import '../App.css'

function ReferralScreen({ user, referralData, navigate }) {
  const [copied, setCopied] = useState(false)

  const copyRefLink = () => {
    if (referralData?.ref_link) {
      navigator.clipboard.writeText(referralData.ref_link)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const shareRefLink = () => {
    const tg = window.Telegram?.WebApp
    if (referralData?.ref_link) {
      if (tg) {
        tg.openTelegramLink(
          `https://t.me/share/url?url=${encodeURIComponent(referralData.ref_link)}&text=Подключайся к Smel VPN 🚀`
        )
      } else {
        window.open(
          `https://t.me/share/url?url=${encodeURIComponent(referralData.ref_link)}&text=Подключайся к Smel VPN 🚀`,
          '_blank'
        )
      }
    }
  }

  return (
    <div className="container">
      <header className="header">
        <button className="back-btn" onClick={() => navigate('home')}>
          <ArrowLeft size={24} />
        </button>
        <h1>Рефералы</h1>
        <div className="spacer"></div>
      </header>

      <main className="main">
        <div className="referral-hero">
          <Gift size={48} className="hero-icon" />
          <h2>Приглашайте друзей</h2>
          <p>Получайте бонусы за каждого приглашенного друга</p>
        </div>

        <div className="referral-bonuses">
          <div className="bonus-card">
            <Users size={32} className="bonus-icon" />
            <div className="bonus-content">
              <h3>+3 дня</h3>
              <p>Когда друг подключит VPN</p>
            </div>
          </div>

          <div className="bonus-card">
            <Gift size={32} className="bonus-icon" />
            <div className="bonus-content">
              <h3>10%</h3>
              <p>От оплат ваших друзей</p>
            </div>
          </div>
        </div>

        <div className="referral-stats">
          <div className="stat-item">
            <p className="stat-number">{referralData?.invited || 0}</p>
            <p className="stat-label">Приглашено</p>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <p className="stat-number">{referralData?.connected || 0}</p>
            <p className="stat-label">Подключили</p>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item">
            <p className="stat-number">{referralData?.balance || 0} ₽</p>
            <p className="stat-label">Баланс</p>
          </div>
        </div>

        <div className="referral-link-section">
          <h3>Ваша реферальная ссылка</h3>
          <div className="ref-link-card">
            <code className="ref-link">{referralData?.ref_link || 'Загрузка...'}</code>
            <button 
              className="copy-link-btn"
              onClick={copyRefLink}
              disabled={copied}
            >
              {copied ? <Check size={20} /> : <Copy size={20} />}
            </button>
          </div>
          <button className="share-btn" onClick={shareRefLink}>
            <Share2 size={18} />
            Поделиться ссылкой
          </button>
        </div>

        <div className="referral-info">
          <h4>Как это работает?</h4>
          <ol>
            <li>Поделитесь ссылкой с друзьями</li>
            <li>Друг переходит по ссылке и оформляет подписку</li>
            <li>Вы получаете +3 дня, когда он подключит VPN</li>
            <li>Вы получаете 10% от каждой оплаты друга на баланс</li>
          </ol>
        </div>
      </main>
    </div>
  )
}

export default ReferralScreen
