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
        # status может быть как свойством, так и методом в зависимости от версии библиотеки
        try:
            if callable(connection.status):
                status = connection.status()
            else:
                status = connection.status
        except:
            # Если не получается получить статус, пробуем читать данные
            status = None
        
        print(f"   Статус: {status}")
        
        status_messages = {
            obd.OBDStatus.CAR_CONNECTED: "✅ Автомобиль подключен",
            obd.OBDStatus.ELM_CONNECTED: "⚠️ ELM адаптер подключен, но автомобиль не обнаружен",
            obd.OBDStatus.NOT_CONNECTED: "❌ Не подключено",
        }
        
        if status:
            status_msg = status_messages.get(status, f"❓ Неизвестный статус: {status}")
            print(f"   {status_msg}")
        else:
            print(f"   ⚠️ Не удалось определить статус, но попробуем читать данные")
        print()
        
        # Пробуем читать данные даже если статус не CAR_CONNECTED
        # Иногда данные доступны даже при ELM_CONNECTED
        if status == obd.OBDStatus.CAR_CONNECTED or status == obd.OBDStatus.ELM_CONNECTED or status is None:
            print("5. Тест чтения данных...")
            
            # Тест RPM
            try:
                print("   Чтение RPM...", end=" ", flush=True)
                response = connection.query(obd.commands.RPM)
                if response.value:
                    print(f"✅ {response.value.magnitude:.0f} об/мин")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест скорости
            try:
                print("   Чтение скорости...", end=" ", flush=True)
                response = connection.query(obd.commands.SPEED)
                # Проверяем наличие значения (может быть 0, что тоже валидно)
                if response.value is not None:
                    try:
                        speed = float(response.value.magnitude)
                        if speed >= 0:
                            print(f"✅ {speed:.0f} км/ч")
                        else:
                            print(f"❌ Некорректное значение: {speed}")
                    except (AttributeError, ValueError, TypeError) as e:
                        print(f"❌ Ошибка преобразования: {e}")
                        print(f"      Тип response.value: {type(response.value)}")
                        print(f"      response.value: {response.value}")
                else:
                    print("❌ Нет данных (response.value is None)")
                    # Дополнительная диагностика
                    print(f"      response: {response}")
                    print(f"      response.is_null(): {response.is_null()}")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                import traceback
                traceback.print_exc()
            
            # Тест температуры охлаждающей жидкости
            try:
                print("   Чтение температуры охлаждающей жидкости...", end=" ", flush=True)
                response = connection.query(obd.commands.COOLANT_TEMP)
                if response.value is not None:
                    try:
                        print(f"✅ {response.value.magnitude:.1f}°C")
                    except (AttributeError, ValueError) as e:
                        print(f"❌ Ошибка преобразования: {e}")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест температуры впускного воздуха
            try:
                print("   Чтение температуры впускного воздуха...", end=" ", flush=True)
                response = connection.query(obd.commands.INTAKE_TEMP)
                if response.value is not None:
                    try:
                        print(f"✅ {response.value.magnitude:.1f}°C")
                    except (AttributeError, ValueError) as e:
                        print(f"❌ Ошибка преобразования: {e}")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест уровня топлива
            try:
                print("   Чтение уровня топлива...", end=" ", flush=True)
                # Подавляем предупреждения библиотеки obd
                import logging
                obd_logger = logging.getLogger('obd.obd')
                old_level = obd_logger.level
                obd_logger.setLevel(logging.ERROR)  # Показываем только ошибки, не предупреждения
                
                try:
                    response = connection.query(obd.commands.FUEL_LEVEL)
                    obd_logger.setLevel(old_level)  # Восстанавливаем уровень
                    
                    if response.value is not None:
                        try:
                            fuel_level = float(response.value.magnitude)
                            if 0 <= fuel_level <= 100:
                                print(f"✅ {fuel_level:.1f}%")
                            else:
                                print(f"❌ Некорректное значение: {fuel_level}")
                        except (AttributeError, ValueError, TypeError) as e:
                            print(f"❌ Ошибка преобразования: {e}")
                    else:
                        # Если value is None, команда скорее всего не поддерживается
                        print("⚠️ Команда не поддерживается автомобилем")
                except Exception as e:
                    obd_logger.setLevel(old_level)  # Восстанавливаем уровень
                    error_str = str(e).lower()
                    if 'not supported' in error_str or 'unsupported' in error_str:
                        print("⚠️ Команда не поддерживается автомобилем")
                    else:
                        print(f"❌ Ошибка: {e}")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест нагрузки двигателя
            try:
                print("   Чтение нагрузки двигателя...", end=" ", flush=True)
                response = connection.query(obd.commands.ENGINE_LOAD)
                if response.value:
                    print(f"✅ {response.value.magnitude:.1f}%")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест давления во впускном коллекторе
            try:
                print("   Чтение давления во впускном коллекторе...", end=" ", flush=True)
                response = connection.query(obd.commands.INTAKE_PRESSURE)
                if response.value:
                    print(f"✅ {response.value.magnitude:.1f} kPa")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест положения дроссельной заслонки
            try:
                print("   Чтение положения дроссельной заслонки...", end=" ", flush=True)
                response = connection.query(obd.commands.THROTTLE_POS)
                if response.value:
                    print(f"✅ {response.value.magnitude:.1f}%")
                else:
                    print("❌ Нет данных")
            except Exception as e:
                print(f"❌ Ошибка: {e}")
            
            # Тест кодов ошибок
            try:
                print("   Чтение кодов ошибок (DTC)...", end=" ", flush=True)
                response = connection.query(obd.commands.GET_DTC)
                if response.value:
                    errors = response.value
                    if errors:
                        print(f"✅ Найдено ошибок: {len(errors)}")
                        for code in errors[:5]:  # Показываем первые 5
                            print(f"      - {code[0]}: {code[1] if len(code) > 1 else 'Нет описания'}")
                    else:
                        print("✅ Ошибок не найдено")
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
            if status == obd.OBDStatus.CAR_CONNECTED:
                print("✅ Тест успешно завершен! Автомобиль подключен.")
            else:
                print("⚠️ Тест завершен. Данные прочитаны, но статус не CAR_CONNECTED")
                print("   Это может быть нормально, если:")
                print("   - Зажигание включено, но двигатель не запущен")
                print("   - Адаптер подключен, но автомобиль не полностью инициализирован")
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

