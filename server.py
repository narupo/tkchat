import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import socket
import threading
import time


# ここのポート番号はサーバーとクライアントで同じものを使用する
# サーバーとクライアントで使用するポート番号が違うと接続エラーになる
MESSAGE_PORT = 1234
BROADCAST_PORT = 2234


class Server(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TkChat Server')

        # スクロールバー付きのテキストエリア
        self.text = ScrolledText(self)
        self.text.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        # ソケットの初期化
        self.init_recv_worker_sock()
        self.init_broadcast_worker_sock()

        # これにブロードキャスト先のソケットが保存される
        self.broadcast_socks = []

        # メッセージ受信用スレッド
        self.recv_worker_thread = threading.Thread(target=self.recv_worker, daemon=True)
        self.recv_worker_thread.start()

        # ブロードキャスト用スレッド
        self.broadcast_worker_thread = threading.Thread(target=self.broadcast_worker, daemon=True)
        self.broadcast_worker_thread.start()

    def log(self, msg):
        self.text.insert(tk.END, msg)  # 末尾に挿入
        self.text.see(tk.END)  # 末尾を見る

    def init_recv_worker_sock(self):
        # TCPソケットを作る
        self.recv_worker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # ソケットにアドレスを割り当てる
        self.recv_worker_sock.bind((socket.gethostname(), MESSAGE_PORT))

        # ソケットを接続待ちソケット（passive socket）にする
        self.recv_worker_sock.listen()
        self.log('receive worker socket is ready\n')

    def init_broadcast_worker_sock(self):
        self.broadcast_worker_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broadcast_worker_sock.bind((socket.gethostname(), BROADCAST_PORT))
        self.broadcast_worker_sock.listen()
        self.log('broadcast worker socket is ready\n')

    def recv_worker(self):
        # メッセージ受信用
        # クライアントから接続を受け付ける

        while True:
            time.sleep(1)

            # 接続を受付けてソケットを作成する
            self.log('recv: accept...\n')
            client_sock, addr = self.recv_worker_sock.accept()
            client_sock.settimeout(10)  # タイムアウト設定

            # 接続されたソケットを渡してワーカースレッドを起動
            th = threading.Thread(
                target=self.recv_client_worker,
                args=(client_sock, ),
                daemon=True,
            )
            th.start()
            self.log('accept new client socket for receive\n')

    def broadcast_worker(self):
        # ブロードキャスト用
        # クライアントから接続を受け付ける

        while True:
            time.sleep(1)

            self.log('broadcast: accept...\n')
            client_sock, addr = self.broadcast_worker_sock.accept()

            # ブロードキャスト用のタイムアウトは短めに設定
            # 長くブロックすると接続切れのソケットがあった場合に
            # ブロードキャストが途中で止まる場合がある
            client_sock.settimeout(3) 

            # 接続してきたクライアントのソケットをリストに追加する
            # このリストを参照してブロードキャストを行う
            self.broadcast_socks.append(client_sock)

            self.log('accept new client socket for broadcast\n')

    def recv_client_worker(self, client_sock):
        # メッセージ受信用
        # 接続済みのクライアントとのソケットを使ってメッセージを受信する

        while True:
            time.sleep(1)

            # 1024バイトまでデータを受信する
            try:
                msg = client_sock.recv(1024)
            except ConnectionResetError:
                # 接続が切れた
                self.remove_broadcast_socket(client_sock)
                break
            except socket.timeout:
                # タイムアウト
                continue

            msg = msg.decode()  # バイト列を文字列に変換
            self.log(f'msg: {msg}\n')

            # 各クライアントへ受信したメッセージをブロードキャスト
            self.broadcast(msg)

    def remove_broadcast_socket(self, sock):
        # sockをbroadcast_socksから除外する
        self.broadcast_socks = list(
            filter(lambda s: id(s) != id(sock), self.broadcast_socks)
        )

    def broadcast(self, msg):
        # メッセージを各クライアントへブロードキャストする
        msg = msg.encode()

        for sock in self.broadcast_socks:
            try:
                sock.send(msg)
            except (ConnectionResetError, socket.timeout):
                continue

        self.log('done broadcast message\n')


if __name__ == '__main__':
    server = Server()
    server.mainloop()
