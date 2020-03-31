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
8、支持分布式部署<br>

#### 实现过程
1、为保证监控结果准确性，直接使用Linux系统命令获取数据；且可视化时未做任何数据处理<br>
2、使用基于协程的http框架`aiohttp`满足高并发<br>
3、主机（服务端）前端使用`jinjia2`模板渲染<br>
4、采用线程池+队列的方式实现同时监控多个端口<br>
5、从机（客户端）每隔5s向主机（服务端）注册本机IP和端口<br>
6、主机（服务端）每隔5s会查询所有已注册的从机（客户端）的状态<br>
7、使用influxDB数据库存储监控数据<br>

## 使用
1. 克隆 performance_monitor
   ```shell
   git clone https://github.com/leeyoshinari/performance_monitor.git
   ```

2. 分别修改master和slave文件夹里的配置文件 `config.ini`.
   
5. 运行
   ```shell
   nohup python3 server.py &
   ```

6. 页面访问<br>
   （1）从机（客户端）启动后，输入`http://ip:port`可以看到页面显示服务器的CPU核数、总内存和磁盘号<br>
   ![slave home](https://github.com/leeyoshinari/performance_monitor/blob/master/master/templates/slave.jpg)
   
   （2）主机（服务端）启动后，输入`http://ip:port`可以看到首页，页面展示已经注册的从机（客户端）的IP和注册时间<br>
   ![master home](https://github.com/leeyoshinari/performance_monitor/blob/master/master/templates/home.jpg)
   
   （3）主机（服务端）启动后，输入`http://ip:port/startMonitor`可以看到监控页面；点击开始监控按钮，即可在指定的服务器上开始监控指定的端口；点击停止监控按钮，即可在指定的服务器上停止监控指定的端口；点击获取监控列表按钮，可以查看当前已经监控的端口<br>
   ![startMonitor](https://github.com/leeyoshinari/performance_monitor/blob/master/master/templates/monitor.jpg)
   
   （4）主机（服务端）启动后，输入`http://ip:port/Visualize`可以看到可视化页面；点击画图按钮，即可将指定服务器上的指定端口的监控数据可视化<br>
   ![Visualize](https://github.com/leeyoshinari/performance_monitor/blob/master/master/templates/visual.jpg)
   
## 注意
1. 服务器必须支持以下命令：`jstat`、`top`、`iostat`、`netstat`、`ps`、`top`，如不支持，请安装。

2. 如果你不知道怎么在Linux服务器上安装好Python3.7+，[请点我](https://github.com/leeyoshinari/performance_monitor/wiki/Python-3.7.x-%E5%AE%89%E8%A3%85)。

3. 如果你对监控要求不高，可以使用单机版，其对第三方模块依赖较少。如需获取，请切换至`single`分支，或[点我](https://github.com/leeyoshinari/performance_monitor/tree/single)。

## Requirements
1. aiohttp>=3.6.2
2. aiohttp_jinja2>=1.2.0
3. jinja2>=2.10.1
4. matplotlib>=3.1.0
5. influxdb>=5.2.3
6. requests
7. Python 3.7+
