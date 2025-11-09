import obd
import logging
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)


class OBDHandler:
    """Обработчик подключения к OBD-II адаптеру"""
    
    def __init__(self):
        self.connection: Optional[obd.OBD] = None
        self.is_connected = False
    
    def connect(self) -> bool:
        """Подключение к OBD адаптеру"""
        try:
            port = settings.OBD_PORT or obd.scan_serial()
            if not port:
                logger.error("OBD адаптер не найден")
                if settings.OBD_MAC:
                    logger.info(f"OBD_MAC указан: {settings.OBD_MAC}, но порт не найден. Проверьте, что RFCOMM порт создан.")
                return False
            
            # Логирование информации о подключении
            logger.info(f"Подключение к OBD на порту: {port}")
            if settings.OBD_MAC:
                logger.debug(f"MAC адрес адаптера: {settings.OBD_MAC}")
            if settings.OBD_PROTOCOL:
                logger.debug(f"Используется протокол: {settings.OBD_PROTOCOL}")
            
            # Если указан протокол, используем его, иначе автоопределение
            if settings.OBD_PROTOCOL:
                self.connection = obd.OBD(port, protocol=settings.OBD_PROTOCOL, timeout=30)
            else:
                self.connection = obd.OBD(port, timeout=30)
            self.is_connected = self.connection.status == obd.OBDStatus.CAR_CONNECTED
            
            if self.is_connected:
                logger.info("Успешно подключено к OBD")
            else:
                logger.warning(f"Статус подключения: {self.connection.status}")
            
            return self.is_connected
        except Exception as e:
            logger.error(f"Ошибка подключения к OBD: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Отключение от OBD адаптера"""
        if self.connection:
            try:
                self.connection.close()
                self.is_connected = False
                logger.info("Отключено от OBD")
            except Exception as e:
                logger.error(f"Ошибка отключения: {e}")
    
    def get_errors(self) -> list[Dict[str, Any]]:
        """Получение кодов ошибок (DTC - Diagnostic Trouble Codes)"""
        if not self.is_connected or not self.connection:
            return []
        
        try:
            response = self.connection.query(obd.commands.GET_DTC)
            if response.value:
                errors = []
                for code in response.value:
                    errors.append({
                        "code": code[0],
                        "description": code[1] if len(code) > 1 else "Неизвестная ошибка"
                    })
                return errors
            return []
        except Exception as e:
            logger.error(f"Ошибка получения DTC: {e}")
            return []
    
    def clear_errors(self) -> bool:
        """Очистка кодов ошибок"""
        if not self.is_connected or not self.connection:
            return False
        
        try:
            response = self.connection.query(obd.commands.CLEAR_DTC)
            return response.value is not None
        except Exception as e:
            logger.error(f"Ошибка очистки DTC: {e}")
            return False
    
    def get_temperature(self, sensor: str = "coolant") -> Optional[float]:
        """Получение температуры
        
        Args:
            sensor: Тип датчика ('coolant' - охлаждающая жидкость, 'intake' - впускной воздух)
        """
        if not self.is_connected or not self.connection:
            return None
        
        try:
            if sensor == "coolant":
                response = self.connection.query(obd.commands.COOLANT_TEMP)
            elif sensor == "intake":
                response = self.connection.query(obd.commands.INTAKE_TEMP)
            else:
                return None
            
            if response.value:
                return float(response.value.magnitude)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения температуры: {e}")
            return None
    
    def get_rpm(self) -> Optional[float]:
        """Получение оборотов двигателя (RPM)"""
        if not self.is_connected or not self.connection:
            return None
        
        try:
            response = self.connection.query(obd.commands.RPM)
            if response.value:
                return float(response.value.magnitude)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения RPM: {e}")
            return None
    
    def get_speed(self) -> Optional[float]:
        """Получение скорости (км/ч)"""
        if not self.is_connected or not self.connection:
            return None
        
        try:
            response = self.connection.query(obd.commands.SPEED)
            if response.value:
                return float(response.value.magnitude)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения скорости: {e}")
            return None
    
    def get_fuel_level(self) -> Optional[float]:
        """Получение уровня топлива (%)"""
        if not self.is_connected or not self.connection:
            return None
        
        try:
            response = self.connection.query(obd.commands.FUEL_LEVEL)
            if response.value:
                return float(response.value.magnitude)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения уровня топлива: {e}")
            return None
    
    def get_engine_load(self) -> Optional[float]:
        """Получение нагрузки двигателя (%)"""
        if not self.is_connected or not self.connection:
            return None
        
        try:
            response = self.connection.query(obd.commands.ENGINE_LOAD)
            if response.value:
                return float(response.value.magnitude)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения нагрузки двигателя: {e}")
            return None
    
    def get_all_data(self) -> Dict[str, Any]:
        """Получение всех доступных данных"""
        data = {
            "connected": self.is_connected,
            "rpm": self.get_rpm(),
            "speed": self.get_speed(),
            "coolant_temp": self.get_temperature("coolant"),
            "intake_temp": self.get_temperature("intake"),
            "fuel_level": self.get_fuel_level(),
            "engine_load": self.get_engine_load(),
            "errors": self.get_errors()
        }
        return data

