import socket
from threading import Thread, Lock
from client_handler import ClientHandler
from db_manager import DBManger
from tensorflow import keras


class Server:
    __SERVER_INFO = (socket.gethostbyname(socket.gethostname()), 2508)
    __MAX_CLIENTS = 2

    def __init__(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(self.__SERVER_INFO)
            print(f"server ip - {self.__SERVER_INFO[0]}, server port - {self.__SERVER_INFO[1]}")
            print("jsut binded !")
            server.listen()
            print("i have an ear problem, but i can still listen :)")

            self.__should_listen = True
            self.__receiver = Thread(target=self.__receive_clients, args=[])
            self.__threads = []
            self.__unhandled_clients = []
            self.__server = server
            self.__model = keras.models.load_model("model")

            self.__db_manager = (DBManger(), Lock())
            self.__model_lock = Lock()
            self.__run()

    def __del__(self) -> None:
        self.__should_listen = False

    def __run(self) -> None:
        self.__receiver.start()

        try:
            while True:
                self.__threads = [t for t in self.__threads if t.is_alive()]

                if len(self.__threads) <= self.__MAX_CLIENTS and len(self.__unhandled_clients) != 0:
                    print("handling a new client so exciting ^-^")
                    self.__create_thread(self.__unhandled_clients.pop(0))
        except KeyboardInterrupt:
            pass

    def __receive_clients(self) -> None:
        while self.__should_listen:
            try:
                client, addr = self.__server.accept()
                print("oh new client yee pee kay yay !")
                self.__unhandled_clients.append(client)
            except OSError:
                pass

    def __create_thread(self, client) -> None:
        thread = Thread(target=ClientHandler, args=(client, self.__db_manager, self.__model_lock, self.__model))
        self.__threads.append(thread)
        thread.start()
