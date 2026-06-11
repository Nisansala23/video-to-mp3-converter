import pika, os, gridfs
from pymongo import MongoClient
from convert import start

def main():
    # MongoDB connections
    client_video = MongoClient(os.environ.get("MONGO_VIDEO_URI"))
    client_mp3 = MongoClient(os.environ.get("MONGO_MP3_URI"))

    db_video = client_video.videos
    db_mp3 = client_mp3.mp3s

    fs_video = gridfs.GridFS(db_video)
    fs_mp3 = gridfs.GridFS(db_mp3)

    # RabbitMQ connection
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST")
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=os.environ.get("VIDEO_QUEUE"), durable=True)

    def callback(ch, method, properties, body):
        err = start(body, fs_video, fs_mp3, channel)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"),
        on_message_callback=callback
    )

    print("Waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
