import os
port_list=[50000,50001,50002,50003]
#pid=os.popen("lsof -i:80").readlines()[1].split()[1]
pid_list=[]
for port in port_list:
        cmd_lsof="lsof -i:%s" % port
        pid=os.popen(cmd_lsof).readlines()
        if len(pid)>1:
            pid=pid[1].split()[1]
            pid_list.append(pid)
for pid in pid_list:
    os.system("kill -9 %s" % pid)