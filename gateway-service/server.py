import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import requests

server = Flask(__name__)

# MongoDB config
server.config["MONGO_URI"] = os.environ.get("MONGO_URI")
mongo_video = PyMongo(server, uri=os.environ.get("MONGO_VIDEO_URI"))
mongo_mp3 = PyMongo(server, uri=os.environ.get("MONGO_MP3_URI"))

fs_video = gridfs.GridFS(mongo_video.db)
fs_mp3 = gridfs.GridFS(mongo_mp3.db)

def validate_token(request):
    if "Authorization" not in request.headers:
        return None, ("missing credentials", 401)

    token = request.headers["Authorization"]
    
    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/validate",
        headers={"Authorization": token}
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)


@server.route("/upload", methods=["POST"])
def upload():
    access, err = validate_token(request)
    if err:
        return err

    if "file" not in request.files:
        return "file required", 400

    file = request.files["file"]

    if file.filename == "":
        return "no file selected", 400

    # store video in MongoDB
    fid = fs_video.put(file)

    # put message in RabbitMQ
    err = to_queue(str(fid), access, os.environ.get("VIDEO_QUEUE"))
    if err:
        fs_video.delete(fid)
        return "internal server error", 500

    return "success!", 200


@server.route("/download", methods=["GET"])
def download():
    access, err = validate_token(request)
    if err:
        return err

    fid = request.args.get("fid")
    if not fid:
        return "fid is required", 400

    try:
        out = fs_mp3.get(ObjectId(fid))
        return send_file(
            out,
            download_name=f"{fid}.mp3",
            mimetype="audio/mpeg"
        )
    except Exception as err:
        return str(err), 500


def to_queue(fid, username, queue):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.environ.get("RABBITMQ_HOST")
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=json.dumps({"video_fid": fid, "username": username}),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ),
    )
    connection.close()
@server.route("/health", methods=["GET"])
def health():
    return "healthy", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)
