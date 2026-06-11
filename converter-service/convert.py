import pika, json, tempfile, os
from bson.objectid import ObjectId
import gridfs
from moviepy.editor import VideoFileClip


def start(message, fs_video, fs_mp3, channel):
    message = json.loads(message)

    # get video from MongoDB
    tf = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    out = fs_video.get(ObjectId(message["video_fid"]))
    tf.write(out.read())
    tf.close()

    # convert video to mp3
    audio = VideoFileClip(tf.name).audio
    tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(tf_path)

    # store mp3 in MongoDB
    with open(tf_path, "rb") as f:
        data = f.read()
        fid = fs_mp3.put(data)

    # cleanup temp files
    os.remove(tf.name)
    os.remove(tf_path)

    # send message to notification queue via new connection
    message["mp3_fid"] = str(fid)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST")
        )
    )
    new_channel = connection.channel()
    new_channel.queue_declare(queue=os.environ.get("MP3_QUEUE"), durable=True)
    new_channel.basic_publish(
        exchange="",
        routing_key=os.environ.get("MP3_QUEUE"),
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ),
    )
    connection.close()
    print(f"MP3 message sent to queue! fid: {str(fid)}")
