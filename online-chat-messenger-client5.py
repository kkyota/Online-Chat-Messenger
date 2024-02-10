import socket
import threading
import time

def create_room(tcp_sock, room_name):
    room_name_size = min(len(room_name), 1).to_bytes(1, byteorder='big')
    operation = b'1'
    state = b'0'
    operation_payload_size = b'\x01' * 29
    request_data = room_name_size + operation + state + operation_payload_size + room_name.encode('utf-8')
    print("Sending create room request:", request_data)
    tcp_sock.sendall(request_data)

    # サーバーからの応答を受け取る
    data = tcp_sock.recv(1024)
    print('Received data:', data.decode('utf-8'))

    # サーバーからの完了応答を受け取る
    completion_data = tcp_sock.recv(1024)
    print('Received completion data:', completion_data.decode('utf-8'))

def join_room(tcp_sock, room_name, username):
    # ルーム名のサイズを取得（1バイト）
    room_name_size = min(len(room_name), 1).to_bytes(1, byteorder='big')
    # 操作コードを示す'2'を追加（1バイト）
    operation = b'2'
    # Stateを示す'0'を追加（1バイト）
    state = b'0'
    # ユーザー名のサイズを取得（1バイト）
    username_size = min(len(username), 255).to_bytes(1, byteorder='big')
    # OperationPayloadSizeを示す29バイトの空白データ
    operation_payload_size = b'\x00' * 29
    # ルーム名、操作コード、State、OperationPayloadSize、ユーザー名を結合してデータを構築
    request_data = room_name_size + operation + state + operation_payload_size + room_name.encode('utf-8') + username_size + username.encode('utf-8')
    print("Sending join room request:", request_data)  # 追加
    # サーバーにデータを送信
    tcp_sock.sendall(request_data)

    # サーバーからの応答を受け取る
    data = tcp_sock.recv(1024)
    print('Received data:', data.decode('utf-8'))

    # サーバーからの完了応答を受け取る
    completion_data = tcp_sock.recv(1024)
    print('Received completion data:', completion_data.decode('utf-8'))

def receive_messages(sock):
    while True:
        data, server = sock.recvfrom(4096)
        received_message = data.decode('utf-8')
        print('\nreceived {!r}'.format(received_message))
        print("Type your message: ", end='', flush=True)  # 新しいメッセージを入力するためのプロンプトを表示

def send_active_signal(sock):
    while True:
        if not sock._closed:  # ソケットが閉じられていない場合にのみ送信
            # アクティブであることを示すメッセージをサーバーに送信
            active_message = "I'm active!"
            sock.sendto(active_message.encode('utf-8'), (server_address, server_udp_port))
        time.sleep(10)  # 10秒ごとにメッセージを送信


server_address = input("Type in the server's address to connect to: ")
server_udp_port = 9001
server_tcp_port = 9002

# ユーザー名の入力
username = input("Enter your username: ")

# AF_INETを使用し、UDPソケットを作成
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# AF_INETを使用し、TCPソケットを作成
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

address = ''
port = 0

# 空の文字列も0.0.0.0として使用できます。
udp_sock.bind((address, 0))
tcp_sock.connect((server_address, server_tcp_port))  # サーバーに接続

receive_thread = threading.Thread(target=receive_messages, args=(udp_sock,))
receive_thread.start()

# クライアントがサーバーにメッセージを送信するためのスレッドを開始
active_signal_thread = threading.Thread(target=send_active_signal, args=(udp_sock,))
active_signal_thread.start()

try:
    while True:
        print("Choose an action:")
        print("1. Create a chat room")
        print("2. Join a chat room")
        action = input("Enter your choice (1 or 2): ")

        if action == "1":
            room_name = input("Enter the name for the new chat room: ")
            create_room(tcp_sock, room_name)
        elif action == "2":
            room_name = input("Enter the name of the chat room to join: ")
            username = input("Enter your username: ")
            join_room(tcp_sock, room_name, username)
        else:
            print("Invalid choice. Please enter '1' or '2'.")

except KeyboardInterrupt:
    pass
finally:
    print('closing socket')
    # ソケットを閉じる
    tcp_sock.close()

try:
    # usernamelenの計算
    usernamelen = min(len(username), 255)
    # ユーザー名をバイト列にエンコード
    encoded_username = username.encode('utf-8')
    
    while True:
        print("Type your message: ", end='', flush=True)  # メッセージの入力プロンプト
        # usernamelenを先頭に付与してメッセージを構築
        message = bytes([usernamelen]) + encoded_username + input().encode('utf-8')

        if len(message) > 4096:
            message = message[:4096]
            print("Message is too long. Please keep it within 4096 bytes.")
            # エラー処理または入力を再度促す処理を追加することもできます
            # 入力を再度促す
            new_input = input("Type your message again: ")
            # 新しい入力を含めてメッセージを構築
            message = bytes([usernamelen]) + encoded_username + new_input.encode('utf-8')

        # print('sending {!r}'.format(message))
        # サーバへのデータ送信
        sent = udp_sock.sendto(message, (server_address, server_udp_port))
        # print('Send {} bytes'.format(sent))

        # # 応答を受信
        # print('waiting to receive')
        # data, server = sock.recvfrom(4096)
        # received_message = data.decode('utf-8')  # 受信したバイト列を文字列にデコード
        # print('received {!r}'.format(received_message))

        # サーバーにデータを送信
        message = 'Hello, server!'
        tcp_sock.sendall(message.encode('utf-8'))

        # サーバーからのデータを受信
        data = tcp_sock.recv(1024)  # 1024バイトのデータを受信
        print('Received data:', data.decode('utf-8'))

finally:
    print('closing socket')
    # ソケットを閉じる
    udp_sock.close()