import ccxt
import time

# Укажите API ключи Testnet
api_key = '8e5474ab68cfecc10d30c5f8353d45511a1bd0bf79509a0f49ec7a640a2611eb'
api_secret = '96f1bfb069b96fa9773079e1c436135a8153258d7a215dc836b105738243c48a'

# Подключение к Binance Testnet
binance_testnet = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'options': {'defaultType': 'future'},  # Для торговли фьючерсами
})
binance_testnet.set_sandbox_mode(True)  # Включаем тестовый режим

# Проверка подключения
try:
    balance = binance_testnet.fetch_balance()
    print("Подключение успешно! Баланс:")
    print(balance)
except Exception as e:
    print(f"Ошибка подключения: {e}")
    exit()

# Параметры ордера
symbol = 'EOS/USDT'  # Торговая пара
order_type = 'market'  # Тип ордера: limit, market и т.д.
side = 'buy'  # Сторона: buy или sell
amount = 1000  # Количество для покупки/продажи

# Создание ордера
try:
    order = binance_testnet.create_order(
        symbol=symbol,
        type=order_type,
        side=side,
        amount=amount
    )
    print("Ордер создан:")
    print(order)
except Exception as e:
    print(f"Ошибка при создании ордера: {e}")

# Проверка статуса ордера
try:
    time.sleep(2)  # Небольшая пауза для обновления статуса
    order_status = binance_testnet.fetch_order(order['id'], symbol)
    print("Статус ордера:")
    print(order_status)
except Exception as e:
    print(f"Ошибка при проверке статуса ордера: {e}")
