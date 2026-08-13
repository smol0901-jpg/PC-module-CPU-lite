#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PC Health Guardian - Легковесный модуль для защиты ПК от перегрузки
Версия: 1.0
Оптимизировано для слабых ПК (Intel Celeron N4120, 8GB RAM)
"""

import os
import sys
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import psutil

# winreg доступен только на Windows
try:
    import winreg
    WINDOWS_PLATFORM = True
except ImportError:
    WINDOWS_PLATFORM = False

# Константы
MAX_CPU_THRESHOLD = 98.0  # Максимальная нагрузка CPU %
LEARN_THRESHOLD = 95.0    # Порог обучения %
CHECK_INTERVAL = 2.0      # Интервал проверки (секунды)
DATA_DIR = Path(os.path.expanduser("~")) / "PCHealthGuardian"
RULES_FILE = DATA_DIR / "rules.json"
LOGS_FILE = DATA_DIR / "logs.json"
LEARNED_FILE = DATA_DIR / "learned.json"
CONFIG_FILE = DATA_DIR / "config.json"

# Системные процессы, которые нельзя завершать
SYSTEM_PROCESSES = {
    'system', 'idle', 'smss.exe', 'csrss.exe', 'wininit.exe',
    'services.exe', 'lsass.exe', 'svchost.exe', 'explorer.exe',
    'winlogon.exe', 'dwm.exe', 'taskmgr.exe', 'registry',
    'memory compression', 'interrupts', 'ntoskrnl.exe'
}

class PCHealthGuardian:
    def __init__(self):
        self.running = True
        self.antivirus_enabled = True
        self.rules = {}
        self.logs = []
        self.learned_processes = {}
        self.pending_actions = {}
        self.confirmed_protocols = {}
        
        # Инициализация директории и файлов
        DATA_DIR.mkdir(exist_ok=True)
        self.load_data()
        
    def load_data(self):
        """Загрузка данных из файлов"""
        try:
            if RULES_FILE.exists():
                with open(RULES_FILE, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
        except Exception as e:
            self.log_action("ERROR", f"Ошибка загрузки правил: {e}")
            
        try:
            if LOGS_FILE.exists():
                with open(LOGS_FILE, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
        except Exception as e:
            self.logs = []
            
        try:
            if LEARNED_FILE.exists():
                with open(LEARNED_FILE, 'r', encoding='utf-8') as f:
                    self.learned_processes = json.load(f)
        except Exception as e:
            self.learned_processes = {}
            
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.antivirus_enabled = config.get('antivirus_enabled', True)
        except Exception as e:
            pass
            
    def save_data(self):
        """Сохранение данных в файлы"""
        try:
            with open(RULES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=2, ensure_ascii=False)
            with open(LOGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.logs[-1000:], f, indent=2, ensure_ascii=False)  # Храним последние 1000 записей
            with open(LEARNED_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.learned_processes, f, indent=2, ensure_ascii=False)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({'antivirus_enabled': self.antivirus_enabled}, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")
    
    def log_action(self, action_type, message, process_name=None):
        """Логирование действий"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': action_type,
            'message': message,
            'process': process_name
        }
        self.logs.append(entry)
        if len(self.logs) > 1000:
            self.logs = self.logs[-1000:]
        self.save_data()
        
    def get_cpu_usage(self):
        """Получение общей нагрузки CPU"""
        return psutil.cpu_percent(interval=1)
    
    def get_process_info(self, proc):
        """Получение информации о процессе"""
        try:
            return {
                'pid': proc.pid,
                'name': proc.name(),
                'cpu_percent': proc.cpu_percent(interval=0.1),
                'memory_percent': proc.memory_percent(),
                'status': proc.status()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None
    
    def is_system_critical(self, process_name):
        """Проверка, является ли процесс системно-критическим"""
        name_lower = process_name.lower()
        return any(sys_proc.lower() in name_lower for sys_proc in SYSTEM_PROCESSES)
    
    def check_antivirus_threat(self, process_name):
        """Проверка процесса на наличие угроз (упрощенный антивирус)"""
        if not self.antivirus_enabled:
            return False
        
        suspicious_patterns = ['miner', 'trojan', 'ransom', 'keylogger']
        name_lower = process_name.lower()
        
        # Простая эвристика
        for pattern in suspicious_patterns:
            if pattern in name_lower:
                self.log_action("ANTIVIRUS", f"Обнаружен подозрительный процесс: {process_name}", process_name)
                return True
        return False
    
    def ask_confirmation(self, action, process_name, reason):
        """Запрос подтверждения у пользователя"""
        protocol_key = f"{action}:{process_name}"
        
        # Проверяем, есть ли уже подтвержденный протокол
        if protocol_key in self.confirmed_protocols:
            self.log_action("AUTO", f"Автоматическое действие по протоколу: {action} для {process_name}", process_name)
            return True
        
        # В реальном приложении здесь было бы GUI-окно
        # Для консольной версии используем input
        print(f"\n{'='*60}")
        print(f"ТРЕБУЕТСЯ ПОДТВЕРЖДЕНИЕ")
        print(f"Действие: {action}")
        print(f"Процесс: {process_name}")
        print(f"Причина: {reason}")
        print(f"{'='*60}")
        print("1. Выполнить сейчас")
        print("2. Выполнить всегда для этого процесса")
        print("3. Отменить")
        print("4. Отложить решение")
        
        choice = input("\nВаш выбор (1-4): ").strip()
        
        if choice == '1':
            self.log_action("CONFIRMED", f"Пользователь подтвердил: {action}", process_name)
            return True
        elif choice == '2':
            self.confirmed_protocols[protocol_key] = True
            self.log_action("PROTOCOL_CREATED", f"Создан протокол: {action} для {process_name}", process_name)
            return True
        elif choice == '4':
            self.pending_actions[process_name] = {'action': action, 'reason': reason}
            self.log_action("DEFERRED", f"Решение отложено: {action}", process_name)
            return False
        else:
            self.log_action("DENIED", f"Пользователь отменил: {action}", process_name)
            return False
    
    def terminate_process(self, proc, reason="Высокая нагрузка"):
        """Завершение процесса с подтверждением"""
        process_name = proc.name()
        
        if self.is_system_critical(process_name):
            self.log_action("SKIPPED", f"Системный процесс пропущен: {process_name}", process_name)
            return False
        
        if not self.ask_confirmation("TERMINATE", process_name, reason):
            return False
        
        try:
            proc.terminate()
            self.log_action("TERMINATED", f"Процесс завершен: {process_name}", process_name)
            return True
        except Exception as e:
            self.log_action("ERROR", f"Не удалось завершить процесс {process_name}: {e}", process_name)
            return False
    
    def learn_from_process(self, process_name, cpu_usage):
        """Обучение на основе поведения процессов"""
        if process_name not in self.learned_processes:
            self.learned_processes[process_name] = {
                'first_seen': datetime.now().isoformat(),
                'high_load_count': 1,
                'max_cpu': cpu_usage,
                'auto_action': None
            }
        else:
            self.learned_processes[process_name]['high_load_count'] += 1
            self.learned_processes[process_name]['max_cpu'] = max(
                self.learned_processes[process_name]['max_cpu'], 
                cpu_usage
            )
        
        # Если процесс часто создает высокую нагрузку, предлагаем авто-действие
        if self.learned_processes[process_name]['high_load_count'] >= 3:
            if self.learned_processes[process_name]['auto_action'] is None:
                print(f"\nПроцесс {process_name} часто создает высокую нагрузку.")
                action = input("Автоматически завершать при высокой нагрузке? (y/n): ").strip().lower()
                if action == 'y':
                    self.learned_processes[process_name]['auto_action'] = 'terminate'
                    self.log_action("LEARNED", f"Изучено правило для {process_name}", process_name)
        
        self.save_data()
    
    def apply_learned_rules(self, process_name, cpu_usage):
        """Применение изученных правил"""
        if process_name in self.learned_processes:
            learned = self.learned_processes[process_name]
            if learned.get('auto_action') == 'terminate' and cpu_usage > LEARN_THRESHOLD:
                if self.ask_confirmation("AUTO_TERMINATE", process_name, f"Нагрузка CPU: {cpu_usage}% (по изученному правилу)"):
                    return True
        return False
    
    def add_rule(self, rule_name, condition, action):
        """Добавление правила"""
        self.rules[rule_name] = {
            'condition': condition,
            'action': action,
            'created': datetime.now().isoformat()
        }
        self.save_data()
        self.log_action("RULE_ADDED", f"Добавлено правило: {rule_name}")
    
    def remove_rule(self, rule_name):
        """Удаление правила"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.save_data()
            self.log_action("RULE_REMOVED", f"Удалено правило: {rule_name}")
            return True
        return False
    
    def list_rules(self):
        """Список всех правил"""
        return self.rules
    
    def monitor_loop(self):
        """Основной цикл мониторинга"""
        self.log_action("STARTED", "Мониторинг запущен")
        
        while self.running:
            try:
                cpu_total = self.get_cpu_usage()
                
                # Проверка общей нагрузки
                if cpu_total > MAX_CPU_THRESHOLD:
                    self.log_action("WARNING", f"Критическая нагрузка CPU: {cpu_total}%")
                    
                    # Поиск процессов с высокой нагрузкой
                    high_load_procs = []
                    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                        try:
                            pinfo = proc.info
                            cpu_pct = pinfo.get('cpu_percent', 0) or proc.cpu_percent(interval=0.1)
                            if cpu_pct > LEARN_THRESHOLD:
                                high_load_procs.append((proc, cpu_pct))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    # Сортировка по нагрузке
                    high_load_procs.sort(key=lambda x: x[1], reverse=True)
                    
                    for proc, cpu_pct in high_load_procs[:3]:  # Топ-3 процесса
                        try:
                            process_name = proc.name()
                            
                            # Проверка изученных правил
                            if self.apply_learned_rules(process_name, cpu_pct):
                                self.terminate_process(proc, f"Нагрузка CPU: {cpu_pct}% (по правилу)")
                                time.sleep(1)
                                continue
                            
                            # Проверка на вирусы
                            if self.check_antivirus_threat(process_name):
                                if self.ask_confirmation("QUARANTINE", process_name, f"Подозрительный процесс, нагрузка: {cpu_pct}%"):
                                    self.terminate_process(proc, "Подозрительная активность")
                                    time.sleep(1)
                                    continue
                            
                            # Стандартная проверка
                            if cpu_pct > LEARN_THRESHOLD:
                                self.learn_from_process(process_name, cpu_pct)
                                
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                
                # Сохранение логов периодически
                if len(self.logs) % 10 == 0:
                    self.save_data()
                    
                time.sleep(CHECK_INTERVAL)
                
            except Exception as e:
                self.log_action("ERROR", f"Ошибка в цикле мониторинга: {e}")
                time.sleep(CHECK_INTERVAL)
    
    def stop(self):
        """Остановка мониторинга"""
        self.running = False
        self.save_data()
        self.log_action("STOPPED", "Мониторинг остановлен")


def add_to_startup():
    """Добавление программы в автозагрузку"""
    if not WINDOWS_PLATFORM:
        print("Автозагрузка доступна только на Windows")
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        script_path = os.path.abspath(sys.argv[0])
        winreg.SetValueEx(key, "PCHealthGuardian", 0, winreg.REG_SZ, f'python "{script_path}" --minimized')
        winreg.CloseKey(key)
        print("Программа добавлена в автозагрузку")
        return True
    except Exception as e:
        print(f"Ошибка добавления в автозагрузку: {e}")
        return False


def show_logs(guardian, count=20):
    """Показать последние логи"""
    print(f"\n{'='*60}")
    print("ПОСЛЕДНИЕ ДЕЙСТВИЯ")
    print(f"{'='*60}")
    for entry in guardian.logs[-count:]:
        print(f"[{entry['timestamp']}] {entry['type']}: {entry['message']}")
    print(f"{'='*60}\n")


def show_menu(guardian):
    """Показать меню управления"""
    while True:
        print("\n" + "="*60)
        print("PC HEALTH GUARDIAN - МЕНЮ УПРАВЛЕНИЯ")
        print("="*60)
        print("1. Показать статус системы")
        print("2. Просмотреть логи действий")
        print("3. Управление правилами")
        print("4. Изученные процессы")
        print("5. Настройки антивируса")
        print("6. Добавить правило вручную")
        print("7. Удалить правило")
        print("8. Выйти (мониторинг продолжится в фоне)")
        print("="*60)
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == '1':
            cpu = guardian.get_cpu_usage()
            mem = psutil.virtual_memory()
            print(f"\nCPU: {cpu}% | RAM: {mem.percent}% | Процессы: {len(psutil.pids())}")
            
        elif choice == '2':
            show_logs(guardian)
            
        elif choice == '3':
            rules = guardian.list_rules()
            if rules:
                print("\nПравила:")
                for name, rule in rules.items():
                    print(f"  - {name}: {rule['condition']} -> {rule['action']}")
            else:
                print("\nНет активных правил")
                
        elif choice == '4':
            if guardian.learned_processes:
                print("\nИзученные процессы:")
                for name, data in guardian.learned_processes.items():
                    print(f"  - {name}: загрузок={data['high_load_count']}, макс.CPU={data['max_cpu']}%, авто-действие={data.get('auto_action', 'нет')}")
            else:
                print("\nНет изученных процессов")
                
        elif choice == '5':
            status = "ВКЛЮЧЕН" if guardian.antivirus_enabled else "ВЫКЛЮЧЕН"
            print(f"\nАнтивирус: {status}")
            change = input("Изменить? (y/n): ").strip().lower()
            if change == 'y':
                guardian.antivirus_enabled = not guardian.antivirus_enabled
                guardian.save_data()
                print(f"Антивирус теперь: {'ВКЛЮЧЕН' if guardian.antivirus_enabled else 'ВЫКЛЮЧЕН'}")
                
        elif choice == '6':
            name = input("Название правила: ").strip()
            condition = input("Условие (например, cpu>90): ").strip()
            action = input("Действие (terminate/notify): ").strip()
            guardian.add_rule(name, condition, action)
            print("Правило добавлено")
            
        elif choice == '7':
            name = input("Название правила для удаления: ").strip()
            if guardian.remove_rule(name):
                print("Правило удалено")
            else:
                print("Правило не найдено")
                
        elif choice == '8':
            print("\nМониторинг продолжается в фоновом режиме.")
            break


def main():
    print("="*60)
    print("PC HEALTH GUARDIAN v1.0")
    print("Легковесный защитник вашего ПК")
    print("="*60)
    
    guardian = PCHealthGuardian()
    
    # Запуск мониторинга в отдельном потоке
    monitor_thread = threading.Thread(target=guardian.monitor_loop, daemon=True)
    monitor_thread.start()
    
    # Показ меню
    show_menu(guardian)
    
    # Ожидание завершения
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка...")
        guardian.stop()


if __name__ == "__main__":
    main()
