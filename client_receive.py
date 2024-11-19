from confluent_kafka import Consumer, KafkaError, Producer
import json

class EmojiStreamViewer:
    def __init__(self, broker='localhost:9092', emoji_stream_topic='emoji_stream_topic', registration_topic='registration_topic'):
        self.broker = broker
        self.emoji_stream_topic = emoji_stream_topic  # Subscribe to emoji_stream_topic instead of cluster1
        self.registration_topic = registration_topic
        self.consumer = None
        self.producer = Producer({'bootstrap.servers': self.broker})  # Producer to send data to clients
        self.registered_clients = set()
        self.load_registered_clients()

    def load_registered_clients(self):
        """Load registered clients from the registration topic."""
        consumer = Consumer({
            'bootstrap.servers': self.broker,
            'group.id': 'client-check-consumer-group',
            'auto.offset.reset': 'earliest'
        })
        consumer.subscribe([self.registration_topic])

        print("Loading registered clients...")
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                break
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    continue

            try:
                registration_data = json.loads(msg.value().decode('utf-8'))
                client_id = registration_data.get("client_id")
                if client_id:
                    self.registered_clients.add(client_id)
            except Exception as e:
                print(f"Error processing registration: {e}")

        consumer.close()
        print(f"Loaded {len(self.registered_clients)} registered clients.")

    def start_stream(self):
        """Start listening to the emoji stream topic and forward the data to registered clients."""
        if not self.registered_clients:
            print("[ERROR] No registered clients found.")
            return

        print("[INFO] Starting emoji stream for registered clients...")

        self.consumer = Consumer({
            'bootstrap.servers': self.broker,
            'group.id': f'{self.emoji_stream_topic}-client-group',
            'auto.offset.reset': 'latest'
        })
        self.consumer.subscribe([self.emoji_stream_topic])

        try:
            while True:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"Consumer error: {msg.error()}")
                        continue

                try:
                    cluster_data = json.loads(msg.value().decode('utf-8'))
                    emoji_type = cluster_data.get("emoji_type")
                    scaled_count = int(cluster_data.get("scaled_count", 0))
                    if emoji_type and scaled_count > 0:
                        emoji_stream = emoji_type * scaled_count
                        print(f"Forwarding emoji stream to registered clients: {emoji_stream}")

                        # Forward emoji data to each registered client
                        for client_id in self.registered_clients:
                            self.send_data_to_client(client_id, emoji_stream)
                except Exception as e:
                    print(f"Error processing cluster data: {e}")

        except KeyboardInterrupt:
            print("\n[INFO] Stopping emoji stream.")
        finally:
            self.consumer.close()

    def send_data_to_client(self, client_id, emoji_stream):
        """Send emoji stream data to a specific registered client."""
        # This can be done in multiple ways depending on how clients are connected (e.g., WebSockets, REST, etc.)
        # For simplicity, we'll just simulate the action with a print statement
        print(f"Sending to client {client_id}: {emoji_stream}")
        # In a real scenario, you would send the emoji_stream to the client here.
        # Example: self.producer.produce(client_topic, json.dumps({"client_id": client_id, "emoji_stream": emoji_stream}).encode('utf-8'))

    def stop(self):
        """Stop the viewer."""
        if self.consumer:
            self.consumer.close()

if __name__ == '__main__':
    viewer = EmojiStreamViewer()
    viewer.start_stream()
