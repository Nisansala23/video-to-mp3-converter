import pika, os
from notify import send_email


def main():
    # RabbitMQ connection
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST")
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=os.environ.get("MP3_QUEUE"), durable=True)

    def callback(ch, method, properties, body):
        err = send_email(body)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE"),
        on_message_callback=callback
    )

    print("Waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
