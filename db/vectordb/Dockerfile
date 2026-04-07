FROM chromadb/chroma:1.5.3

# Keep the project-level persistence path aligned with the current backlog
# and future compose wiring, even though recent Chroma defaults moved to /data.
ENV CHROMA_PERSIST_PATH=/chroma/chroma

VOLUME ["/chroma/chroma"]

# Prepare the image context for later init and collection content.
WORKDIR /chroma
