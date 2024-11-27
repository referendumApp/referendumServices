import os
import time
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.1", max_tokens=300)  # Adjust max_tokens for faster processing

CACHE_DIR = "cache"


def split_text_by_delineator(text, delineator):
    """Split text into chunks using a specified delineator."""
    return [
        delineator + chunk if i > 0 else chunk for i, chunk in enumerate(text.split(delineator))
    ]


def get_cached_summary(chunk):
    """Retrieve or generate a cached summary for a chunk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    hash_key = hashlib.md5(chunk.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{hash_key}.json")

    if os.path.exists(cache_path):
        with open(cache_path, "r") as file:
            return json.load(file)

    summary = summarize_chunk(chunk)
    with open(cache_path, "w") as file:
        json.dump(summary, file)
    return summary


def summarize_chunk(chunk):
    """Summarize a single chunk."""
    try:
        return llm.invoke(f"Summarize:\n{chunk}").strip()
    except Exception as e:
        print(f"Error summarizing chunk: {e}")
        return "[Error in summarizing this chunk]"


def batch_chunks(chunks, batch_size=4):
    """Group chunks into larger batches."""
    for i in range(0, len(chunks), batch_size):
        yield "\n\n".join(chunks[i : i + batch_size])


def batch_summarize(chunks, max_workers=16, batch_size=4):
    """Summarize chunks with batching and caching."""
    print(f"Summarizing {len(chunks)} chunks with caching and batching...")
    batched_chunks = list(batch_chunks(chunks, batch_size))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        summaries = list(executor.map(get_cached_summary, batched_chunks))
    print(summaries)
    return summaries


def consolidate_summaries(summaries):
    """Consolidate all summaries into a single summary."""
    print("Consolidating summaries...")
    try:
        combined_text = "\n\n".join(summaries)
        return llm.invoke(f"Summarize:\n{combined_text}").strip()
    except Exception as e:
        print(f"Error in final summarization: {e}")
        return "\n\n".join(summaries)


def summarize_large_text(file_path, delineator="•S 4361 PCS", max_workers=16, batch_size=4):
    """Optimized summarization for large text."""
    print("Reading input text...")
    with open(file_path, "r") as file:
        text = file.read()

    chunks = split_text_by_delineator(text, delineator)

    summaries = batch_summarize(chunks, max_workers=max_workers, batch_size=batch_size)

    final_summary = consolidate_summaries(summaries)

    return final_summary


if __name__ == "__main__":
    file_path = "/Users/henrydalton/Documents/GitHub/referendumApi/pipeline/testmore.txt"

    start_time = time.time()

    print("Starting summarization...")
    final_summary = summarize_large_text(file_path, max_workers=16, batch_size=16)

    end_time = time.time()
    elapsed_time = end_time - start_time

    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    print("\nFinal Summary:\n", final_summary)
    print(f"\nTime taken: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")
