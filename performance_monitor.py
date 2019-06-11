#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
import os
import pymysql
import time
import threading
import config as cfg

lock = threading.Lock()


class PerMon(object):
    def __init__(self):
        self._is_run = 0
        self.counter = 0
        self._pid = []
        self.db = None
        self.cursor = None
        self._total_time = 0
        self.interval = int(cfg.INTERVAL)

        self.cpu_cores = 0
        self.total_mem = 0

        self.cpu = []
        self.mem = []

        self.mysql_ip = cfg.MySQL_IP
        self.mysql_username = cfg.MySQL_USERNAME
        self.mysql_password = cfg.MySQL_PASSWORD
        self.database_name = cfg.MySQL_DATABASE

        self.get_cpu_cores()
        self.get_total_mem()

        self.start_time = 0

    @property
    def is_run(self):
        return self._is_run

    @is_run.setter
    def is_run(self, value):
        self._is_run = value

    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, value):
        self._pid = value

    @property
    def total_time(self):
        return self._total_time

    @total_time.setter
    def total_time(self, value):
        self._total_time = value + 200

    def connect_mysql(self):
        if self.db is None:
            self.db = pymysql.connect(self.mysql_ip, self.mysql_username, self.mysql_password, self.database_name)
            self.cursor = self.db.cursor()

        cpu_and_mem_sql = 'CREATE TABLE IF NOT EXISTS cpu_and_mem (id INT NOT NULL PRIMARY KEY auto_increment, pid INT, time DATETIME, cpu FLOAT, mem FLOAT);'
        io_sql = 'CREATE TABLE IF NOT EXISTS io (id INT NOT NULL PRIMARY KEY auto_increment, pid INT, time DATETIME, writer FLOAT, reader FLOAT, io FLOAT);'
        handle_sql = 'CREATE TABLE IF NOT EXISTS handles (id INT NOT NULL PRIMARY KEY auto_increment, pid INT, time DATETIME, handles FLOAT);'

        lock.acquire()
        self.cursor.execute(cpu_and_mem_sql)
        self.cursor.execute(io_sql)
        self.cursor.execute(handle_sql)
        self.db.commit()
        lock.release()

    def write_cpu_mem(self):
        while True:
            if self._is_run == 1 or self._is_run == 2:
                self.connect_mysql()
                self.start_time = time.time()
                start_search_time = time.time()

                while True:
                    if time.time() - self.start_time < self._total_time:
                        get_data_time = time.time()
                        if get_data_time - start_search_time > self.interval:
                            start_search_time = get_data_time
                            if self.counter > cfg.RUN_ERROR_TIMES:
                                self._is_run = 0
                                break

                            try:
                                for pid in self._pid:
                                    cpu = self.get_cpu(pid)
                                    if cpu is None:
                                        continue

                                    mem = self.get_mem(pid)
                                    search_time = time.strftime('%Y-%m-%d %H:%M:%S')

                                    self.write_in_sql(search_time, pid, cpu, mem, 0, 0, 'cpu_and_mem')

                                self.counter = 0

                            except Exception as err:
                                print('Error:{}.'.format(err))
                                self.counter += 1
                                continue

                    else:
                        self._is_run = 0
                        break

                    if self._is_run == 0:
                        break
            else:
                time.sleep(cfg.SLEEPTIME)

    def write_io(self):
        while True:
            if self._is_run == 1 or self._is_run == 2:
                self.connect_mysql()
                self.start_time = time.time()

                while True:
                    if time.time() - self.start_time < self._total_time:
                        if self.counter > cfg.RUN_ERROR_TIMES:
                            self._is_run = 0
                            break

                        try:
                            for ipid in self._pid:
                                ioer = self.get_io(ipid)

                                io_time = time.strftime('%Y-%m-%d %H:%M:%S')

                                self.write_in_sql(io_time, ipid, 0, 0, ioer, 0, 'io')

                            self.counter = 0

                        except Exception as err:
                            print('Error:{}.'.format(err))
                            self.counter += 1
                            continue

                    else:
                        self._is_run = 0
                        break

                    if self._is_run == 0:
                        break
            else:
                time.sleep(cfg.SLEEPTIME)

    def write_handle(self):
        while True:
            if self._is_run == 1 or self._is_run == 2:
                self.connect_mysql()
                self.start_time = time.time()

                while True:
                    if time.time() - self.start_time < self._total_time:
                        if self.counter > cfg.RUN_ERROR_TIMES:
                            self._is_run = 0
                            break

                        try:
                            for hpid in self._pid:
                                handles = self.get_handle(hpid)
                                if handles is None:
                                    continue

                                handle_time = time.strftime('%Y-%m-%d %H:%M:%S')

                                self.write_in_sql(handle_time, hpid, 0, 0, 0, handles, 'handles')

                            self.counter = 0

                        except Exception as err:
                            print('Error:{}.'.format(err))
                            self.counter += 1
                            continue

                    else:
                        self._is_run = 0
                        break

                    if self._is_run == 0:
                        break
            else:
                time.sleep(cfg.SLEEPTIME)

    def get_cpu(self, pid):
        result = os.popen('top -n 1 -b |grep -P {} |tr -s " "'.format(pid)).readlines()[0]
        res = result.strip().split(' ')

        cpu = None
        if str(pid) in res:
            ind = res.index(str(pid))
            cpu = float(res[ind + 8]) / self.cpu_cores

        return cpu

    def get_mem(self, pid):
        result = os.popen('jstat -gc {} |tr -s " "'.format(pid)).readlines()[1]
        res = result.strip().split(' ')

        mem = float(res[2]) + float(res[3]) + float(res[5]) + float(res[7])

        return mem / 1024 / 1024

    def get_io(self, pid):
        result = os.popen('iotop -n 1 -b -qq |grep -P {} |tr -s " "'.format(pid)).readlines()
        res = [line for line in result if 'grep' not in line]
        iores = res[0].split(' ')

        writer = None
        reader = None
        ioer = None
        if str(pid) in iores:
            ind = iores.index(str(pid))
            ioer = float(iores[ind + 9])
            writer = self.all_to_k(float(iores[ind + 3]), iores[ind + 4])
            reader = self.all_to_k(float(iores[ind + 5]), iores[ind + 6])

        return [ioer, reader, writer]

    def get_handle(self, pid):
        result = os.popen("lsof -n | awk '{print $2}'| sort | uniq -c | sort -nr | " + "grep {}".format(pid)).readlines()
        res = result[0].strip().split(' ')
        handles = None
        if str(pid) in res:
            handles = int(res[0])

        return handles

    def get_cpu_cores(self):
        result = os.popen('cat /proc/cpuinfo| grep "processor"| wc -l').readlines()[0]

        self.cpu_cores = int(result)

    def get_total_mem(self):
        result = os.popen('cat /proc/meminfo| grep "MemTotal"| uniq').readlines()[0]

        self.total_mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024

    def all_to_k(self, value, keys):
        if keys == 'B/s':
            return value / 1024
        elif keys == 'M/s':
            return value * 1024
        elif keys == 'K/s':
            return value
        else:
            return None

    def write_in_sql(self, search_time, pid, cpu, mem, ioer, handles, dbname):
        if self.db is None:     # If MySQL connection is broken, reconnect.
            self.db = pymysql.connect(self.mysql_ip, self.mysql_username, self.mysql_password, self.database_name)
            self.cursor = self.db.cursor()

        if dbname == 'cpu_and_mem':
            sql = "INSERT INTO {}(id, pid, time, cpu, mem) VALUES (default, {}, '{}', {}, {});".format(dbname, pid, search_time, cpu, mem)
        if dbname == 'io':
            sql = "INSERT INTO {}(id, pid, time, writer, reader, io) VALUES (default, {}, '{}', {}, {}, {});".format(dbname, pid, search_time, ioer[2], ioer[1], ioer[0])
        if dbname == 'handles':
            sql = "INSERT INTO {}(id, pid, time, handles) VALUES (default, {}, '{}', {});".format(dbname, pid, search_time, handles)

        lock.acquire()
        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as error:
            print(error)
            self.db.rollback()
        lock.release()

    def __del__(self):
        pass

