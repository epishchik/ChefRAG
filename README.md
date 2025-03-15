# ChefRAG
## Installation
```bash
poetry install
```

## Parser
Paste your ScrapeOPS API key into `.env` file.
```bash
SCRAPEOPS_API_KEY=
```

Parse recipes links (duplicates).
```bash
PYTHONPATH=. python3 parser/recipes_pages.py
```

Delete duplicates and sort recipes links.
```bash
PYTHONPATH=. python3 parser/unique_recipes.py
```

Parse each recipe using links.
```bash
PYTHONPATH=. python3 parser/recipes_texts.py
```

## Vectorize chunks
Step 1: clean parsed texts.
```bash
PYTHONPATH=. python3 chunks/clean_texts.py
```

Step 2: create chunks dataframe, for example, using `chunks/create_chunks.py` scripts.
```bash
PYTHONPATH=. python3 chunks/create_chunks.py
```

Step 3: vectorize chunks.
```bash
PYTHONPATH=. python3 chunks/vectorize_chunks.py
```

## Upload dataset to HuggingFace Hub
**NOTE: you should choose different repository name.**

Add your huggingface write access token into `.env` file.
```bash
HF_TOKEN=
```

Upload dataset to hub.
```bash
PYTHONPATH=. python3 utils/push_to_hf_hub.py
```

## Ollama
### Build
Docker build for MacOS cpu. Follow [guide](https://ollama.com/blog/ollama-is-now-available-as-an-official-docker-image).

Step 1: Pull docker image.
```bash
docker pull ollama/ollama:0.5.11
```

Step 2: Run docker container.
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama:0.5.11
```

Step 3: Pull models.
```bash
docker exec -it ollama ollama pull hf.co/bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M
docker exec -it ollama ollama pull bge-m3:567m-fp16
```

### Documentation
- Full API documentation is [here](https://github.com/ollama/ollama/blob/main/docs/api.md).
- OpenAI compability guide is [here](https://ollama.com/blog/openai-compatibility).

## Qdrant
### Build
Docker build. Follow [guide](https://qdrant.tech/documentation/guides/installation/#docker).

Step 1: Pull docker image.
```bash
docker pull qdrant/qdrant:v1.13.3
```

Step 2: Run docker container.
```bash
docker run -d \
  -p 6333:6333 \
  -p 6334:6334 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  --name qdrant \
  qdrant/qdrant:v1.13.3
```

## ChatBot
Preparation: You need to have `chunks.parquet` and `embeddings.mmap` files from "Vectorize chunks" section.

Step 1: Start containers using docker compose.
```bash
docker compose up -d
```

Step 2: Pull ollama models.
```bash
docker exec -it ollama ollama pull hf.co/bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M
docker exec -it ollama ollama pull bge-m3:567m-fp16
```

Step 3: Upload chunks, choose collection name carefully because later it'll be used as workspace name.
```bash
PYTHONPATH=. python3 qdrant/upload.py --collection-name chefrag
```

Step 4: Open AnythingLLM UI at `localhost:3001` and create workspace called `chefrag`.
**NOTE: it's important to have name of workspace same as collection in qdrant, because otherwise it won't find collection.**

Step 5: Just chat with LLM.

## Benchmarking
### Cosine similarity
Define ground truth text and question, after that get answers from LLM / RAG-LLM. Calculate cosine similarity between ground truth and LLM, ground truth and RAG-LLM, compare values. It's expected that for RAG-LLM cosine similarity will be higher if your questions require knowledge from specific documents.

Example dataset preparation shown in `notebooks/human_picked_dataset.ipynb`.

Use this script to get LLM and RAG-LLM metric values using `BAAI/bge-multilingual-gemma2` embeddings.
```bash
PYTHONPATH=. python3 benchmark/ragllm_vs_llm.py --process-raw-df
```

#### Results
Metrics presented in table were calculated using `hf.co/bartowski/Qwen2.5-3B-Instruct-GGUF:Q4_K_M` as ChatBot LLM and `bge-m3:567m-fp16` as embedder for retrieval. LLM temperature was set to 0.2 and maximum number of retrieved chunks was 4.

We've tested 3 different chunking methods:
1. Chunk is a full recipe (RAG_LLM_1).
2. Chunk is either ingredient list or recipe steps (RAG_LLM_2).
3. All kinds of chunks: title, description, ingredients, recipe parts (RAG_LLM_3).

However, we always pass the same full recipe to the LLM context, different chunking strategies affect only the retrieval part.

| Approach      | Cosine similarity |
|:-------------:|:-----------------:|
| LLM           |  0.1271           |
| **RAG_LLM_1** |  **0.1821**       |
| RAG_LLM_2     |  0.1480           |
| RAG_LLM_3     |  0.1624           |
