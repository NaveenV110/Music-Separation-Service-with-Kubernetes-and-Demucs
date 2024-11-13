from flask import Flask, request, jsonify, send_file, abort
import redis
import base64
import hashlib
import io
from minio import Minio
from minio.error import S3Error
import json

app = Flask(__name__)


# Configure Redis connection
redis_client = redis.StrictRedis(
    host='redis',  # Port-forwarded Redis on localhost
    port=6379,
    db=0
)

# Configure Min.io connection
minio_client = Minio(
    'minio:9000',  # Port-forwarded Min.io on localhost
    access_key='rootuser',  # Replace with actual Min.io access key
    secret_key='rootpass123',  # Replace with actual Min.io secret key
    secure=False
)
bucket_name = "audio-tracks"

# Ensure Min.io bucket exists
try:
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
    print("Connected to Min.io and ensured 'audio-tracks' bucket exists.")
except S3Error as e:
    print(f"Failed to connect to Min.io or create bucket: {e}")

# Helper function to generate a unique identifier for each song
def generate_songhash(data):
    return hashlib.sha256(data.encode()).hexdigest()

# Route to process and queue work for waveform separation
@app.route('/apiv1/separate', methods=['POST'])
def separate():
    try:
        data = request.get_json()
        if not data or 'mp3' not in data:
            return jsonify({'error': 'Invalid input data'}), 400

        songhash = generate_songhash(data['mp3'])
        mp3_data = base64.b64decode(data['mp3'])

        # Prepare a JSON message for the worker with songhash and optional callback URL
        message = {
            "songhash": songhash
        }

        # Store the JSON message in Redis list 'toWorkers'
        redis_client.rpush('toWorkers', json.dumps(message))

        # Upload the MP3 file to Min.io using songhash as the filename
        try:
            minio_client.put_object(
                bucket_name,
                f"{songhash}/original.mp3",
                io.BytesIO(mp3_data),
                length=len(mp3_data),
                content_type="audio/mpeg"
            )
            print(f"Uploaded MP3 data to Min.io with songhash {songhash}.")
        except S3Error as e:
            print(f"Failed to upload MP3 to Min.io: {e}")
            return jsonify({'error': 'Failed to store MP3 in Min.io', 'details': str(e)}), 500

        # Optional callback execution (if provided)
        callback = data.get('callback')
        if callback:
            # Note: Callback implementation would go here if required
            print(f"Callback specified: {callback}")

        return jsonify({'songhash': songhash}), 200

    except Exception as e:
        print(f"Unexpected error in /apiv1/separate: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Route to retrieve all queued songhashes
@app.route('/apiv1/queue', methods=['GET'])
def get_queue():
    try:
        queue_entries = redis_client.lrange('toWorkers', 0, -1)
        decoded_entries = [entry.decode('utf-8') for entry in queue_entries]
        return jsonify(decoded_entries), 200
    except redis.RedisError as e:
        print(f"Error retrieving from Redis list 'toWorkers': {e}")
        return jsonify({'error': 'Failed to retrieve queue', 'details': str(e)}), 500

# Route to retrieve a specific track file as a binary download
@app.route('/apiv1/track/<songhash>/<track>', methods=['GET'])
def get_track(songhash, track):
    track_path = f"{songhash}/{track}.mp3"
    try:
        # Download the track from Min.io and serve it as a binary download
        data = minio_client.get_object(bucket_name, track_path)
        return send_file(
            io.BytesIO(data.read()),
            mimetype="audio/mpeg",
            as_attachment=True,
            download_name=f"{track}.mp3"
        )
    except S3Error as e:
        print(f"Failed to retrieve {track} for songhash {songhash} from Min.io: {e}")
        return jsonify({'error': 'Track not found'}), 404

# Route to remove a specific track from Min.io
@app.route('/apiv1/remove/<songhash>/<track>', methods=['DELETE'])
def remove_track(songhash, track):
    track_path = f"{songhash}/{track}.mp3"
    try:
        minio_client.remove_object(bucket_name, track_path)
        print(f"Removed track {track} for songhash {songhash} from Min.io.")
        return jsonify({'status': 'Track removed successfully'}), 200
    except S3Error as e:
        print(f"Failed to remove {track} for songhash {songhash} from Min.io: {e}")
        return jsonify({'error': 'Track not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
