import socket
import threading
import json
import sys
import os
from datetime import datetime


class MaxMessengerClient:
    def __init__(self, host='10.192.69.112', port=8888):  # Изменен хост по умолчанию
        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.running = True
        self.input_buffer = ""  # Буфер для текущего ввода

    def connect(self):
        try:
            self.client_socket.connect((self.host, self.port))

            # Запрашиваем имя пользователя
            self.username = input("👋 Введите ваше имя: ").strip()
            if not self.username:
                self.username = f"User_{os.getpid()}"

            # Отправляем имя на сервер
            username_data = json.dumps({'username': self.username})
            self.client_socket.send(username_data.encode('utf-8'))

            # Запускаем поток для получения сообщений
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()

            print(f"✅ Подключено к серверу Макс! ({self.host}:{self.port})")
            print("💬 Введите /help для списка команд")
            print("-" * 50)

            # Отправляем сообщения
            self.send_messages()

        except ConnectionRefusedError:
            print(f"❌ Не удалось подключиться к серверу {self.host}:{self.port}. Убедитесь, что сервер запущен.")
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
        finally:
            self.client_socket.close()

    def receive_messages(self):
        """Получение сообщений от сервера"""
        while self.running:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                message_data = json.loads(data)
                self.display_message(message_data)

            except json.JSONDecodeError:
                print("⚠️ Получено поврежденное сообщение")
            except Exception as e:
                if self.running:
                    print(f"⚠️ Ошибка при получении сообщения: {e}")
                break

    def display_message(self, message_data):
        """Отображение сообщения в консоли без ломания строки ввода"""
        msg_type = message_data.get('type', 'message')
        msg_time = message_data.get('time', '')

        # Сохраняем текущий ввод
        current_input = self.input_buffer

        # Очищаем текущую строку ввода
        sys.stdout.write('\r' + ' ' * (len(current_input) + 4) + '\r')
        sys.stdout.flush()

        # Выводим полученное сообщение
        if msg_type == 'system':
            print(f"\r📢 [{msg_time}] {message_data['message']}")
        else:
            username = message_data.get('username', 'Unknown')
            message = message_data.get('message', '')
            print(f"\r💬 [{msg_time}] {username}: {message}")

        # Возвращаем приглашение к вводу и сохраненный ввод
        sys.stdout.write(f">>> {current_input}")
        sys.stdout.flush()

    def send_messages(self):
        """Отправка сообщений на сервер"""
        try:
            while self.running:
                # Используем sys.stdin.readline для лучшего контроля
                try:
                    # Очищаем буфер перед чтением
                    sys.stdout.write(">>> ")
                    sys.stdout.flush()

                    # Читаем ввод с обработкой backspace
                    message = ""
                    while True:
                        char = sys.stdin.read(1)
                        if char == '\n':
                            break
                        elif ord(char) == 127 or ord(char) == 8:  # Backspace
                            if message:
                                message = message[:-1]
                                sys.stdout.write('\b \b')
                                sys.stdout.flush()
                        else:
                            message += char
                            sys.stdout.write(char)
                            sys.stdout.flush()

                    # Обновляем буфер ввода
                    self.input_buffer = message.strip()

                    if not self.input_buffer:
                        continue

                    # Проверяем команды
                    if self.input_buffer.startswith('/'):
                        if self.input_buffer in ['/exit', '/quit']:
                            self.running = False
                            break
                        elif self.input_buffer == '/clear':
                            self.clear_screen()
                            continue
                        else:
                            # Отправляем команду на сервер
                            command_data = {
                                'type': 'command',
                                'command': self.input_buffer
                            }
                            self.client_socket.send(json.dumps(command_data).encode('utf-8'))
                    else:
                        # Обычное сообщение
                        message_data = {
                            'type': 'message',
                            'message': self.input_buffer
                        }
                        self.client_socket.send(json.dumps(message_data).encode('utf-8'))

                    # Очищаем буфер после отправки
                    self.input_buffer = ""

                except EOFError:
                    break
                except Exception as e:
                    print(f"❌ Ошибка при отправке: {e}")
                    break

        except KeyboardInterrupt:
            print("\n👋 До свидания!")
        finally:
            self.running = False

    def clear_screen(self):
        """Очистка экрана"""
        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    # Очищаем экран
    os.system('cls' if os.name == 'nt' else 'clear')

    print("╔════════════════════════════════╗")
    print("║      Макс Мессенджер v1.1      ║")
    print("╚════════════════════════════════╝")

    # Сразу предлагаем ввести адрес с дефолтным значением
    host_input = input(f"🌐 Сервер (Enter для 10.192.69.112): ").strip()
    port_input = input(f"🔌 Порт (Enter для 8888): ").strip()

    # Если пользователь ничего не ввел (просто нажал Enter), используем значения по умолчанию
    host = host_input if host_input else '10.192.69.112'
    port = int(port_input) if port_input else 8888

    print(f"✅ Подключаемся к {host}:{port}...")

    client = MaxMessengerClient(host, port)
    client.connect()