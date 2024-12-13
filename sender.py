import socket
import time
import random
import struct
import threading

# 配置UDP发送端
UDP_IP = "127.0.0.1"
UDP_PORT = 12345
NUM_MESSAGES = 4096
MESSAGE = b"Hello, UDP with ACK!"
PACKET_SIZE = len(MESSAGE) + 8  # 序列号（4字节）+ 时间戳（4字节）+ 消息长度
ACK_PORT = 12346  # 接收ACK的端口（可以与发送端口不同）
TIMEOUT = 2.0  # 超时时间（秒）
RETRY_LIMIT = 3  # 最大重传次数

# 创建UDP套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#sock.bind(("", UDP_PORT))  # 绑定发送端口（虽然UDP不需要，但为了避免端口冲突）

# 用于接收ACK的套接字
ack_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ack_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ack_sock.bind(("", ACK_PORT))
ack_sock.settimeout(TIMEOUT)  # 设置超时时间

# 未确认消息的队列
unacked_messages = []
lock = threading.Lock()

def send_message(seq_num):
    timestamp = int(time.time())  # 毫秒级时间戳
    message = struct.pack('!II', seq_num, timestamp) + MESSAGE
    sock.sendto(message, (UDP_IP, UDP_PORT))
    print(f"Sent message {seq_num} at {timestamp}ms")
    with lock:
        unacked_messages.append((seq_num, time.time()))

def handle_acks():
    while True:
        try:
            data, addr = ack_sock.recvfrom(PACKET_SIZE)
            ack_seq_num, _ = struct.unpack('!II', data[:8])
            with lock:
                for i, (seq_num, send_time) in enumerate(unacked_messages):
                    if seq_num == ack_seq_num:
                        print(f"Received ACK for message {ack_seq_num}")
                        del unacked_messages[i]
                        break
                else:
                    print(f"Unexpected ACK for message {ack_seq_num}")
        except socket.timeout:
            with lock:
                for seq_num, send_time in list(unacked_messages):
                    if time.time() - send_time > TIMEOUT:
                        print(f"Timeout, retransmitting message {seq_num}")
                        send_message(seq_num)
                    else:
                        break  # 只需检查超时的消息，因此一旦找到未超时的就停止
        except Exception as e:
            print(f"Error receiving ACK: {e}")
            break

# 启动ACK处理线程
threading.Thread(target=handle_acks, daemon=True).start()

# 发送消息
for i in range(NUM_MESSAGES):
    send_message(i)

# 等待一段时间以确保所有消息都被处理（在实际应用中，应该有更好的同步机制）
time.sleep(NUM_MESSAGES * TIMEOUT * (RETRY_LIMIT + 1))

# 关闭套接字
sock.close()
ack_sock.close()