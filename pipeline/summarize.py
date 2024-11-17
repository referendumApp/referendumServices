from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3")


def split_text_into_chunks(text, max_token_length):
    """Split text into chunks efficiently."""
    print("Splitting text into manageable chunks...")
    chunks, current_chunk = [], []
    current_length = 0
    max_chunk_length = max_token_length - 512

    for paragraph in text.split("\n\n"):
        paragraph_length = len(paragraph)
        if current_length + paragraph_length < max_chunk_length:
            current_chunk.append(paragraph)
            current_length += paragraph_length
        else:
            chunks.append("\n\n".join(current_chunk))
            current_chunk = [paragraph]
            current_length = paragraph_length

    if current_chunk:
        chunks.append("\n\n".join(current_chunk))

    print(f"Total chunks created: {len(chunks)}")
    return chunks


def summarize_chunks_with_context(chunks):
    """Summarize text chunks iteratively with context."""
    print("Summarizing chunks iteratively to build context...")
    context = ""
    final_summary = ""

    for i, chunk in enumerate(chunks):
        prompt = f"Previous summary: {context}\n\nSummarize this chunk with the previous context:\n{chunk}"
        try:
            summary = llm.invoke(prompt)
            context = summary.strip()
            final_summary += f"\n\n{context}"
        except Exception as e:
            print(f"Error summarizing chunk {i}: {e}")
            final_summary += "\n\n[Error in summarizing this chunk]"

    return final_summary.strip()


def summarize_large_text_with_context(file_path, max_token_length=4096):
    """Summarize large text using iterative summarization with context."""
    print("Reading input text...")
    with open(file_path, "r") as file:
        text = file.read()

    chunks = split_text_into_chunks(text, max_token_length)
    print("Summarizing chunks with context...")

    final_summary = summarize_chunks_with_context(chunks)
    print("Final summary generated.")
    return final_summary


file_path = "/Users/henrydalton/Documents/GitHub/referendumApi/pipeline/testmore.txt"

print("Starting summarization...")
final_summary = summarize_large_text_with_context(file_path, max_token_length=4096)
print("\nFinal Summary:\n", final_summary)
