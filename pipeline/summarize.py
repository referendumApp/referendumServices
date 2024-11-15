from langchain_ollama import OllamaLLM
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load the Llama3 model
llm = OllamaLLM(model="llama3")


# Function to split text into chunks within the model's context window
def split_text_into_chunks(text, max_token_length):
    """Split text into chunks, each fitting within the model's token limit."""
    print("Starting to split text into chunks...")
    chunks = []
    current_chunk = ""
    for paragraph in text.split("\n\n"):
        if len(current_chunk) + len(paragraph) < max_token_length:
            current_chunk += paragraph + "\n\n"
        else:
            chunks.append(current_chunk)
            current_chunk = paragraph + "\n\n"
    if current_chunk:
        chunks.append(current_chunk)
    print(f"Total chunks created: {len(chunks)}")
    return chunks


def summarize_chunk(chunk):
    """Summarize a single chunk of text."""
    summary_prompt = (
        "Please provide a concise summary of the following text:\n\n" f"{chunk}\n\n" "Summary:"
    )
    print("Sending a chunk to the model for summarization...")
    try:
        summary = llm.invoke(summary_prompt)
        print("Chunk summarized successfully.")
        return summary
    except Exception as e:
        print(f"An error occurred during summarization: {e}")
        return "[Error in summarizing chunk]"


def summarize_large_text_parallel(file_path, max_token_length=4096, max_workers=4):
    """Summarize large text from a file using parallel processing for chunks and combine into a single summary."""

    # Read input text from file
    print("Reading input text from file...")
    with open(file_path, "r") as file:
        text = file.read()

    # Split the text into manageable chunks
    print("Starting the parallel summarization process...")
    chunks = split_text_into_chunks(text, max_token_length)
    chunk_summaries = []

    # Use ThreadPoolExecutor for parallel summarization of chunks
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_chunk = {executor.submit(summarize_chunk, chunk): chunk for chunk in chunks}

        for i, future in enumerate(as_completed(future_to_chunk), start=1):
            try:
                result = future.result()
                if result:
                    chunk_summaries.append(result.strip())
                    print(
                        f"Chunk {i} summarized: {result[:60]}..."
                    )  # Display the first 60 chars of summary
                else:
                    print(f"Warning: No summary returned for chunk {i}.")
            except Exception as e:
                print(f"An error occurred with chunk {i}: {e}")

    # Combine all chunk summaries into one text for the final summary
    combined_summary_text = "\n\n".join(chunk_summaries)
    print("Creating a single final summary of all summarized chunks...")

    final_summary_prompt = (
        "Please provide a single, concise summary of the following summarized sections:\n\n"
        f"{combined_summary_text}\n\n"
        "Final Summary:"
    )
    try:
        final_summary = llm.invoke(final_summary_prompt)
        print("Final summary created successfully.")
        return final_summary if final_summary else "[Final summary could not be generated]"
    except Exception as e:
        print(f"An error occurred during final summarization: {e}")
        return "[Error during final summarization]"


# Example usage
file_path = "/Users/henrydalton/Documents/GitHub/referendumApi/pipeline/test more.txt"  # Path to the input text file
print("Starting summarization process...")
output = summarize_large_text_parallel(file_path, max_token_length=4096, max_workers=4)
print(f"\nFinal Summarized Text:\n{output}")
