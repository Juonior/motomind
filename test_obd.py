#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подключения к OBD адаптеру
"""
import sys
import time
import signal
from config import settings
import obd

# Флаг для корректного завершения
running = True

def signal_handler(sig, frame):
    """Обработчик сигнала для корректного завершения"""
    global running
    print("\n\nОстановка теста...")
    running = False
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def test_obd_connection():
    """Тест подключения к OBD"""
    print("=" * 60)
    print("Тест подключения к OBD адаптеру")
    print("=" * 60)
    print(f"OBD_PORT: {settings.OBD_PORT}")
    print(f"OBD_PROTOCOL: {settings.OBD_PROTOCOL or 'auto'}")
    print()
    
    # Проверка доступных портов
    print("1. Поиск доступных последовательных портов...")
    try:
        ports = obd.scan_serial()
        if ports:
            print(f"   Найдено портов: {ports}")
        else:
            print("   Порт не найден автоматически")
    except Exception as e:
        print(f"   Ошибка при сканировании: {e}")
    print()
    
    # Определение порта для подключения
    port = settings.OBD_PORT
    if not port:
        print("2. OBD_PORT не указан в настройках!")
        print("   Попытка автоопределения...")
        try:
            ports = obd.scan_serial()
            if ports:
                port = ports[0]
                print(f"   Используется порт: {port}")
            else:
                print("   ❌ Порт не найден!")
                return False
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
            return False
    else:
        print(f"2. Используется порт из настроек: {port}")
    
    # Проверка существования порта
    import os
    if not os.path.exists(port):
        print(f"   ❌ Порт {port} не существует!")
        print(f"   Проверьте, что RFCOMM порт создан:")
        print(f"   sudo rfcomm bind 0 <MAC_ADDRESS> 1")
        return False
    else:
        print(f"   ✅ Порт {port} существует")
    print()
    
    # Подключение к OBD
    print("3. Подключение к OBD адаптеру...")
    print("   (это может занять до 30 секунд)")
    
    connection = None
    try:
        start_time = time.time()
        
        if settings.OBD_PROTOCOL:
            print(f"   Используется протокол: {settings.OBD_PROTOCOL}")
            connection = obd.OBD(port, protocol=settings.OBD_PROTOCOL, timeout=30)
        else:
            print("   Автоопределение протокола...")
            connection = obd.OBD(port, timeout=30)
        
        elapsed = time.time() - start_time
        print(f"   Подключение заняло: {elapsed:.2f} секунд")
        print()
        
        # Проверка статуса
        print("4. Проверка статуса подключения...")
        status = connection.status
        print(f"   Статус: {status}")
        
        status_messages = {
            obd.OBDStatus.CAR_CONNECTED: "✅ Автомобиль подключен",
            obd.OBDStatus.ELM_CONNECTED: "⚠️ ELM адаптер подключен, но автомобиль не обнаружен",
            obd.OBDStatus.NOT_CONNECTED: "❌ Не подключено",
        }
        
        status_msg = status_messages.get(status, f"❓ Неизвестный статус: {status}")
        print(f"   {status_msg}")
        print()
        
        if status == obd.OBDStatus.CAR_CONNECTED:
            print("5. Тест чтения данных...")
            
            # Тест RPM
            try:
                print("   Чтение RPM...", end=" ", flush=True)
                response = connection.query(obd.commands.RPM, timeout=5)
                if response.value:
                    print(f"✅ {response.value.magnitude:.0f} об/мин")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест скорости
            try:
                print("   Чтение скорости...", end=" ", flush=True)
                response = connection.query(obd.commands.SPEED, timeout=5)
                if response.value:
                    print(f"✅ {response.value.magnitude:.0f} км/ч")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест температуры
            try:
                print("   Чтение температуры охлаждающей жидкости...", end=" ", flush=True)
                response = connection.query(obd.commands.COOLANT_TEMP, timeout=5)
                if response.value:
                    print(f"✅ {response.value.magnitude:.1f}°C")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            print()
            print("6. Информация об адаптере:")
            try:
                print(f"   Версия ELM: {connection.query(obd.commands.ELM_VERSION).value}")
                print(f"   Протокол: {connection.protocol_name()}")
            except:
                pass
            
            print()
            print("=" * 60)
            print("✅ Тест успешно завершен!")
            print("=" * 60)
            return True
        else:
            print()
            print("=" * 60)
            print("⚠️ Подключение установлено, но автомобиль не обнаружен")
            print("   Убедитесь, что:")
            print("   - Зажигание включено")
            print("   - OBD адаптер правильно подключен к автомобилю")
            print("=" * 60)
            return False
            
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        return False
    except Exception as e:
        print(f"\n   ❌ Ошибка подключения: {e}")
        print()
        print("Возможные причины:")
        print("  - Неправильный порт")
        print("  - Устройство не является OBD адаптером")
        print("  - Адаптер не подключен к автомобилю")
        print("  - Зажигание выключено")
        return False
    finally:
        if connection:
            try:
                connection.close()
                print("\nСоединение закрыто")
            except:
                pass

if __name__ == "__main__":
    try:
        success = test_obd_connection()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

