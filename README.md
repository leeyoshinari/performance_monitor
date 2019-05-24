# performace_monitor
Continuously monitor the value of CPU, memory and IO of the specified port in the Linux system.
According to your need, you can save the monitoring results to the MySQL database.

## Usage
1. clone performance-monitor repository
   ```shell
   git clone https://github.com/leeyoshinari/performance_monitor.git
   
   cd performance-monitor
   ```

2. set the `PID`, `the monitoring time`, linux's `username` and `password`, etc.

3. run
   ```shell
   python server.py
   ```
   
## Requirements
1. flask
2. pymysql
3. matplotlib
