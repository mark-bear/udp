#server
import socket
import threading
import queue
import time
from random import random


#define
HOST="127.0.0.1"
SERVER_RECEIVE_PORT=50000 #服务端接收报文
SERVER_ACK_PORT=50001 #服务端发送ACK
CLIENT_SEND_PORT=50002 #客户端发送报文
CLIENT_ACK_PORT=50003 #客户端接收ACK
MAX_DATA_LENGTH=4194304 #最大报文长度4M
SWND=8 #发送窗口
TIMEOUT=2 #超时重传时间
BANDWIDTH=64 #带宽

def msg_receiver(rec_queue,p_drop):
    #接收发送端报文，存入rec_array，以概率p_drop丢包
    rec_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    rec_socket.bind((HOST,SERVER_RECEIVE_PORT))
    rec_socket.settimeout(2*TIMEOUT)
    round_start=time.perf_counter()
    pkg_num=0 #未被丢弃包数
    pkg_recv=0 #收到包数
    while(True):
        round_end=time.perf_counter()
        time_gap=round_end-round_start
        if time_gap>=1:
            pkg_p_sec=pkg_num/time_gap
            pkg_recv_p_sec=pkg_recv/time_gap
            print("speed:{}/{} in {} seconds".format(pkg_p_sec,pkg_recv_p_sec,time_gap))
            if pkg_recv_p_sec>BANDWIDTH:
                p_drop=(pkg_recv_p_sec-BANDWIDTH)/pkg_recv_p_sec
            else:
                p_drop=0
            pkg_num=0
            pkg_recv=0
            round_start=round_end
        msg,addr=rec_socket.recvfrom(1024)
        #print(msg.decode("utf8"),addr)
        msg=msg.decode("utf8")
        if msg:
            pkg_recv+=1
            if random()>p_drop and not rec_queue.full():
                rec_queue.put(msg)
                pkg_num+=1
            continue

def ack_sender(rec_queue):
    #回复ack信息，线程间通过队列通信
    ack_socket=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    ack_socket.bind((HOST,SERVER_ACK_PORT))
    wc_dog=time.perf_counter()
    while(True):
        if not rec_queue.empty():
            ack=str(rec_queue.get()).encode("utf8")
            ack_socket.sendto(ack,(HOST,CLIENT_ACK_PORT))
            wc_dog=time.perf_counter()
            continue
        if time.perf_counter()-wc_dog>2*TIMEOUT:
            ack_socket.close()
            print("ACK TIMEOUT CLOSE")
            break


class msgrecThread(threading.Thread):
    def __init__(self,rec_queue,p_drop):
        threading.Thread.__init__(self)
        self.rec_queue=rec_queue
        self.p_drop=p_drop
    def run(self):
        msg_receiver(self.rec_queue,self.p_drop)

class acksendThread(threading.Thread):
    def __init__(self,rec_queue):
        threading.Thread.__init__(self)
        self.rec_queue=rec_queue
    def run(self):
        ack_sender(self.rec_queue)


if __name__=="__main__":
    msg_queue=queue.Queue(MAX_DATA_LENGTH)
    thread1=msgrecThread(msg_queue,0)
    thread2=acksendThread(msg_queue)
    thread1.start()
    thread2.start()