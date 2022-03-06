#!/bin/env python
import time
from concurrent.futures.thread import ThreadPoolExecutor


def testRun(msg):
    for i in range(3):
        print(f"from {msg}")
        time.sleep(2)


with ThreadPoolExecutor(max_workers=512) as tpe:
    for i in range(10):
        tpe.submit(testRun, f"bg job {i}")
    time.sleep(20)
