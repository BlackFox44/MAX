import socket
import threading
import json
import time
from datetime import datetime


class MaxMessengerServer:
    def __init__(self, host='10.192.69.112', port=8888):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # {client_socket: username}
        self.rooms = {'general': []}  # {room_name: [client_sockets]}

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"🚀 Сервер Макс запущен на {self.host}:{self.port}")
            print("📝 Ожидание подключений...")

            while True:
                client_socket, client_address = self.server_socket.accept()
                print(f"🔌 Новое подключение от {client_address}")

                # Запускаем поток для обработки клиента
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()

        except Exception as e:
            print(f"❌ Ошибка сервера: {e}")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        """Обработка сообщений от клиента"""
        try:
            # Получаем имя пользователя
            username_data = client_socket.recv(1024).decode('utf-8')
            username_info = json.loads(username_data)
            username = username_info.get('username', f'User_{client_address[1]}')

            # Регистрируем клиента
            self.clients[client_socket] = username
            self.rooms['general'].append(client_socket)

            # Отправляем подтверждение
            welcome_msg = {
                'type': 'system',
                'message': f'👋 Добро пожаловать, {username}!',
                'time': datetime.now().strftime('%H:%M:%S')
            }
            client_socket.send(json.dumps(welcome_msg).encode('utf-8'))

            # Уведомляем всех о новом пользователе
            self.broadcast({
                'type': 'system',
                'message': f'🟢 {username} присоединился к чату',
                'time': datetime.now().strftime('%H:%M:%S')
            }, exclude=client_socket)

            print(f"✅ Пользователь {username} подключился")

            # Обрабатываем сообщения от клиента
            while True:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break

                    message_data = json.loads(data)

                    # Обрабатываем команды
                    if message_data.get('type') == 'command':
                        self.handle_command(client_socket, message_data)
                    else:
                        # Обычное сообщение
                        self.broadcast({
                            'type': 'message',
                            'username': username,
                            'message': message_data.get('message', ''),
                            'time': datetime.now().strftime('%H:%M:%S')
                        })

                except json.JSONDecodeError:
                    print(f"⚠️ Ошибка декодирования сообщения от {username}")
                except Exception as e:
                    print(f"⚠️ Ошибка при получении сообщения: {e}")
                    break

        except Exception as e:
            print(f"⚠️ Ошибка обработки клиента {client_address}: {e}")
        finally:
            self.remove_client(client_socket)

    def handle_command(self, client_socket, command_data):
        """Обработка команд от клиента"""
        command = command_data.get('command', '')
        username = self.clients.get(client_socket, 'Unknown')

        if command == '/users':
            # Список пользователей
            users_list = list(self.clients.values())
            response = {
                'type': 'system',
                'message': f'👥 Пользователи онлайн: {", ".join(users_list)}',
                'time': datetime.now().strftime('%H:%M:%S')
            }
            client_socket.send(json.dumps(response).encode('utf-8'))

        elif command == '/help':
            help_text = """
📋 Доступные команды:
/users - список пользователей онлайн
/help - показать это сообщение
/clear - очистить чат
/private @user сообщение - личное сообщение
            """
            response = {
                'type': 'system',
                'message': help_text,
                'time': datetime.now().strftime('%H:%M:%S')
            }
            client_socket.send(json.dumps(response).encode('utf-8'))

    def broadcast(self, message, exclude=None):
        """Отправка сообщения всем клиентам"""
        message_json = json.dumps(message).encode('utf-8')

        for client_socket in list(self.rooms['general']):
            if exclude and client_socket == exclude:
                continue

            try:
                client_socket.send(message_json)
            except:
                # Если не удалось отправить, удаляем клиента
                self.remove_client(client_socket)

    def remove_client(self, client_socket):
        """Удаление отключившегося клиента"""
        if client_socket in self.clients:
            username = self.clients[client_socket]
            del self.clients[client_socket]

            # Удаляем из всех комнат
            for room in self.rooms.values():
                if client_socket in room:
                    room.remove(client_socket)

            # Уведомляем остальных
            self.broadcast({
                'type': 'system',
                'message': f'🔴 {username} покинул чат',
                'time': datetime.now().strftime('%H:%M:%S')
            })

            print(f"👋 Пользователь {username} отключился")

        try:
            client_socket.close()
        except:
            pass


if __name__ == "__main__":
    server = MaxMessengerServer()
    server.start()