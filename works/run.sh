python server.py > send.log 2>&1 &
sleep 0.5
python client.py > recv.log 2>&1 &
wait -n
cat send.log recv.log > result.log
