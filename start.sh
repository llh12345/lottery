#for ((i=0;i < 10000;i++));do
#  echo "start to execute lottery script at $(date)"
#  echo "test" >> /Users/luolinhong/script/py/lottery/result.log
#  python3 /Users/luolinhong/script/py/lottery/main.py >> /Users/luolinhong/script/py/lottery/result.log
#  echo "done"
#  sleep 600
#done
ps aux | grep "main.py" | awk '{print $2}' | xargs kill -9
nohup python3 main.py 2>&1 &

#ps aux | grep "main.py" | awk '{print $2}' | xargs kill -9