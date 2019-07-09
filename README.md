# performace_monitor
Continuously monitor the value of CPU, memory, IO and handles of the specified port or PID in the Linux system.
Monitor can be started or stopped at any time. And plotting them.

## Usage
1. Clone performance_monitor repository
   ```shell
   git clone https://github.com/leeyoshinari/performance_monitor.git
   cd performance_monitor
   ```

2. Modify `config.py`.
   
3. Ensure which disk your application runs, or which disk your application reads and writes. And then, set the name of disk into `config.py`.

4. Run
   ```shell
   python3 server.py
   ```
   or
   ```shell
   nohup python3 server.py &
   ```

5. Start monitor<br>
   Enter `http://ip:port/runMonitor?isRun=1&type=pid&num=123,456&totalTime=3600` in your browser<br>
   param:<br>
   &emsp;&emsp;`isRun=0`: stop monitor; `isRun=1`: start monitor.<br>
   &emsp;&emsp;`type=port` means the `num` is port. `type=pid` means the `num` is pid. The `num` can be specified one or more.<br>
   &emsp;&emsp;&emsp;&emsp;&emsp;example: `num=1234` or `num=1234,5678`<br>
   &emsp;&emsp;`totalTime`: the total time of monitoring. It's second. If `totalTime` is null, it will always monitor.
   
6. Plotting<br>
   Enter `http://ip:port/plotMonitor?type=pid&num=1234&startTime=2019-05-21 08:08:08&duration=3600` in your browser<br>
   param:<br>
   &emsp;&emsp;`type=port` means the `num` is port. `type=pid` means the `num` is pid.<br>
   &emsp;&emsp;`startTime` and `duration` are optional parameters, if you plot last monitor, they are not needed, but if you want to plot over a period of time, they are needed. `duration` is second. The range of a period of time is `startTime + duration`. `startTime` must be accurate, if you're not sure it, please see `startTime.txt` or logs.

## Note
1. Your Linux must support the `jstat`, `top`, `iotop`, `iostat` and `lsof` commands, if not, please install them.

2. In `config.py`, the default value of `IS_HANDLE` is `False`. If it's setted to `True`, the command of querying handle number is very slow, and occupy system resources. So, if not necessary, setting it to `True` is not suggested. You can query handle number manually.

## Requirements
1. flask
2. matplotlib
