#client
import sys
import socket
import time
import threading
import random
import numpy as np
from tqdm import tqdm

#define
HOST="127.0.0.1"
SERVER_RECEIVE_PORT=50000 #服务端接收报文
SERVER_ACK_PORT=50001 #服务端发送ACK 非必须
CLIENT_SEND_PORT=50002 #客户端发送报文 非必须
CLIENT_ACK_PORT=50003 #客户端接收ACK
MAX_DATA_LENGTH=4194304 #最大报文长度4M
SWND=8 #发送窗口
TIMEOUT=2 #超时重传时间

def msg_sender(msg_array,ack_array):
    #信息发送套接字
    m_sender=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    m_sender.bind((HOST,CLIENT_SEND_PORT))

    time_array=np.zeros_like(msg_array,dtype=float)
    swnd=SWND
    segment_p=0
    swnd_p=0
    with tqdm(total=len(msg_array)) as pbar:
        while(True):
            if(segment_p==len(msg_array)):#发送完成
                pbar.update(swnd)
                m_sender.close()
                break
            while ack_array[swnd_p]:#移动窗口
                swnd_p+=1
                pbar.update()
            if segment_p==swnd_p+swnd:
                for _ in range(segment_p-swnd,segment_p):
                    if ack_array[_]==False and time.perf_counter()-time_array[_]>TIMEOUT:
                        m_sender.sendto(str(msg_array[_]).encode("utf8"),(HOST,SERVER_RECEIVE_PORT))
                continue
            m_sender.sendto(str(msg_array[segment_p]).encode("utf8"),(HOST,SERVER_RECEIVE_PORT))
            time_array[segment_p]=time.perf_counter()
            segment_p+=1


def ack_receiver(ack_array):
    #ack接收套接字
    ack_receiver=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    ack_receiver.bind((HOST,CLIENT_ACK_PORT))
    ack_receiver.settimeout(2*TIMEOUT)
    while(True):
        ack,addr=ack_receiver.recvfrom(1024)
        if ack:
            ack=int(ack.decode("utf8"))
            ack_array[ack]=True

class senderThread(threading.Thread):
    def __init__(self,msg_array,ack_array):
        threading.Thread.__init__(self)
        self.msg_array=msg_array
        self.ack_array=ack_array
    def run(self):
        msg_sender(self.msg_array,self.ack_array)

class receiverThread(threading.Thread):
    def __init__(self,ack_array):
        threading.Thread.__init__(self)
        self.ack_array=ack_array
    def run(self):
        ack_receiver(self.ack_array)


if __name__=="__main__":
    msg_length=1024
    massage=np.zeros([msg_length],dtype=int)
    for _ in range(len(massage)):
        massage[_]=_
    ack=np.zeros([msg_length],dtype=bool)
    #print(massage.shape,ack.shape)
    thread1=senderThread(massage,ack)
    thread2=receiverThread(ack)
    thread1.start()
    thread2.start()