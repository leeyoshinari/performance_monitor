# performace_monitor
Continuously monitor the value of CPU, memory, IO of the specified port in the Linux system.
You can start or stop monitoring at any time. You can save the monitoring results to the MySQL database. And plotting them.

## Usage
1. Clone performance_monitor repository
   ```shell
   git clone https://github.com/leeyoshinari/performance_monitor.git
   
   cd performance_monitor
   ```

2. Modify `config.py`.

3. Create database, named `MySQL_DATABASE` that you set in `config.py`.

4. Run
   ```shell
   python server.py
   ```
   or
   ```shell
   nohup python -u server.py > server.log 2>&1 &
   ```

5. Start monitor<br>
   Enter `http://ip:port/startMonitor?isRun=1&port=123,456&totalTime=3600` in your browser<br>
   param:<br>
   &emsp;&emsp;`isRun=0`: stop monitor; `isRun=1`: start monitor with clear database; `isRun=2`: start monitor without clear database.<br>
   &emsp;&emsp;`port`: monitor system resources occupied by a specified port, it can monitor one or more ports.<br>
   &emsp;&emsp;&emsp;&emsp;&emsp;example: `port=1234` or `port=1234,5678`<br>
   &emsp;&emsp;`totalTime`:the total time of monitoring. It's second.

6. Stop monitor<br>
   Enter `http://ip:port/stopMonitor?isRun=0` in your browser<br>
   param:<br>
   &emsp;&emsp;`isRun=0`: stop monitor
   
7. Plotting<br>
   Enter `http://ip:port/plotMonitor?type=port&num=1234&startTime=2019-05-21 08:08:08&duration=3600` in your browser<br>
   param:<br>
   &emsp;&emsp;`type=port` means the `num` is port. `type=pid` means the `num` is pid.<br>
   &emsp;&emsp;`startTime` and `duration` are optional parameters, if you plot all time, they are not needed, but if you want to plot over a period of time, they are needed. `duration` is second. The range of a period of time is `startTime + duration`.

8. dropTable<br>
   Enter `http://ip:port/dropTable` in your browser. It drops the table that store the data of monitoring.

## Note
1. Your Linux must support the `jstat`, `top`, `iotop` and `lsof` commands, if not, please install them.

## Requirements
1. flask
2. pymysql
3. matplotlib
