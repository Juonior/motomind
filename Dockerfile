FROM python:3.10-slim

# Установка системных зависимостей для работы с Bluetooth и OBD
RUN apt-get update && apt-get install -y \
    bluetooth \
    bluez \
    bluez-tools \
    libbluetooth-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Копирование и установка скрипта инициализации Bluetooth
COPY init_bluetooth.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init_bluetooth.sh

# Запуск бота через скрипт инициализации
ENTRYPOINT ["/usr/local/bin/init_bluetooth.sh"]
CMD ["python", "bot.py"]

