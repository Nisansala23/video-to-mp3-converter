import json


def send_email(message):
    message = json.loads(message)
    print(f"MP3 ready! fid: {message['mp3_fid']} for user: {message.get('username', 'unknown')}")
    print(f"Download with: /download?fid={message['mp3_fid']}")
