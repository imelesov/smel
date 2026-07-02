import { ArrowLeft, CreditCard, Crown, Star, Check } from 'lucide-react'
import { useState } from 'react'
import '../App.css'

function SubscriptionScreen({ user, userData, plans, navigate, refreshData }) {
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [selectedPeriod, setSelectedPeriod] = useState(null)
  const [paymentMethod, setPaymentMethod] = useState(null)
  const [processing, setProcessing] = useState(false)

  const planIcons = {
    basic: <Star size={24} />,
    standard: <Crown size={24} />,
    family: <Crown size={24} />
  }

  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan)
    setSelectedPeriod(null)
    setPaymentMethod(null)
  }

  const handlePeriodSelect = (period) => {
    setSelectedPeriod(period)
    setPaymentMethod(null)
  }

  const handlePaymentMethod = (method) => {
    setPaymentMethod(method)
  }

  const handlePayment = async () => {
    if (!selectedPlan || !selectedPeriod || !paymentMethod) return

    const tg = window.Telegram?.WebApp
    setProcessing(true)

    try {
      const API_BASE = '/api'
      
      if (paymentMethod === 'balance') {
        const res = await fetch(`${API_BASE}/pay/balance`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: user.id,
            plan: selectedPlan,
            period: selectedPeriod
          })
        })

        const data = await res.json()
        
        if (data.success) {
          if (tg) {
            tg.showAlert('Подписка успешно активирована!')
          } else {
            alert('Подписка успешно активирована!')
          }
          refreshData()
          navigate('home')
        } else {
          if (tg) {
            tg.showAlert(data.error || 'Ошибка оплаты')
          } else {
            alert(data.error || 'Ошибка оплаты')
          }
        }
      } else if (paymentMethod === 'sbp') {
        const res = await fetch(`${API_BASE}/pay`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: user.id,
            plan: selectedPlan,
            period: selectedPeriod
          })
        })

        const data = await res.json()
        
        if (data.payment_id) {
          if (tg) {
            tg.showPopup({
              title: 'Оплата СБП',
              message: `Переведите ${data.price} ₽ на номер ${data.sbp_phone}\nБанк: ${data.sbp_bank}`,
              buttons: [
                { id: 'paid', text: 'Я оплатил' },
                { id: 'cancel', text: 'Отмена' }
              ]
            }, (buttonId) => {
              if (buttonId === 'paid') {
                tg.showAlert('Заявка отправлена на проверку')
                navigate('home')
              }
            })
          } else {
            alert(`Переведите ${data.price} ₽ на номер ${data.sbp_phone}\nБанк: ${data.sbp_bank}`)
            navigate('home')
          }
        }
      } else if (paymentMethod === 'crypto') {
        const res = await fetch(`${API_BASE}/pay/crypto`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: user.id,
            plan: selectedPlan,
            period: selectedPeriod
          })
        })

        const data = await res.json()
        
        if (data.pay_url) {
          if (tg) {
            tg.openLink(data.pay_url)
          } else {
            window.open(data.pay_url, '_blank')
          }
        } else {
          if (tg) {
            tg.showAlert(data.error || 'Ошибка создания платежа')
          } else {
            alert(data.error || 'Ошибка создания платежа')
          }
        }
      }
    } catch (error) {
      if (tg) {
        tg.showAlert('Ошибка соединения')
      } else {
        alert('Ошибка соединения')
      }
    } finally {
      setProcessing(false)
    }
  }

  const price = plans?.plans?.[selectedPlan]?.[selectedPeriod] || 0
  const canPayWithBalance = userData?.balance >= price

  return (
    <div className="container">
      <header className="header">
        <button className="back-btn" onClick={() => navigate('home')}>
          <ArrowLeft size={24} />
        </button>
        <h1>Подписка</h1>
        <div className="spacer"></div>
      </header>

      <main className="main">
        {!selectedPlan && (
          <>
            <h2 className="section-title">Выберите тариф</h2>
            <div className="plans-grid">
              {plans?.plan_names && Object.entries(plans.plan_names).map(([key, name]) => (
                <div 
                  key={key}
                  className="plan-card"
                  onClick={() => handlePlanSelect(key)}
                >
                  <div className="plan-icon">{planIcons[key]}</div>
                  <h3>{name}</h3>
                  <p>{plans.devices[key]} устройств</p>
                  <p className="plan-price">от {plans.plans[key]['1m']} ₽/мес</p>
                </div>
              ))}
            </div>
          </>
        )}

        {selectedPlan && !selectedPeriod && (
          <>
            <button className="back-link" onClick={() => setSelectedPlan(null)}>
              <ArrowLeft size={16} /> Назад к тарифам
            </button>
            <h2 className="section-title">Выберите срок</h2>
            <div className="periods-grid">
              {plans?.periods && Object.entries(plans.periods).map(([key, name]) => (
                <div 
                  key={key}
                  className="period-card"
                  onClick={() => handlePeriodSelect(key)}
                >
                  <h3>{name}</h3>
                  <p className="period-price">{plans.plans[selectedPlan][key]} ₽</p>
                </div>
              ))}
            </div>
          </>
        )}

        {selectedPlan && selectedPeriod && !paymentMethod && (
          <>
            <button className="back-link" onClick={() => setSelectedPeriod(null)}>
              <ArrowLeft size={16} /> Назад к срокам
            </button>
            <h2 className="section-title">Способ оплаты</h2>
            <div className="payment-methods">
              <div 
                className={`payment-card ${canPayWithBalance ? '' : 'disabled'}`}
                onClick={() => canPayWithBalance && handlePaymentMethod('balance')}
              >
                <CreditCard size={24} />
                <div className="payment-content">
                  <h3>С баланса</h3>
                  <p>Доступно: {userData?.balance || 0} ₽</p>
                </div>
                {!canPayWithBalance && <span className="badge">Недостаточно</span>}
              </div>

              <div 
                className="payment-card"
                onClick={() => handlePaymentMethod('sbp')}
              >
                <CreditCard size={24} />
                <div className="payment-content">
                  <h3>СБП</h3>
                  <p>Оплата по номеру телефона</p>
                </div>
              </div>

              <div 
                className="payment-card"
                onClick={() => handlePaymentMethod('crypto')}
              >
                <Crown size={24} />
                <div className="payment-content">
                  <h3>CryptoBot</h3>
                  <p>Криптовалюта</p>
                </div>
              </div>
            </div>

            <div className="payment-summary">
              <p>К оплате: <strong>{price} ₽</strong></p>
            </div>
          </>
        )}

        {paymentMethod && (
          <>
            <button className="back-link" onClick={() => setPaymentMethod(null)}>
              <ArrowLeft size={16} /> Назад к способам оплаты
            </button>
            <div className="payment-confirm">
              <h2>Подтверждение оплаты</h2>
              <div className="confirm-details">
                <p>Тариф: {plans?.plan_names[selectedPlan]}</p>
                <p>Срок: {plans?.periods[selectedPeriod]}</p>
                <p>Сумма: <strong>{price} ₽</strong></p>
                <p>Способ: <strong>{
                  paymentMethod === 'balance' ? 'Баланс' :
                  paymentMethod === 'sbp' ? 'СБП' : 'CryptoBot'
                }</strong></p>
              </div>
              <button 
                className="confirm-btn"
                onClick={handlePayment}
                disabled={processing}
              >
                {processing ? 'Обработка...' : 'Оплатить'}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default SubscriptionScreen
