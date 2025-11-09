#!/bin/bash
# Не используем set -e, чтобы обрабатывать ошибки вручную

# Скрипт инициализации Bluetooth для OBD адаптера

echo "Инициализация Bluetooth для OBD..."

# Если указан порт в переменной окружения
if [ -n "$OBD_PORT" ] && [[ "$OBD_PORT" == /dev/rfcomm* ]]; then
    RFCOMM_NUM=$(echo $OBD_PORT | sed 's|/dev/rfcomm||')
    
    # Если указан MAC адрес, всегда пересоздаем порт
    if [ -n "$OBD_MAC" ]; then
        # Проверяем формат MAC адреса
        if ! echo "$OBD_MAC" | grep -qE "^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"; then
            echo "❌ Неверный формат MAC адреса: $OBD_MAC"
            echo "   Ожидается формат: XX:XX:XX:XX:XX:XX"
            exit 1
        fi
        
        # Проверяем, что устройство сопряжено (только информационно)
        # Примечание: bluetoothctl не работает в Docker, сопряжение нужно делать на хосте
        echo "Проверка устройства $OBD_MAC..."
        
        # Освобождаем порт, если он уже занят
        if [ -e "$OBD_PORT" ]; then
            echo "Освобождение существующего порта $OBD_PORT..."
            rfcomm release $RFCOMM_NUM 2>/dev/null || true
            sleep 1
        fi
        
        echo "Подключение к устройству $OBD_MAC на порт $OBD_PORT..."
        if rfcomm bind $RFCOMM_NUM "$OBD_MAC" 1 2>/dev/null; then
            # Проверяем, что порт действительно создан
            sleep 1
            if [ -e "$OBD_PORT" ]; then
                echo "✅ RFCOMM порт $OBD_PORT успешно создан для устройства $OBD_MAC"
            else
                echo "⚠️  Команда выполнена, но порт $OBD_PORT не найден"
                echo "   Возможно, устройство недоступно или не сопряжено"
            fi
        else
            echo "❌ Не удалось создать RFCOMM порт. Убедитесь что:"
            echo "   1. Устройство включено и находится в зоне действия"
            echo "   2. Устройство уже сопряжено с системой (bluetoothctl pair $OBD_MAC)"
            echo "   3. MAC адрес указан правильно: $OBD_MAC"
            echo ""
            echo "   Для сопряжения устройства выполните на хосте:"
            echo "   bluetoothctl scan on"
            echo "   bluetoothctl pair $OBD_MAC"
            echo "   bluetoothctl trust $OBD_MAC"
            exit 1
        fi
    else
        # Если MAC не указан, проверяем существование порта
        if [ ! -e "$OBD_PORT" ]; then
            echo "⚠️  Предупреждение: OBD_PORT указан как $OBD_PORT, но OBD_MAC не задан."
            echo "   RFCOMM порт должен быть создан вручную на хосте перед запуском контейнера."
        else
            echo "✅ Порт $OBD_PORT уже существует (создан вручную)."
        fi
    fi
else
    echo "OBD_PORT не указан или не является RFCOMM портом. Пропускаем инициализацию Bluetooth."
fi

# Запускаем основной скрипт
exec "$@"

