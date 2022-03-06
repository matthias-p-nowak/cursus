#!/bin/env python
import concurrent.futures
import logging
import pickle
import random
import socket
import sys
import time
from concurrent.futures.thread import ThreadPoolExecutor

import yaml
from docutils.nodes import thead

config = {}
conn_ids = {}
conn_ips = {}
thread_pool = None


def read_config():
    global config
    args = sys.argv
    logging.info(f"config from {args}")
    if len(args) < 2:
        print(f"run {args[0]} <config>")
        sys.exit(1)
    with open(args[1]) as inp:
        config = yaml.safe_load(inp)
    logging.debug(config)


class CursesConn:
    def __init__(self, server, sock_addr):
        global conn_ips
        # conn_addr = [socket,address]
        self.server = server
        self.s = sock_addr[0]
        self.addr = sock_addr[1]
        self.fd = self.s.makefile('rwb')
        ip = sock_addr[1][0]
        conn_ips[ip] = self

    def read(self):
        try:
            while True:
                obj = pickle.load(self.fd)
                print(f"got an object {obj}")
                if 'iam' in obj:
                    id = obj['iam']
                    print(f"got id {id}")
                    if id == self.server.id:
                        return
                    if id in conn_ids:
                        if conn_ids[id] != self:
                            return
        except Exception as ex:
            logging.debug(f"exception while reading from connection {ex.args}")

        finally:
            self.fd.close()
            self.fd = None
            self.s.close()
            self.s = None


class CursesServer:
    def __init__(self):
        global config
        self.id = random.getrandbits(128)
        for i in range(config['range']):
            try:
                self.socket = socket.create_server(('', config['local'] + i))
                break
            except:
                continue

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.debug("closing server socket")
        self.socket.close()

    def iam(self, fd):
        data = {'iam': self.id}
        pickle.dump(data, fd)
        fd.flush()

    def listen(self):
        global thread_pool
        try:
            self.socket.listen(32)
            while True:
                conn_addr = self.socket.accept()
                con = CursesConn(self, conn_addr)
                self.iam(con.fd)
                thread_pool.submit(con.read)
                logging.debug(f"added connection to {conn_addr[1]}")
        except Exception as ex:
            logging.error("listen exception", ex)

    def add_clients(self):
        try:
            for client in config['members']:
                print(f"client {client}")
                hn, aliases, ips = socket.gethostbyname_ex(client['host'])
                for ip in ips:
                    if ip in conn_ips:
                        continue
                    for i in range(config['range']):
                        try:
                            port = client['port'] + i
                            s = socket.create_connection((client['host'], port))
                            pn = s.getpeername()
                            con = CursesConn(self, (s, pn))
                            conn_ips[pn[0]] = con
                            break
                        except Exception as ex:
                            logging.debug("exception might indicate missing port", ex)
                            continue
            time.sleep(config['interval'])
        except Exception as ex:
            logging.error("add_clients", ex)


def cursus():
    global thread_pool
    logging.basicConfig(filename='cursus.log', level=logging.DEBUG, filemode='w',
                        format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(funcName)s: %(message)s', )
    read_config()
    with CursesServer() as srv, ThreadPoolExecutor() as tpex:
        thread_pool = tpex
        sl = tpex.submit(srv.listen)
        tpex.submit(srv.add_clients)
        sl.result()
        logging(f"all futures ended")
    print('all done')


if __name__ == "__main__":
    random.seed()
    cursus()
