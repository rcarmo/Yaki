"""
Simple message queue.

Messages are scheduled and processed in a single worker thread spawned
from the main process.  Thus, events are enqueued asynchronously, but
processed in a linear fashion.

"""
import time
import sched
from Queue import Queue, Empty
from threading import Thread


def delay_put(duration, queue, message):
    time.sleep(duration)
    queue.put(message)

def run_scheduler(scheduler):
    scheduler.run()

class Scheduler(sched.scheduler):
    def __init__(self, queue, handler, timeout):
        self.message_queue = queue
        self.handler = handler
        self.timeout = timeout
        sched.scheduler.__init__(self, time.time, self.delay)

    def delay(self, duration):
        queue = self.message_queue
        if duration > 0:
            # Spawn a process that will sleep, enqueue None, and exit.
            Thread(target=delay_put, args=(duration, queue, None)).start()
        try:
            message = queue.get(True, duration + self.timeout) # Block!
        except Empty:
            self.timed_out()
        else:
            if message is not None:
               # A message was enqueued during the delay.
                timestamp = message.get('timestamp', self.timefunc())
                priority = message.get('priority', 1)
                self.enterabs(timestamp, priority, self.handler, (message,))

    def timed_out(self):
        print "Timed out."

    def startup(self):
        print "Starting scheduler!"

    def shutdown(self):
        print "Scheduler done."

    def run(self):
        # Schedule the `startup` event to trigger `delayfunc`.
        self.enter(0, 0, self.startup, ())
        sched.scheduler.run(self)
        self.shutdown()

class MessageQueue(object):
    def __init__(self, handler, timeout=10, scheduler_class=Scheduler):
        self.queue = Queue()
        self.scheduler = scheduler_class(self.queue, handler, timeout)
        self.worker = None

    def enqueue(self, message):
        self.queue.put(message)
        if not self.working():
            self.start_worker()

    def start_worker(self):
        self.worker = Thread(target=run_scheduler, args=(self.scheduler,))
        self.worker.start()

    def working(self):
        return self.worker is not None and self.worker.isAlive()
