

# Cloud Object Storage 0.47

Adds adapters for Amazon S3, Azure Blob Storage, Azure Data Lake Storage Gen2 and Google Cloud Storage. Common operations include prefix listing, byte/text read and write, upload/download, deletion, CSV/JSON DataFrame ingestion and optional Parquet ingestion through pyarrow. Provider SDKs remain optional dependencies. Credentials should use provider-standard runtime identity chains rather than committed secrets.


