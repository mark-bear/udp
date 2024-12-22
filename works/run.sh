python server.py > recv.log 2>&1 &
sleep 0.5
python client.py > send.log 2>&1 &
wait -n
echo "sended:" > result.log
cat send.log >> result.log
echo "received:" >> result.log
cat recv.log >> result.log
echo "Done!"
rm send.log recv.log