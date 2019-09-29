#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import time
import queue
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

import config as cfg
from logger import logger
from Email import sendMsg
from extern import port_to_pid


class PerMon(object):
    def __init__(self):
        self.is_system = 0    # 是否开始监控系统，0为停止监控，1为开始监控
        self._msg = {'port': [], 'pid': [], 'isRun': [], 'startTime': []}
        self.interval = int(cfg.INTERVAL)   # 每次监控时间间隔
        self.error_times = cfg.ERROR_TIMES  # 命令执行失败次数
        self.disk = cfg.DISK        # 待监控的服务部署的磁盘号

        self.cpu_cores = 0  # CPU核数
        self.total_mem = 0  # 总内存

        self.get_cpu_cores()
        self.get_total_mem()

        self.monitor_task = queue.Queue()   # 创建一个FIFO队列
        self.executor = ThreadPoolExecutor(cfg.THREAD_NUM + 1)  # 创建一个线程池

        self.run_error = 0      # 初始化命令执行失败次数
        self.FGC = 0            # 初始化Full GC次数
        self.FGC_time = []      # 存放full gc的时间

    @property
    def start(self):
        return self._msg

    @start.setter
    def start(self, value):
        if value['port']:
            if value['port'] in self._msg['port']:
                index = self._msg['port'].index(value['port'])
                self._msg['pid'][index] = value['pid']
                if self._msg['is_run'][index] == 0:
                    self._msg['is_run'][index] = value['is_run']
                    self._msg['startTime'][index] = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.monitor_task.put((self.write_cpu_mem, index))
                else:
                    pass
            else:
                self._msg['pid'].append(value['pid'])
                self._msg['port'].append(value['port'])
                self._msg['is_run'].append(value['is_run'])
                self._msg['startTime'].append(time.strftime('%Y-%m-%d %H:%M:%S'))
                self.monitor_task.put((self.write_cpu_mem, len(self._msg['port'])-1))
        else:
            pass

        if len(self._msg['port']) > 0:
            self.is_system = 1

    @property
    def stop(self):
        return self._msg

    @stop.setter
    def stop(self, value):
        index = self._msg['port'].index(value['port'])
        self._msg['is_run'][index] = value['is_run']

    def worker(self):
        while True:
            func, param = self.monitor_task.get()
            func(param)
            self.monitor_task.task_done()

    def monitor(self):
        for i in range(cfg.THREAD_NUM + 1):
            self.executor.submit(self.worker)

        self.monitor_task.put((self.write_system_cpu_mem, 1))

    def write_cpu_mem(self, index):
        """
            监控CPU和内存.
        """
        start_search_time = time.time()
        port = self._msg['port'][index]
        pid = self._msg['pid'][index]
        while True:
            if self._msg['isRun'][index] == 1:  # 开始监控
                get_data_time = time.time()
                if get_data_time - start_search_time > self.interval:   # 如果大于每次监控时间间隔，则开始监控
                    start_search_time = get_data_time
                    try:
                        cpu, mem = self.get_cpu(pid)    # 获取CPU和内存

                        if cpu is None:
                            if port:
                                # 如果没有获取到，可能出现异常，则重新根据端口号查询进程号
                                # 正常情况不会出现异常，如果出现异常，可能端口在重启
                                pid = port_to_pid(port)  # 端口号转进程号
                                if pid:
                                    self._msg['pid'][index] = pid

                                time.sleep(cfg.SLEEPTIME)
                                continue
                            else:
                                if self.run_error > self.error_times:  # 如果命令执行失败次数大于设置次数，停止监控
                                    logger.error(f'{pid} has been stopped monitor, some errors may be occurred.')
                                    break

                                self.run_error += 1     # 命令执行失败次数加1
                                logger.error(f'The number of running command failed is {self.run_error}.')
                                time.sleep(cfg.SLEEPTIME)
                                continue

                        jvm = self.get_mem(pid)     # 获取JVM内存

                        logger.info(f'cpu_and_mem: port_{port},pid_{pid},{cpu},{mem},{jvm}')
                        self.run_error = 0      # 命令执行成功后，重新初始化0

                    except Exception as err:
                        logger.error(traceback.format_exc())
                        time.sleep(cfg.SLEEPTIME)
                        continue

            if self._msg['isRun'][index] == 0:   # stop monitor.
                logger.info(f'{port} has been stopped monitor')
                break

    def write_system_cpu_mem(self, is_system):
        """
            监控系统cpu和内存
        """
        while True:
            if self.is_system == 1:
                disk_r, disk_w, disk_util, cpu, mem = self.get_system_cpu_io(types=True)
                if disk_util is not None:
                    logger.info(f'system: disk_util,{disk_r},{disk_w},{disk_util}')
                if cpu is not None and mem is not None:
                    logger.info(f'system: CpuAndMem,{cpu},{mem}')

                    if mem <= cfg.MIN_MEM:
                        logger.warning(f'Current memory is {mem}, memory is too low.')
                        thread = threading.Thread(target=self.mem_alert, args=(mem,))
                        thread.start()

            else:
                time.sleep(1)

    def get_cpu(self, pid):
        """
            使用top命令获取指定进程的CPU(%)和内存(G)
        """
        # result = os.popen(f'top -n 1 -b -p {pid} |tr -s " "').readlines()       # 执行top命令
        result = os.popen(f'top -b |grep -P {pid} |tr -s " "').readlines()
        res = result[-1].strip().split(' ')
        logger.debug(res)

        cpu = None
        mem = None
        if str(pid) in res:
            ind = res.index(str(pid))
            cpu = float(res[ind + 8]) / self.cpu_cores      # 计算CPU使用率
            mem = float(res[ind + 9]) * self.total_mem      # 计算占用内存大小

        return cpu, mem

    def get_mem(self, pid):
        """
            使用jstat命令获取指定进程的JVM(G)，仅java应用。
        """
        mem = 0
        try:
            result = os.popen(f'jstat -gc {pid} |tr -s " "').readlines()[1]     # 执行jstat命令
            res = result.strip().split(' ')
            logger.debug(res)
            mem = float(res[2]) + float(res[3]) + float(res[5]) + float(res[7])     # 计算JVM大小

            # 将Full GC变化的时间以追加写入的方式写到文件里
            fgc = int(res[14])
            if self.FGC != fgc:
                self.FGC = fgc
                self.FGC_time.append(time.time())
                if len(self.FGC_time) > 2:
                    frequency = (self.FGC_time[-1] - self.FGC_time[0]) / self.FGC
                    if frequency < 3600:
                        logger.warning(f'进程{pid}当前Full GC频率为{frequency}.')
                        thread = threading.Thread(target=self.jvm_alert, args=(frequency, pid,))
                        thread.start()

                with open(cfg.FGC_TIMES, 'a') as f:
                    f.write(f"{self.FGC}--{time.strftime('%Y-%m-%d %H:%M:%S')}" + "\n")

            # 清空存放Full GC时间的变量
            if self.FGC == 0:
                self.FGC_time = []

        except Exception as err:
            logger.info(err)

        return mem / 1024 / 1024

    def get_io(self, pid):
        """
            使用iotop命令获取指定进程读写磁盘速率
        """
        result = os.popen(f'iotop -n 2 -d 1 -b -qqq -p {pid} -k |tr -s " "').readlines()[-1]    # 执行iotop命令
        res = result.strip().split(' ')
        logger.debug(res)

        disk_r, disk_w, disk_util, _, _ = self.get_system_cpu_io()      # 获取磁盘读写速率和IO(%)

        writer = 0
        reader = 0
        if str(pid) in res:
            ind = res.index(str(pid))
            writer = float(res[ind + 3])    # 读磁盘的速率(kB/s)
            reader = float(res[ind + 5])    # 写磁盘的速率(kB/s)

        # 通过进程读写速率和整个磁盘的读写速率，计算进程的IO
        try:
            util = (writer + reader) / (disk_w + disk_r) * disk_util
        except Exception as err:
            logger.warning(err)
            util = 0

        return [reader, writer, disk_r, disk_w, disk_util, util]

    def get_system_cpu_io(self, types=None):
        """
            使用iostat命令获取磁盘读写速率和IO(%)
        """
        disk_r = None
        disk_w = None
        disk_util = None
        cpu = None
        mem = None
        try:
            result = os.popen(f'iostat -x -k {self.disk} 1 2 |tr -s " "').readlines()    # 执行iostat命令
            disk_res = result[-2].strip().split(' ')
            logger.debug(disk_res)

            if self.disk in disk_res:
                disk_r = float(disk_res[5])         # 读磁盘的速率(kB/s)
                disk_w = float(disk_res[6])         # 写磁盘的速率(kB/s)
                disk_util = float(disk_res[-1])     # 磁盘IO(%)

            if types:
                cpu_res = result[-5].strip().split(' ')
                if len(cpu_res) > 3:
                    cpu = 100 - float(cpu_res[-1])      # 系统CPU

                result = os.popen('cat /proc/meminfo| grep MemFree| uniq').readlines()[0]
                mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024      # 系统可用内存

        except Exception as err:
            logger.error(err)

        return disk_r, disk_w, disk_util, cpu, mem

    @staticmethod
    def get_handle(pid):
        """
            使用lsof命令获取指定进程的句柄数
            该命令执行很慢，建议不监控
        """
        result = os.popen("lsof -n | awk '{print $2}'| sort | uniq -c | sort -nr | " + "grep {}".format(pid)).readlines()
        res = result[0].strip().split(' ')
        logger.debug(res)
        handles = None
        if str(pid) in res:
            handles = int(res[0])

        return handles

    def get_cpu_cores(self):
        """
            获取CPU核数
        """
        result = os.popen('cat /proc/cpuinfo| grep "processor"| wc -l').readlines()[0]

        self.cpu_cores = int(result)

        logger.info(f'CPU core number is {self.cpu_cores}')

    def get_total_mem(self):
        """
            获取总内存大小
        """
        result = os.popen('cat /proc/meminfo| grep "MemTotal"| uniq').readlines()[0]

        self.total_mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024 / 100

        logger.info(f'Total memory is {self.total_mem * 100}')

    @staticmethod
    def mem_alert(mem):
        """
            当内存过低的时候，发出警告，并清理缓存
        """
        if cfg.IS_MEM_ALERT:    # 是否邮件发送警告
            msg = {'msg': f'当前剩余内存为{mem:.2f}G'}
            sendMsg(msg)

        if cfg.ECHO:    # 是否清理缓存
            logger.info(f'Start clearing cache：echo {cfg.ECHO} >/proc/sys/vm/drop_caches')
            os.popen(f'echo {cfg.ECHO} >/proc/sys/vm/drop_caches')
            logger.info('Clear cache successful.')

    @staticmethod
    def jvm_alert(frequency, pid):
        """
            当 Full GC 频繁时，发出警告
        """
        if cfg.IS_JVM_ALERT:    # 是否邮件发送警告
            msg = {'msg': f'{pid}进程，最近一次Full GC频率为{frequency}'}
            sendMsg(msg)

    def __del__(self):
        pass
