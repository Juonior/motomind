#!/bin/bash
set -e

# Скрипт инициализации Bluetooth для OBD адаптера

echo "Инициализация Bluetooth для OBD..."

# Если указан порт в переменной окружения
if [ -n "$OBD_PORT" ] && [[ "$OBD_PORT" == /dev/rfcomm* ]]; then
    RFCOMM_NUM=$(echo $OBD_PORT | sed 's|/dev/rfcomm||')
    
    # Проверяем, существует ли уже порт
    if [ ! -e "$OBD_PORT" ]; then
        echo "Порт $OBD_PORT не найден. Попытка создания..."
        
        # Если указан MAC адрес в переменной OBD_MAC
        if [ -n "$OBD_MAC" ]; then
            echo "Подключение к устройству $OBD_MAC на порт $OBD_PORT..."
            rfcomm bind $RFCOMM_NUM $OBD_MAC 1 2>/dev/null || {
                echo "Не удалось создать RFCOMM порт. Убедитесь что:"
                echo "1. Устройство включено и находится в зоне действия"
                echo "2. Устройство уже сопряжено с системой"
                echo "3. MAC адрес указан правильно"
            }
        else
            echo "Предупреждение: OBD_PORT указан как $OBD_PORT, но OBD_MAC не задан."
            echo "RFCOMM порт должен быть создан вручную на хосте перед запуском контейнера."
        fi
    else
        echo "Порт $OBD_PORT уже существует."
    fi
else
    echo "OBD_PORT не указан или не является RFCOMM портом. Пропускаем инициализацию Bluetooth."
fi

# Запускаем основной скрипт
exec "$@"

