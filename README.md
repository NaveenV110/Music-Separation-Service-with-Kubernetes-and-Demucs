# Music Separation Service

This project is a scalable, cloud-native music separation service designed to separate audio tracks (vocals, bass, drums, and other) from MP3 files using the [Demucs](https://github.com/facebookresearch/demucs) model, with deployments managed through Kubernetes and Google Kubernetes Engine (GKE).

## Architecture

### Components
- **Rest-server Deployment**: Receives MP3 files, generates a unique hash for each file, and enqueues it in Redis. MP3 files are stored in MinIO buckets, with logs sent to Redis under a "logging" key.
- **Redis Deployment**: Manages the workflow by:
  - Storing song hashes in the `toWorkers` list for processing
  - Centralizing logs from the rest-server and worker-server deployments.
- **Worker-server Deployment**: Monitors Redis for new song hashes, retrieves MP3 files from MinIO, processes them using Demucs, and saves separated tracks (vocals, bass, drums, other) back to MinIO.
- **Logs Deployment**: Fetches logs from Redis and enables log monitoring through `kubectl logs` commands.
- **MinIO Deployment**: Object storage for MP3 files, set up via Helm with Bitnami’s MinIO chart.

### Namespaces
- **default**: Primary namespace for the main services.
- **minio-ns**: Dedicated namespace for MinIO.

### Services and Configuration
- **default namespace**:
  - **Rest-server**: Exposed as a NodePort service.
  - **Redis**: Cluster IP.
  - **MinIO**: External name to communicate across namespaces.
  - **Logs**: No service (access via `kubectl logs`).
  - **Worker**: No service (direct communication with Redis and MinIO).
- **minio-ns**:
  - **MinIO**: Cluster IP service for object storage access.

### Process Flow
1. **File Upload**: The rest-server receives an MP3 file, generates a hash, and stores the file in MinIO. It adds the hash to Redis's `toWorkers` list.
2. **Task Processing**: Worker-server pods monitor the `toWorkers` list, retrieve files from MinIO when a hash appears, process the files with Demucs, and save the separated tracks back to MinIO.
3. **Log Management**: Logs from both the rest-server and worker-server are centralized in Redis, viewable via the `Logs` pod with `kubectl`.