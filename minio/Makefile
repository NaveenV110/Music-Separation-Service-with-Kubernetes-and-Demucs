# Makefile for MinIO Helm Deployment

# Define variables for the Helm release
NAMESPACE=minio-ns
RELEASE_NAME=minio-proj
CONFIG_FILE=./minio/minio-config.yaml
CHART=bitnami/minio

# Default target to install MinIO
install:
	helm install -f $(CONFIG_FILE) -n $(NAMESPACE) --create-namespace $(RELEASE_NAME) $(CHART)

# Optional target to uninstall MinIO
uninstall:
	helm uninstall -n $(NAMESPACE) $(RELEASE_NAME)

# Target to upgrade MinIO
upgrade:
	helm upgrade -f $(CONFIG_FILE) -n $(NAMESPACE) $(RELEASE_NAME) $(CHART)

# Target to display status of the MinIO deployment
status:
	helm status -n $(NAMESPACE) $(RELEASE_NAME)