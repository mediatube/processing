# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
import sys

from redis import Redis
from rq import Connection, Worker

from rq_access import *

redis_conn = Redis(host=host, port=port, password=password)
with Connection(redis_conn):
    qs = sys.argv[1:] or ['default']
    w = Worker(qs)
    w.work()
