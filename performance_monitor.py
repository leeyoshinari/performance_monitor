#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Author: leeyoshinari
# nohup python -u performance_monitor.py > monitor.log 2>&1 &
import os
import pymysql
import time
import argparse


class PerMon(object):
    def __init__(self, PID, total_time, interval, mysql_ip, mysql_username, mysql_password, database_name):

        self.counter = 0    # 执行linux命令失败计数，默认5次
        self.pid = PID
        self.db = None
        self.cursor = None
        self.total_time = int(total_time) + 200
        self.interval = int(interval)

        self.cpu_cores = 0
        self.total_mem = 0

        self.cpu = []
        self.mem = []

        self.mysql_ip = mysql_ip
        self.mysql_username = mysql_username
        self.mysql_password = mysql_password
        self.database_name = database_name

        self.connect_mysql()
        self.get_cpu_cores()
        self.get_total_mem()

        self.start_time = time.time()

    def connect_mysql(self):
        self.db = pymysql.connect(self.mysql_ip, self.mysql_username, self.mysql_password, self.database_name)
        self.cursor = self.db.cursor()

        sql = 'CREATE TABLE IF NOT EXISTS performance (' \
              'id INT NOT NULL PRIMARY KEY auto_increment,' \
              'pid INT,' \
              'time DATETIME, ' \
              'cpu FLOAT,' \
              'mem FLOAT,' \
              'io FLOAT);'

        self.cursor.execute(sql)
        self.db.commit()

    def get_data(self):
        start_search_time = time.time()

        while True:
            if time.time() - self.start_time < self.total_time:
                get_data_time = time.time()
                if get_data_time - start_search_time > self.interval:
                    start_search_time = get_data_time
                    if self.counter > 10:
                        break

                    try:
                        cpu, mem = self.get_cpu_mem()
                        if cpu is None:
                            continue

                        ioer = self.get_io()
                        if ioer is None:
                            continue

                        search_time = time.strftime('%Y-%m-%d %H:%M:%S')

                        self.write_in_sql(search_time, cpu, mem, ioer)

                        self.counter = 0

                    except Exception as e:
                        print('Error:{}.'.format(e))
                        self.counter += 1
                        continue

                    print('{} CPU: {}%, MEM: {}G, IO: {}%'.format(search_time, cpu, mem, ioer))

            else:
                break

    def get_cpu_mem(self):
        result = os.popen('top -n 1 -b |grep -P {} |tr -s " "'.format(self.pid)).readlines()[0]
        # print(result)
        res = result.strip().split(' ')

        cpu = None
        mem = None
        if str(self.pid) in res:
            ind = res.index(str(self.pid))
            # search_time = time.strftime('%Y-%m-%d %H:%M:%S')
            cpu = float(res[ind + 8]) / self.cpu_cores
            mem = float(res[ind + 9]) * self.total_mem

        return cpu, mem

    def get_io(self):
        result = os.popen('iotop -n 1 -b -qq |grep -P {} |tr -s " "'.format(self.pid)).readlines()
        res = [line for line in result if 'grep' not in line]
        line = res[0].split(' ')

        # writer = None
        # reader = None
        ioer = None
        if str(self.pid) in line:
            ind = res.index(str(self.pid))
            ioer = float(line[ind + 8])

        return ioer

    def get_cpu_cores(self):
        result = os.popen('cat /proc/cpuinfo| grep "processor"| wc -l').readlines()[0]

        self.cpu_cores = int(result)

    def get_total_mem(self):
        result = os.popen('cat /proc/meminfo| grep "MemTotal"| uniq').readlines()[0]

        self.total_mem = float(result.split(':')[-1].split('k')[0].strip()) / 1024 / 1024

    def write_in_sql(self, search_time, cpu, mem, ioer):
        if self.db is None:     # If MySQL connection is broken, reconnect.
            self.db = pymysql.connect(self.mysql_ip, self.mysql_username, self.mysql_password, self.database_name)
            self.cursor = self.db.cursor()

        sql = "INSERT INTO performance(id, pid, time, cpu, mem, io) " \
              "VALUES (default, {}, '{}', {}, {}, {}});".format(self.pid, search_time, cpu, mem, ioer)

        try:
            self.cursor.execute(sql)
            self.db.commit()
        except Exception as error:
            print(error)
            self.db.rollback()

    def run(self):
        self.get_data()
        self.db.close()

    def __del__(self):
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--PID', required=True, type=int, help='The PID that is monitored.')
    parser.add_argument('--total_time', required=True, type=int, help='The total time(/s) of monitoring.')
    parser.add_argument('--interval', default=2, type=int, help='The interval(/s) of getting data from server.')
    parser.add_argument('--ip', required=True, type=str, help='The MySQL ip.')
    parser.add_argument('--username', default='root', type=str, help='The username of the MySQL.')
    parser.add_argument('--password', required=True, type=str, help='The password of the MySQL.')
    parser.add_argument('--database', required=True, type=str, help='The name of the database of the MySQL.')
    args = parser.parse_args()

    # result = os.popen('ps -ef|grep {}'.format(args.PID)).readlines()[0]

    perfmon = PerMon(args.PID, args.total_time, args.interval, args.ip, args.username, args.password, args.database)
    perfmon.run()


if __name__ == '__main__':
    main()
