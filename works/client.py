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
SSEHRESH=16 #慢启动阈值
CWND=1 #拥塞窗口

def msg_sender(msg_array,ack_array):
    #信息发送套接字
    m_sender=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    m_sender.bind((HOST,CLIENT_SEND_PORT))

    time_array=np.zeros_like(msg_array,dtype=float)
    swnd=128
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

def msg_sender_cwnd(msg_array, ack_array):
    # 信息发送套接字
    m_sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    m_sender.bind((HOST, CLIENT_SEND_PORT))

    time_array = np.zeros_like(msg_array, dtype=float)
    cwnd=CWND #拥塞窗口
    wnd_start=0 #窗口起始
    wnd_end=wnd_start+cwnd #窗口结束
    send_p=wnd_start #发送指针

    with tqdm(total=len(msg_array)) as pbar:
        while (True):
            if wnd_start==wnd_end:
                if wnd_end==len(msg_array): # 发送完成
                    pbar.update()
                    m_sender.close()
                    break
                wnd_end=min(wnd_end+cwnd,len(msg_array))
            while ack_array[wnd_start]: # 移动窗口)
                if random.random()>0.9:
                    cwnd+=1
                wnd_start+=1
                pbar.update()
            if send_p==wnd_end:
                #send_ratio=1-np.sum(ack_array[wnd_start:wnd_end])/cwnd
                for _ in range(wnd_start,wnd_end):
                    if ack_array[_]==False and time.perf_counter()-time_array[_]>TIMEOUT:
                        cwnd=max(1,cwnd-1)
                        m_sender.sendto(str(msg_array[_]).encode("utf8"),(HOST,SERVER_RECEIVE_PORT))
                        time_array[_]=time.perf_counter()
            else:
                m_sender.sendto(str(msg_array[send_p]).encode("utf8"),(HOST,SERVER_RECEIVE_PORT))
                time_array[send_p]=time.perf_counter()
                send_p+=1




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
    def __init__(self,msg_array,ack_array,cwnd):
        threading.Thread.__init__(self)
        self.msg_array=msg_array
        self.ack_array=ack_array
        self.cwnd=cwnd
    def run(self):
        if self.cwnd:
            msg_sender_cwnd(self.msg_array,self.ack_array)
        else:
            msg_sender(self.msg_array,self.ack_array)

class receiverThread(threading.Thread):
    def __init__(self,ack_array):
        threading.Thread.__init__(self)
        self.ack_array=ack_array
    def run(self):
        ack_receiver(self.ack_array)


if __name__=="__main__":
    msg_length=2048
    massage=np.zeros([msg_length],dtype=int)
    for _ in range(len(massage)):
        massage[_]=_
    ack=np.zeros([msg_length],dtype=bool)
    #print(massage.shape,ack.shape)
    thread1=senderThread(massage,ack,cwnd=False)
    thread2=receiverThread(ack)
    thread1.start()
    thread2.start()