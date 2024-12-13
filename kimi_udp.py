import socket
import time
import sys
import threading

def udp_sender(send_count, interval):
    # 创建UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', 10000)  # 服务器地址和端口号

    lost_count = 0
    for i in range(send_count):
        message = f'Message {i+1}'.encode()  # 发送的消息包含顺序信息
        sent = sock.sendto(message, server_address)
        print(f'发送了数据包 {i+1}')
        time.sleep(interval)  # 等待指定的时间间隔

        # 等待接收端的确认
        data, _ = sock.recvfrom(4096)
        if data.decode().strip() == 'ack':
            print(f'成功收到确认 {i+1}')
        else:
            lost_count += 1
            print(f'数据包 {i+1} 未收到确认')

    print(f'总共丢失的数据包数: {lost_count}')
    sock.close()

def udp_receiver():
    # 创建UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('', 10000)  # 绑定到所有可用接口的10000端口
    sock.bind(server_address)

    print('等待接收数据包...')
    received_count = 0
    while True:
        data, address = sock.recvfrom(4096)  # 接收数据包
        message_id = data.decode().split()[-1]
        print(f'收到来自 {address} 的数据包：{data.decode()}')
        received_count += 1
        sock.sendto(b'ack', address)  # 发送确认

        # 如果接收到退出指令
        if data.decode() == 'exit':
            break

    print(f'总共成功收到的数据包数: {received_count}')
    sock.close()

def main(send_count=5, interval=1):
    # 启动接收端
    receiver_thread = threading.Thread(target=udp_receiver)
    receiver_thread.start()

    # 启动发送端
    udp_sender(send_count, interval)

    # 等待接收线程结束
    receiver_thread.join()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('使用方法: python script.py <send_count> <interval>')
    else:
        try:
            send_count = int(sys.argv[1])
            interval = float(sys.argv[2])
            rand_port=bool(sys.argv[3])
            main(send_count, interval)
        except ValueError:
            print('参数必须是整数和浮点数')