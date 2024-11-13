import os
import json
import redis
import platform
import sys
from minio import Minio
from minio.error import S3Error
from time import sleep

# Redis configuration
redis_host = "redis"
redis_port = 6379
redis_queue = "toWorkers"

# Define logging keys based on the platform
info_key = "{}.worker.info".format(platform.node())
debug_key = "{}.worker.debug".format(platform.node())

def log_debug(message, key=debug_key):
    print("DEBUG:", message, file=sys.stdout)
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
    redis_client.lpush('logging', f"{key}:{message}")

def log_info(message, key=info_key):
    print("INFO:", message, file=sys.stdout)
    redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)
    redis_client.lpush('logging', f"{key}:{message}")

def get_minio_client():
    return Minio(
        "minio:9000",
        access_key="rootuser",
        secret_key="rootpass123",
        secure=False
    )

# Bucket and directory configuration
# Bucket and directory configuration
bucket_name = "audio-tracks"
input_dir = "/tmp/input"
output_dir = "/tmp/output"
model_name = "mdx_extra_q"

def separate_tracks(songhash):
    input_path = f"{input_dir}/{songhash}.mp3"
    demucs_command = f"python -m demucs.separate --out {output_dir} --mp3 {input_path}"
    log_info(f"Running DEMUCS command: {demucs_command}")
    result = os.system(demucs_command)

    if result == 0:
        log_info(f"Separation successful for {songhash}")
        return True
    else:
        log_debug(f"Failed to separate tracks for {songhash}")
        return False

def upload_tracks_to_minio(songhash):
    minio_client = get_minio_client()
    parts = ['bass', 'drums', 'vocals', 'other']
    for part in parts:
        track_path = f"{output_dir}/{model_name}/{songhash}/{part}.mp3"
        if os.path.exists(track_path):
            minio_client.fput_object(
                bucket_name,
                f"{songhash}/{part}.mp3",
                track_path
            )
            log_info(f"Uploaded {part} track to Min.io for song {songhash}")
        else:
            log_debug(f"Track {part} for song {songhash} does not exist in {output_dir}")

def main():
    # Initialize Redis connection
    redis_conn = redis.Redis(host=redis_host, port=redis_port, db=0)
    log_info("Worker server started and connected to Redis")

    while True:
        message = redis_conn.blpop(redis_queue, timeout=5)
        sleep(5)
        if message:
            _, message_data = message
            message_data = json.loads(message_data)
            songhash = message_data['songhash']
            
            object_path = f"{songhash}/original.mp3"
            log_info(f"Checking if object {object_path} exists in bucket {bucket_name}...")

            try:
                minio_client = get_minio_client()
                minio_client.fget_object(bucket_name, object_path, f"{input_dir}/{songhash}.mp3")
                log_info(f"Downloaded {songhash}.mp3 from Min.io")
            except S3Error as e:
                log_debug(f"Error retrieving object from Min.io: {e}")
                continue
            
            if separate_tracks(songhash):
                upload_tracks_to_minio(songhash)
            else:
                log_debug(f"Separation failed for {songhash}")
        else:
            log_info("No messages in the queue, waiting...")
            sleep(5)

if __name__ == "__main__":
    main()