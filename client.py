import tkinter as tk
from tkinter import ttk
import socket
import threading
import time


MESSAGE_PORT = 1234
BROADCAST_PORT = 2234


class Client(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('TkChat Client')

        self.text = tk.Text(self)
        self.text.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.msg_row = tk.Frame(self)
        self.msg_row.pack(side=tk.TOP, expand=True, fill=tk.X)

        self.msg = ttk.Entry(self.msg_row)
        self.msg.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.send_msg_btn = ttk.Button(
            self.msg_row,
            text='Send',
            command=self.send_msg,
        )
        self.send_msg_btn.pack(side=tk.LEFT)

        self.init_send_sock()
        self.init_broadcast_sock()

        self.broadcast_worker_thread = threading.Thread(target=self.broadcast_worker, daemon=True)
        self.broadcast_worker_thread.start()

    def init_send_sock(self):
        self.send_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.send_sock.connect((socket.gethostname(), MESSAGE_PORT))
        self.text.insert('1.0', 'send socket connected\n')

    def init_broadcast_sock(self):
        self.broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.broadcast_sock.connect((socket.gethostname(), BROADCAST_PORT))
        self.text.insert('1.0', 'broadcast socket connected\n')

    def send_msg(self):
        if not self.send_sock:
            return

        msg = self.msg.get()
        msg = msg.encode()
        self.send_sock.send(msg)

    def broadcast_worker(self):
        while True:
            time.sleep(1)

            data = self.broadcast_sock.recv(1024)
            data = data.decode()
            self.text.insert('1.0', f'{data}\n')


if __name__ == '__main__':
    client = Client()
    client.mainloop()
    