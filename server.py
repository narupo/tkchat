import tkinter as tk
from tkinter import ttk
import socket
import threading
import time


MESSAGE_PORT = 1234
BROADCAST_PORT = 2234


class Server(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TkChat Server')

        self.text = tk.Text(self)
        self.text.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.init_recv_worker_sock()
        self.init_broadcast_worker_sock()
        self.broadcast_socks = []

        self.recv_worker_thread = threading.Thread(target=self.recv_worker, daemon=True)
        self.recv_worker_thread.start()

        self.broadcast_worker_thread = threading.Thread(target=self.broadcast_worker, daemon=True)
        self.broadcast_worker_thread.start()

    def init_recv_worker_sock(self):
        # TCPソケットを作る
        self.recv_worker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ソケットにアドレスを割り当てる
        self.recv_worker_sock.bind((socket.gethostname(), MESSAGE_PORT))

        # ソケットを接続待ちソケット（passive socket）にする
        self.recv_worker_sock.listen()
        self.text.insert('1.0', 'receive worker socket is ready\n')

    def init_broadcast_worker_sock(self):
        self.broadcast_worker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broadcast_worker_sock.bind((socket.gethostname(), BROADCAST_PORT))
        self.broadcast_worker_sock.listen()
        self.text.insert('1.0', 'broadcast worker socket is ready\n')

    def recv_worker(self):
        while True:
            time.sleep(1)

            self.text.insert('1.0', 'recv: accept...\n')
            client_sock, addr = self.recv_worker_sock.accept()
            client_sock.settimeout(10)

            th = threading.Thread(
                target=self.recv_client_worker,
                args=(client_sock, ),
                daemon=True,
            )
            th.start()
            self.text.insert('1.0', 'accept new client socket for receive\n')

    def broadcast_worker(self):
        while True:
            time.sleep(1)

            self.text.insert('1.0', 'broadcast: accept...\n')
            client_sock, addr = self.broadcast_worker_sock.accept()
            client_sock.settimeout(3)

            # 接続してきたクライアントのソケットをリストに追加する
            self.broadcast_socks.append(client_sock)
            self.text.insert('1.0', 'accept new client socket for broadcast\n')

    def recv_client_worker(self, client_sock):
        while True:
            time.sleep(1)

            try:
                msg = client_sock.recv(1024)
            except ConnectionResetError:
                # 接続が切れた
                self.remove_broadcast_socket(client_sock)
                break
            except socket.timeout:
                continue

            msg = msg.decode()
            self.text.insert('1.0', f'msg: {msg}\n')

            # 各クライアントへメッセージをブロードキャスト
            self.broadcast(msg)

    def remove_broadcast_socket(self, sock):
        self.broadcast_socks = list(
            filter(lambda s: id(s) != id(sock), self.broadcast_socks)
        )

    def broadcast(self, msg):
        msg = msg.encode()

        for sock in self.broadcast_socks:
            try:
                sock.send(msg)
            except ConnectionResetError:
                continue

        self.text.insert('1.0', 'done broadcast message\n')


if __name__ == '__main__':
    server = Server()
    server.mainloop()
