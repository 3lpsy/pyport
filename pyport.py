#!/usr/bin/env python3
import argparse
import threading
from threading import Thread, Lock
from queue import Queue
import requests
import time
import socket
from random import shuffle

print_lock = Lock()

protos = {
    'tcp': socket.SOCK_STREAM,
    'udp': socket.SOCK_DGRAM
}

class Worker(Thread):
    """ Thread executing tasks from a given tasks queue """
    def __init__(self, queue, verbose=0):
        Thread.__init__(self)
        self.verbose = verbose
        self.queue = queue
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.queue.get()
            if self.verbose > 4:
                print("[*] worker: getting task from queue", args)
            try:
                if self.verbose > 4:
                    print("[*] worker: executing task from queue", args)
                func(*args, **kargs)
            except Exception as e:
                if self.verbose > 4:
                    print("[*] worker: error occurred in task", args)
            if self.verbose > 4:
                print("[*] worker: mark task as done", args)
            self.queue.task_done()

class ThreadPool:
    """ Pool of threads consuming tasks from a queue """
    def __init__(self, num_threads, verbose=0):
        self.verbose = verbose
        self.queue = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.queue, verbose)

    def add_task(self, func, *args, **kargs):
        """ Add a task to the queue """
        self.queue.put((func, args, kargs))

    def map(self, func, args_list, **kwargs):
        """ Add a list of tasks to the queue """
        for args in args_list:
            self.add_task(func, args, **kwargs)

    def wait_completion(self):
        """ Wait for completion of all the tasks in the queue """
        self.queue.join()



# The threader thread pulls an worker from the queue and processes it

class ScanManager(object):

    def __init__(self, verbose=0):
        self.open = []
        self.errors = []
        self.verbose = verbose

    def handler(self, port, target, proto="tcp", timeout=30, verbose=False):
        if self.verbose > 2:
            print('[*] handler: attempting', target, port)


        if proto in protos:
            s = socket.socket(socket.AF_INET, protos[proto])
            s.settimeout(timeout)

        try:
            if proto == 'tcp':
                con = s.connect((target, port))
            elif proto == 'udp':
                data = 'HELP'.encode()
                if self.verbose > 2:
                    print("[*] handler: sending data")
                s.sendto(data, (target,port))
                res = s.recvfrom(1024)
                if self.verbose > 1:
                    print("[*] handler: received", res)
            elif proto == 'http':
                res = requests.get('http://{}:{}'.format(target, port), timeout=timeout)
                if self.verbose > 1:
                    print("[*] handler: received", res)
            elif proto == 'https':
                requests.packages.urllib3.disable_warnings()
                res = requests.get('https://{}:{}'.format(target, port), timeout=timeout, verify=False)
                if self.verbose > 1:
                    print("[*] handler: received", res)
            else:
                raise Exception("Invalid Protocol")
            with print_lock:
                print("[!!!] open:", port)
                self.open.append(port)
            con.close()
        except socket.timeout as e:
            with print_lock:
                if self.verbose > 2:
                    print("[!] handler: error", port, type(e))
                self.errors.append(e)

        except requests.exceptions.ConnectTimeout as e:
            with print_lock:
                if self.verbose > 2:
                    print("[!] handler: error", port, type(e))
                self.errors.append(e)

        except Exception as e:
            with print_lock:
                if self.verbose > 1:
                    print("[!] handler: interesting error", port, type(e))
                self.errors.append(e)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', type=str, required=True, help="desired target (ip)")
    parser.add_argument('-m', '--min-port', type=int, default=1, help="min port (range)")
    parser.add_argument('-M', '--max-port', type=int, default=65535, help="max port (range)")
    parser.add_argument('-T', '--threads', type=int, default=10, help="do you want to go fast?")
    parser.add_argument('--timeout', type=int, default=10, help="set timeout")
    parser.add_argument('--verbose', '-v', action='count',default=0, help="verbosity (-v, -vv, -vvv, -vvvv)")
    parser.add_argument('--no-random', action="store_true", default=False, help="don't randomize port order")
    parser.add_argument('-P', '--proto', type=str, default="tcp", choices=['tcp', 'udp', 'http', 'https'], help="protocol")
    parser.add_argument('-p', '--port',nargs='+', type=str, default=None, required=False, help="ports (-p 1 2 3, -p 1-5, or -p 1,2,3)")

    args = parser.parse_args()

    target = args.target

    if not args.port:
        ports = list(range(args.min_port, args.max_port + 1))
    else:
        ports = []
        specified_ports = list(args.port)
        for p in specified_ports:
            more_ports = []
            if '-' in p:
                port_split = p.split('-')
                print(port_split)
                if len(port_split) > 2:
                    raise Exception("Port format incorrect. {} in ".format(p, str(specified_ports)))
                _min = int(port_split[0])
                _max = int(port_split[1]) + 1
                more_ports = list(range(_min, _max))
            elif ',' in p:
                if p.endswith(','):
                    raise Exception("Port format incorrect. Canot end in comma. {} in ".format(p, str(specified_ports)))
                for _p in p.split(','):
                    more_ports.append(int(_p))
            else:
                _p = int(p)
                more_ports.append(_p)
            ports = ports + more_ports

    if not args.no_random:
        shuffle(ports)

    threads = args.threads
    if threads > len(ports):
        threads = len(ports) - 1 if len(ports) > 1 else 1

    proto = args.proto

    timeout = args.timeout
    verbose = int(args.verbose)

    manager = ScanManager(verbose=verbose)

    print("[*] pyport starting")
    print("[*] target", target)
    if len(ports) < 11:
        print("[*] ports", ports)
    else:
        print("[*] ports", len(ports), 'total')
    print("[*] protocol", proto)
    print("[*] threads", str(threads))
    print("[*] timeout", timeout)
    print("[*] verbosity", verbose)

    pool = ThreadPool(threads, verbose=verbose)
    pool.map(manager.handler, ports, target=target, proto=proto, timeout=timeout, verbose=verbose)

    pool.wait_completion()

    if verbose > 2:
        print('[=>] errors:', len(manager.errors), 'total')
        for e in manager.errors:
            print('[==>]', e)

    print('[=>] open ports:', len(manager.open), 'total')
    for p in manager.open:
        print('[==>]', p)
