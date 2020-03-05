# performace_monitor
## 介绍
#### 已完成如下功能<br>
1、监控整个服务器的CPU使用率、剩余内存大小和磁盘IO<br>
2、监控指定端口的CPU使用率、内存占用大小<br>
3、针对java应用，可以监控jvm大小和垃圾回收情况；当Full GC频率过高时，可发送邮件提醒<br>
4、当系统剩余内存过低时，可发送邮件提醒；也可设置自动清理缓存<br>
5、可随时启动/停止监控指定端口<br>
6、当端口重启后，可自动重新监控<br>
7、可按照指定时间段可视化监控结果<br>

#### 实现过程
1、为保证监控结果准确性，直接使用Linux系统命令获取数据；且可视化时未做任何数据处理<br>
2、使用`flask`框架搭建前后端<br>
3、采用线程池+队列的方式实现同时监控多个端口<br>
4、监控数据直接写到日志中，并直接从日志中读取数据<br>

## 用法
1. 克隆`performance_monitor`仓库
   ```shell
   git clone https://github.com/leeyoshinari/performance_monitor.git
   cd performance_monitor
   ```

2. 修改`config.py`配置文件。
   
3. 确定你的应用运行在哪个磁盘上，通过`df -h 文件名`查询应用所在磁盘，然后将磁盘号填入`config.py`文件中。

4. 运行
   ```shell
   nohup python3 server.py &
   ```

5. 使用<br>
   在浏览器中输入`http://ip:port`可查看主页<br>
   (1) 输入`http://ip:port/startMonitor`页面如下：<br>
   ![startMonitor](https://github.com/leeyoshinari/performance_monitor/blob/master/templates/Visualize.jpg)
   
   (2) 输入`http://ip:port/Visualize`页面如下：<br>
   ![Visualize](https://github.com/leeyoshinari/performance_monitor/blob/master/templates/startMonitor.jpg)
   
## 注意
1. 服务器必须支持以下命令：`jstat`、`top`、`iostat`、`netstat`、`ps`、`top`，如不支持，请安装。

2. 如果你不知道怎么在Linux服务器上安装好Python3.7+，[请点我](https://github.com/leeyoshinari/performance_monitor/wiki/Python-3.7.x-%E5%AE%89%E8%A3%85)。

## Requirements
1. flask
2. flask_bootstrap
3. matplotlib
4. Python 3.7+
