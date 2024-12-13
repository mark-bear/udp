import socket
import struct

# 配置UDP接收端
UDP_IP = "127.0.0.1"
UDP_PORT = 12345
ACK_PORT = 12346  # 发送ACK的端口（与发送端的ACK接收端口相匹配）
BUFFER_SIZE = 2048

# 创建UDP套接字
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# 创建用于发送ACK的套接字
ack_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    while True:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        seq_num, timestamp = struct.unpack('!II', data[:8])
        message = data[8:].decode() if len(data) > 8 else ""
        print(f"Received message {seq_num} with timestamp {timestamp}ms: {message}")
        
        # 发送ACK
        ack_message = struct.pack('!II', seq_num, 0)  # 时间戳在这里不需要，但保留结构一致性
        ack_sock.sendto(ack_message, (UDP_IP, ACK_PORT))
        print(f"Sent ACK for message {seq_num}")
except KeyboardInterrupt:
    pass
finally:
    sock.close()
    ack_sock.close()