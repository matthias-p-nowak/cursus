#!/bin/env python
import logging
import pickle
import random
import signal
import socket
import sys
import threading
import time
from typing import List, Any

import yaml

config = {}
my_id: int = 0
peers = {}
local_sock: socket.socket
threads = list()
running = True


class Connection:
    def __init__(self, sock: socket.socket):
        global peers
        self.sock = sock
        self.host, port = sock.getpeername()
        self.fd = sock.makefile("rwb")
        data = {'iam': my_id}
        pickle.dump(data, self.fd)
        self.fd.flush()
        peers[self.host] = self

    def serve(self):
        try:
            while True:
                obj = pickle.load(self.fd)
                print(f"got an object {obj}")
                if 'iam' in obj:
                    peer_id = obj['iam']
                    print(f"got id {peer_id}")
                    if peer_id == my_id:
                        self.close()
                        return
        except pickle.UnpicklingError:
            logging.error(f"connection failed to host {self.host}")
            self.close()

    def close(self):
        global peers
        if self.fd is not None:
            self.fd.close()
            self.fd = None
        if self.sock is not None:
            self.sock.close()
            self.sock = None
        peers.pop(self.host)

    def start(self):
        t = threading.Thread(target=self.serve)
        t.name = self.host
        threads.append(t)
        t.start()



def shutdown(*args):
    global peers, local_sock, threads, running
    logging.info(f"shutting down due to signal {args}")
    running = False
    local_sock.close()
    for k, c in peers:
        c.close()
    for t in threads:
        t.cancel()
    logging.info("all threads shut down")


def run_server():
    global my_id, local_sock, threads
    my_id = random.getrandbits(256)
    try:
        port = -1
        for i in range(config['range']):
            try:
                port = config['port'] + i
                local_sock = socket.create_server(('', port))
                break
            except OSError:
                continue
        if local_sock is None:
            logging.error(f"could not create local port")
            sys.exit(1)
        logging.info(f"opened port {port}")
        local_sock.listen(32)
        while True:
            sock, addr = local_sock.accept()
            logging.debug(f"added connection to {addr}")
            conn = Connection(sock)
            conn.start()
    except Exception as ex:
        logging.warning(f"exception in server listening {ex}")
    finally:
        if local_sock is not None:
            local_sock.close()


def connect_peers():
    for client in config['peers']:
        try:
            hn, aliases, ips = socket.gethostbyname_ex(client['host'])
            for ip in ips:
                if ip in peers:
                    print(f"jumping over {client}-{ip}")
                    continue
                for i in range(config['range']):
                    try:
                        port = client['port'] + i
                        s = socket.create_connection((client['host'], port))
                        conn=Connection(s)
                        conn.start()
                    except OSError as ex:
                        continue


        except Exception as ex:
            logging.waring(f"hostname {client}",ex)


def cursus():
    global config
    args = sys.argv
    logging.info(f"config from {args}")
    if len(args) < 2:
        print(f"run {args[0]} <config>")
        sys.exit(1)
    with open(args[1]) as inp:
        config = yaml.safe_load(inp)
    signal.signal(signal.SIGINT, shutdown)
    t = threading.Thread(target=run_server)
    t.name = 'running server'
    threads.append(t)
    t.start()
    time.sleep(0.1)
    while running:
        connect_peers()
        time.sleep(config['interval'])
    logging.info("cursus ended")


if __name__ == "__main__":
    logging.basicConfig(filename='cursus.log', level=logging.DEBUG, filemode='w',
                        format='%(asctime)s [%(levelname)s] %(pathname)s:%(lineno)d %(funcName)s: %(message)s', )
    random.seed()
    cursus()
    logging.info("all done")
