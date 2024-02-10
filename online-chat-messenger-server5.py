import socket
import json
import secrets
import string
import time

class ChatRoom:
    def __init__(self):
        self.participants = set()
        self.tokens = set()

# クライアント情報を保持する辞書
connected_clients = {}
CLIENT_TIMEOUT = 300  # クライアントのタイムアウト時間（秒） ここでは5分としています。
chat_rooms = {}

# トークン生成関数
def generate_unique_token():
    alphabet = string.ascii_letters + string.digits  # 英数字を使用してトークンを生成
    token_length = 16  # トークンの長さを設定（ここでは例として16としていますが、必要に応じて変更してください）
    return ''.join(secrets.choice(alphabet) for _ in range(token_length))  # ランダムなトークンを生成

# チャットルームを作成する関数
def create_chat_room(requested_username):
    # チャットルームの作成処理
    if requested_username not in chat_rooms:
        chat_rooms[requested_username] = ChatRoom()
        
        # トークンの生成と管理
        token = generate_unique_token()
        chat_rooms[requested_username].tokens.add(token)
        print("create chat room ok")

        # クライアント情報にルーム名とアドレスを設定
        connected_clients[tcp_address] = {'username': requested_username, 'room_name': requested_username, 'address': tcp_address}
        
        # 生成されたトークンと作成されたルーム名を返す
        return True, token, requested_username
    else:
        # 既に同じ名前のチャットルームが存在する場合は失敗として扱う
        return False, None, None

    
# チャットルームに参加する関数
def join_chat_room(requested_username, room_name, tcp_address):
    if room_name in chat_rooms:
        room = chat_rooms[room_name]
        # トークンの生成と管理
        token = generate_unique_token()
        room.tokens.add(token)
        print("Joining chat room successful")

        # クライアント情報にルーム名とアドレスを設定
        connected_clients[tcp_address] = {'username': requested_username, 'room_name': room_name, 'address': tcp_address}

        # 生成されたトークンと参加したルーム名を返す
        return True, token, room_name
    else:
        # チャットルームが存在しない場合はエラーメッセージをクライアントに送信
        error_message = "Room does not exist. Please create the room first to join."
        send_response(0, error_message, None, None)
        return False, None, None

# 新しいメッセージを受信したときに、そのクライアントのタイムスタンプを更新する関数
def update_client_timestamp(client_address):
    if client_address in connected_clients:
        connected_clients[client_address]['last_message_time'] = time.time()
    else:
        print(f"Warning: Client with address {client_address} not found in connected clients.")

# クライアントのタイムスタンプをチェックしてタイムアウトするクライアントを削除する関数
def check_client_timeouts():
    current_time = time.time()
    clients_to_remove = []
    for address, info in connected_clients.items():
        last_message_time = info.get('last_message_time', 0)
        if current_time - last_message_time > CLIENT_TIMEOUT:
            clients_to_remove.append(address)

    # タイムアウトしたクライアントを削除
    for address in clients_to_remove:
        del connected_clients[address]

def send_response(code, message, token, room_name):
    # レスポンスの準備
    response_code = code.to_bytes(1, byteorder='big')
    operation_payload_size = len(message).to_bytes(4, byteorder='big')
    response_data = response_code + operation_payload_size + message.encode('utf-8')

    # 応答の送信
    tcp_client.sendall(response_data)
    print("send_response sent")

def send_completion_response(code, token, room_name):
    # トークンとルーム名のサイズを取得
    token_size = len(token).to_bytes(1, byteorder='big')
    room_name_size = len(room_name).to_bytes(1, byteorder='big')

    # レスポンスの準備
    response_code = code.to_bytes(1, byteorder='big')
    operation_payload_size = (len(token) + len(room_name)).to_bytes(4, byteorder='big')
    response_data = response_code + operation_payload_size + token_size + room_name_size + token.encode('utf-8') + room_name.encode('utf-8')

    # 応答の送信
    tcp_client.sendall(response_data)
    print("send_completion_response sent")

def process_message(room_name, sender_address, message):
    # メッセージを処理するロジックを追加
    print(f"Received message '{message}' from {connected_clients[sender_address]['username']} in room '{room_name}'")

    # 新しいメッセージを接続中の全クライアントにリレーする
    for client_address, client_info in connected_clients.items():
        # 同じチャットルーム内のクライアントにのみリレーする
        if client_info['room_name'] == room_name and client_address != sender_address:
            client_username = client_info['username']
            relay_message = f"{connected_clients[sender_address]['username']}: {message}"
            udp_sock.sendto(relay_message.encode('utf-8'), client_address)

# クライアントからのメッセージを受信した後の処理
def handle_client_message(room_name, sender_address, message):
    # メッセージを処理する
    process_message(room_name, sender_address, message)

# チャットルームごとのメッセージ処理のループ
def chat_room_handler(room_name):
    while True:
        # メッセージを受信
        data, address = udp_sock.recvfrom(4096)
        room_name_size = int.from_bytes(data[:1], byteorder='big')
        sender_address = address  # 送信者のアドレス

        if room_name_size > 0:
            room_name = data[1:1 + room_name_size].decode('utf-8')
            message = data[1 + room_name_size:].decode('utf-8')

            # クライアント情報にルーム名を設定
            connected_clients[sender_address]['room_name'] = room_name

            # クライアントからのメッセージを処理
            handle_client_message(room_name, sender_address, message)
        else:
            print("Received invalid message format.")


# TCRP関連の定数
ROOM_NAME_SIZE = 1
OPERATION = 1
STATE = 1
OPERATION_PAYLOAD_SIZE = 29
MAX_PAYLOAD_SIZE = OPERATION_PAYLOAD_SIZE
HEADER_SIZE = ROOM_NAME_SIZE + OPERATION + STATE + OPERATION_PAYLOAD_SIZE

# AF_INETを使用し、UDPソケットを作成
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# AF_INETを使用し、TCPソケットを作成
tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = '0.0.0.0'
server_udp_port = 9001
server_tcp_port = 9002

print('starting up on port {}'.format(server_udp_port))
# AF_INETを使用し、UDPソケットを作成
udp_sock.bind((server_address, server_udp_port))

print('starting up on TCP port {}'.format(server_tcp_port))
tcp_sock.bind((server_address, server_tcp_port))
tcp_sock.listen(5)  # 接続待ちの最大数

while True:
    # TCP接続の待ち受け
    print('Waiting for TCP connection...')
    tcp_client, tcp_address = tcp_sock.accept()

    # TCP接続からのデータを受信
    tcp_data = tcp_client.recv(1024)

    # TCRPプロトコルを適用する
    header = tcp_data[:HEADER_SIZE]
    room_name_size, operation, state = header[:3]  # 末尾のoperation_payload_sizeを除外
    operation_payload_size = int.from_bytes(header[3:], byteorder='big')  # バイト列を整数に変換

    room_name = tcp_data[HEADER_SIZE:HEADER_SIZE + room_name_size].decode('utf-8')
    operation_payload = tcp_data[HEADER_SIZE + room_name_size:HEADER_SIZE + room_name_size + operation_payload_size]



    # try:
    #     header = tcp_data[:HEADER_SIZE]
    #     print("header = " + header)
    #     room_name_size, operation, state = header[:3]  # 末尾のoperation_payload_sizeを除外
    #     operation_payload_size = int.from_bytes(header[3:], byteorder='big')  # バイト列を整数に変換
    # except Exception as e:
    #     print(f"153 Error decoding header: {e}")

    if operation_payload_size > 0:
        try:
            room_name = tcp_data[HEADER_SIZE:HEADER_SIZE + room_name_size].decode('utf-8')
            operation_payload = tcp_data[HEADER_SIZE + room_name_size:]
            
        except Exception as e:
            print(f"160 Error decoding header: {e}")
            print(f"Received data: {tcp_data}")
    else:
        print(f"Received TCRP message with operation_payload_size <= 0")


    # print("room_name_size = " + room_name_size.decode())
    # print("operation_payload_size = " + operation_payload_size.decode())
    # print("MAX_PAYLOAD_SIZE = " + MAX_PAYLOAD_SIZE)
    print("operation = " + str(operation))

    if room_name_size > 0:
        #  and operation_payload_size <= MAX_PAYLOAD_SIZE
        try:
            json_payload = json.loads(operation_payload)  # JSONとしてデコード
            print(f"Decoded payload as JSON: {json_payload}")
            print(f"Received TCRP message in room '{room_name}' with payload '{operation_payload.decode('utf-8')}' from {tcp_address}")
        except json.JSONDecodeError:
            try:
                integer_payload = int.from_bytes(operation_payload, byteorder='big')  # 整数としてデコード
                print(f"Decoded payload as integer: {integer_payload}")
            except ValueError:
                try:
                    string_payload = operation_payload.decode('utf-8')  # 文字列としてデコード
                    print(f"Decoded payload as string: {string_payload}")
                except UnicodeDecodeError:
                    print("Payload is not a valid JSON, integer, or string.")

    # デコードに失敗した場合でも room_name や operation_payload の内容をプリントしないように移動
    else:
        print(f"190 Received TCRP message in room '{room_name}' with payload '{operation_payload.decode('utf-8')}' from {tcp_address}")

    # プロトコル操作コードごとの処理
    if operation == 49:  # サーバー初期化
        print("receive creating room")
        # リクエストの処理
        requested_username = operation_payload.decode('utf-8')  # リクエストから希望するユーザー名を取得

        # チャットルームの作成処理
        create_success, token, room_name = create_chat_room(requested_username)

        # レスポンスの準備
        if create_success:
            response_status = "OK"
            response_message = f"Room creation request received. Status: {response_status}"
            print("response status = " + response_status)
        else:
            response_status = "Error"
            response_message = f"Failed to create room '{requested_username}'. Room may already exist."

        # レスポンスの送信（リクエストの応答）
        send_response(1, response_message, token, room_name)

        if create_success:
            # リクエストの完了
            send_completion_response(2, token, room_name)

    elif operation == 50:  # クライアントが参加リクエストを送信した場合
        # リクエストの処理
        requested_username = operation_payload.decode('utf-8')  # リクエストから希望するユーザー名を取得

        # チャットルームの参加処理
        join_success, token, room_name = join_chat_room(requested_username, room_name, tcp_address)

        # レスポンスの準備
        if join_success:
            response_status = "OK"
            response_message = f"Room join request received. Status: {response_status}"
            print("response status = " + response_status)
        else:
            response_status = "Error"
            response_message = f"Failed to join room '{room_name}'. Room may not exist."

        # レスポンスの送信（リクエストの応答）
        send_response(1, response_message, token, room_name)

        if join_success:
            # リクエストの完了
            send_completion_response(2, token, room_name)

        

    else:
        error_message = "Unknown operation code"
        udp_sock.sendto(error_message.encode('utf-8'), tcp_address)  # 不明な操作コードをクライアントに通知する
        tcp_client.close()  # 接続を閉じる

    print('\nWaiting for data...')
    data, address = udp_sock.recvfrom(8192)
    # update_client_timestamp(address)
    # タイムアウトしたクライアントを定期的にチェック
    # check_client_timeouts()

    if len(data) > 4096:  # 受信したデータが4096バイトを超える場合
            data = data[:4096]
            error_message = "Message size exceeds limit of 4096 bytes"
            udp_sock.sendto(error_message.encode('utf-8'), address)  # エラーメッセージをクライアントに送信

    # usernamelenを読み取る
    usernamelen = int.from_bytes(data[:1], byteorder='big')
    username = data[1:1 + usernamelen].decode('utf-8')
    message = data[1 + usernamelen:].decode('utf-8')

    print(f"Received message '{message}' from {username} at {address}")

    # クライアント情報を辞書に追加
    connected_clients[address] = {'username': username, 'address': address}

    # 新しいメッセージを接続中の全クライアントにリレーする
    for client_address in connected_clients:
        # 自分自身には送信しないようにする
        if client_address != address:
            client_username = connected_clients[client_address]['username']
            relay_message = f"{username}: {message}"  # リレーするメッセージを作成
            udp_sock.sendto(relay_message.encode('utf-8'), client_address)  # 他のクライアントにメッセージを送信

    # if data:
    #     sent = sock.sendto(message.encode('utf-8'), address)
    #     print('sent {} bytes back to {}'.format(sent, address))