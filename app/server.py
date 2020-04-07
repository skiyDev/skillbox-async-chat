import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport
    last_received_message: str

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        decoded = data.decode().strip()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").strip()
                if login in self.server.users:
                    self.transport.write(f"Логин {login} занят, попробуйте другой!\n".encode('utf-8'))
                    # отключение пользователя от чата
                    self.transport.close()
                else:
                    self.login = login
                    self.server.users.add(login)
                    self.transport.write(
                        f"Привет, {self.login}!\n".encode('utf-8')
                    )
                    self.send_history()
            else:
                self.transport.write("Неправильный логин\n".encode('utf-8'))

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        if self.login is not None:
            self.server.users.remove(self.login)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"\r{self.login}: {content}\n"
        if len(self.server.history) == 10:
            self.server.history.pop(0)
        self.server.history.append(message)

        for user in self.server.clients:
            if user.login is not None:
                user.transport.write(message.encode('utf-8'))
            # else:
            #     user.transport.write(f"{}".encode('utf-8'))

    def send_history(self):
        history_len = len(self.server.history)
        if history_len > 0:
            history_message = ''.join(self.server.history)
            self.transport.write(f"\rПоследние {history_len} сообщений\n{history_message}".encode('utf-8'))


class Server:
    clients: list
    users: set
    history: list

    def __init__(self):
        self.clients = []
        self.users = set()
        self.history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
