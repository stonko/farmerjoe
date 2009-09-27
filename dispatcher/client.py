from eventlet import api
from amqplib import client_0_8 as amqp
import simplejson as json

class ClientMessageQueue(object):
        def __init__(self, user):
                self.__queue = "client." + user
                conn = amqp.Connection(host="localhost:5672 ", userid="guest", password="guest", virtual_host="/",insist=False)
                self.__chan = conn.channel()
                self.__chan.exchange_declare(exchange="ex", type="topic", durable=False, auto_delete=True)
                self.__chan.queue_declare(queue=self.__queue, durable=False,exclusive=False, auto_delete=True)
                self.__chan.queue_bind(queue=self.__queue, exchange="ex", routing_key= "depth")

                print("registered " + user)

        def listen(self, req):
                msgs = []
                msg = self.__chan.basic_get(queue=self.__queue)
                while msg is None:
                        api.sleep()
                        msg = self.__chan.basic_get(queue=self.__queue)

                while msg is not None:
                        msgs.append(msg.body)
                        self.__chan.basic_ack(msg.delivery_tag)
                        msg = self.__chan.basic_get(queue=self.__queue)

                req.write("[" + ",".join(msgs) + "]")

__client_queues__ = {}

def login(msg):
        # authenticate
        print msg["user"] + " logged in"

	# find uid
	uid = msg["user"]

	# bind to mq if needed
	client = "/comet/client/" + uid
        if not (client in __client_queues__):
                __client_queues__[client] = ClientMessageQueue(msg["user"])

        return json.dumps({"uid": uid})

def handle(req):
	if req.path() in __client_queues__:
		__client_queues__[req.path()].listen(req)
	else:
		req.error(401)