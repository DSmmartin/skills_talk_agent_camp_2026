---
id: INF-04
name: ChromaDB Dockerfile and Persistent Volume
epic: Epic 1 - Infrastructure and Data
status: [x] Done
summary: Create the ChromaDB container baseline with persistent storage for vector data.
---

# INF-04 - ChromaDB Dockerfile and Persistent Volume

- Epic: Epic 1 - Infrastructure and Data
- Priority: P0
- Estimate: S
- Status: [x] Done
- Source: [PRODUCT_BACKLOG.md](/Users/mmartin/projects/skills_talk_agent_camp_2026/PRODUCT_BACKLOG.md#L614)

## Objective

Create the ChromaDB container baseline for the demo so the vector database can be built consistently and retain embedded documents across restarts.

## Description

This task defines the ChromaDB infrastructure baseline for Epic 1. Its purpose is to establish the local image definition and persistence target for the vector store that will hold schema documents and Q&A examples used by the RAG flow.

The task should stay limited to the container and storage foundation. It should prepare the `db/vectordb/` build context for the later vector seed task without absorbing embedding logic, collection content, or service orchestration responsibilities.

## Scope

- Create the ChromaDB image definition under `db/vectordb/`.
- Use the official ChromaDB image strategy for the local demo setup.
- Define the expected persistent data location used by the container.
- Prepare the `db/vectordb/` build context for later `init/` and `collections/` content.
- Keep the task compatible with later compose-based service wiring and vector seeding.

## Out Of Scope

- Seeding ChromaDB with schema documents or Q&A examples.
- Creating embedding logic or OpenAI integration.
- Wiring the ChromaDB service into `docker-compose.yml`.
- Implementing ClickHouse or MLflow infrastructure.
- Writing migration-aware RAG content updates.
- Running cross-platform cold-start validation.

## Deliverables

- A ChromaDB Dockerfile at `db/vectordb/Dockerfile`.
- A defined persistent storage target for ChromaDB data, expected to map to `/chroma/chroma`.
- A prepared `db/vectordb/` build context that supports later `init/` and `collections/` additions without rework.
- A backlog task artifact at `backlog/INF-04.md` that records the task scope, expected output, and status.

## Acceptance Criteria

- `db/vectordb/Dockerfile` exists and is intended to build the local ChromaDB service image.
- The Dockerfile is based on the official ChromaDB image strategy described in the product backlog.
- The persistent data location for ChromaDB is explicit and compatible with later named-volume wiring.
- The task does not absorb vector seeding, embedding logic, or compose orchestration responsibilities.
- The folder structure created by this task is compatible with follow-up tasks `INF-05` and `INF-07`.

## Dependencies

- `INF-00` completed so Epic 1 scope and boundaries are already defined.
- Product decision to use ChromaDB as the vector database for the demo.
- Later vector seeding in `INF-05` and compose wiring in `INF-07`.

## Assumptions

- The implementation will use the official ChromaDB Docker image as the base layer.
- Persistent storage will be mounted through Docker Compose in a later task rather than fully wired here.
- The local demo environment remains Docker-first on macOS and Linux.
- ChromaDB data persistence should align with the compose plan path `/chroma/chroma`.

## Verification

Procedure used to verify the task against a live ChromaDB container:

1. Build the local ChromaDB image from `db/vectordb/`.
2. Create a Docker volume for persistent ChromaDB data.
3. Start a live container from the built image with the project persistence path mounted at `/chroma/chroma`.
4. Inspect the container logs to confirm Chroma reports `Saving data to: /chroma/chroma`.
5. Inspect the runtime environment and filesystem to confirm `CHROMA_PERSIST_PATH=/chroma/chroma` and that `chroma.sqlite3` is created in that directory.
6. Inspect `/proc/net/tcp` inside the container to confirm the service is listening on port `8000`.

Commands used:

```bash
docker build -t skills-talk-chromadb:inf04 db/vectordb
docker volume create skills-talk-chromadb-data
docker run -d --name skills-talk-chromadb-live -p 8001:8000 -v skills-talk-chromadb-data:/chroma/chroma skills-talk-chromadb:inf04
docker logs skills-talk-chromadb-live
docker exec skills-talk-chromadb-live sh -lc 'printf "%s\n" "$CHROMA_PERSIST_PATH" && test -d /chroma/chroma && ls -la /chroma/chroma'
docker exec skills-talk-chromadb-live sh -lc 'grep -i ":1F40" /proc/net/tcp /proc/net/tcp6 || true'
```

Expected verification result:

- The ChromaDB image builds successfully from `db/vectordb/Dockerfile`.
- A live container starts successfully from the built image.
- Chroma saves data under `/chroma/chroma`.
- The runtime environment exposes `CHROMA_PERSIST_PATH=/chroma/chroma`.
- The persistent directory contains Chroma state files such as `chroma.sqlite3`.
- The server is listening on container port `8000`.

## Notes

- Created on 2026-04-07 as the next Epic 1 task after `INF-03`.
- Completed on 2026-04-07.
- Implemented `db/vectordb/Dockerfile` plus placeholder folders for `init/`, `collections/schema_docs/`, and `collections/qa_examples/`.
- Used the official `chromadb/chroma:1.5.3` base image.
- Explicitly set `CHROMA_PERSIST_PATH=/chroma/chroma` to preserve the project’s planned volume path even though current Chroma defaults have moved to `/data`.
- Verified against a live ChromaDB container named `skills-talk-chromadb-live`.
