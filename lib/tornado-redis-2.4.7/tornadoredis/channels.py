import json
from collections import Counter, defaultdict

from tornado import stack_context


class RedisChannels(object):
    """
    A helper class to handle Pub/Sub subscriptions
    using a single redis connection.

    See the SockJS Chat Demo
    """
    def __init__(self, tornado_redis_client):
        self.redis = tornado_redis_client
        self.subscribers = defaultdict(Counter)
        self.subscriber_count = Counter()

    def subscribe(self, channel_name, subscriber, callback=None):
        """
        Subscribes a given subscriber object to a redis channel.
        Does nothing if subscribe calls are nested for the
        same subscriber object.

        The broadcast method of the subscriber object will be called
        for each message received from specified channel.
        Override the on_message method to change this behaviour.
        """
        self.subscribers[channel_name][subscriber] += 1
        self.subscriber_count[channel_name] += 1
        if self.subscriber_count[channel_name] == 1:
            if not self.redis.subscribed:
                if callback:
                    callback = stack_context.wrap(callback)

                def _cb(*args, **kwargs):
                    self.redis.listen(self.on_message)
                    if callback:
                        callback(*args, **kwargs)

                cb = _cb
            else:
                cb = callback
            self.redis.subscribe(channel_name, callback=cb)
        elif callback:
            callback(True)

    def unsubscribe(self, channel_name, subscriber):
        """
        Unsubscribes a subscriber from the redis channel.

        Unsubscribes the redis client from the channel
        if there are no subscribers left.
        """
        self.subscribers[channel_name][subscriber] -= 1
        if self.subscribers[channel_name][subscriber] <= 0:
            del self.subscribers[channel_name][subscriber]
            self.subscriber_count[channel_name] -= 1
            if self.subscriber_count[channel_name] <= 0:
                del self.subscriber_count[channel_name]
                self.redis.unsubscribe(channel_name)

    def on_message(self, msg):
        """
        Handles a message posted to the Redis channel.

        Broadcasts JSON-encoded message to end users using
        the SockJSConnection.broadcast method.

        Override this method if needed.
        """
        if not msg:
            return

        if msg.kind == 'disconnect':
            # Disconnected from the Redis server
            # Close the redis connection
            self.close()
        if msg.kind == 'message':
            # Get the list of broadcasters for this channel
            broadcasters = list(self.subscribers[msg.channel].keys())
            if broadcasters and msg.body:
                broadcasters[0].broadcast(broadcasters, str(msg.body))

    def publish(self, channel_name, data, client=None, callback=None):
        """
        Publishes a message to the redis channel.

        Use a different client instance if you ever need in in application.
        """
        data = json.dumps(data) if data is not None else ''
        (client or self.redis).publish(channel_name, data, callback=callback)

    def close(self):
        """
        Unsubscribes the redis client from all channels.
        Clears subscriber lists and counters.
        """
        for channel_name, subscribers in self.subscriber_count.items():
            if subscribers:
                self.redis.unsubscribe(channel_name)
        self.subscribers = defaultdict(Counter)
        self.subscriber_count = Counter()

    def is_subscribed(self):
        """
        Returns True if subscribed to any channel.
        """
        for channel_name, subscribers in self.subscriber_count.items():
            if subscribers:
                return True
        return False
