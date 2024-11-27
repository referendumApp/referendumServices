# import time
# from langchain_ollama import OllamaLLM

# llm = OllamaLLM(model="llama3.1", max_tokens=300)  # Adjust max_tokens for faster processing

# def summarize_text(text):
#     """Summarize the entire text directly if it's short enough."""
#     try:
#         return llm.invoke(f"Summarize:\n{text}").strip()
#     except Exception as e:
#         print(f"Error summarizing text: {e}")
#         return "[Error in summarizing the text]"

# def summarize_large_text(file_path, delineator="•S 4361 PCS"):
#     """Summarize text from a file, optimizing for both small and large inputs."""
#     print("Reading input text...")
#     with open(file_path, "r") as file:
#         text = file.read().strip()

#     # Directly summarize small text
#     if len(text.split()) <= 100:  # Adjust this threshold for "small text"
#         print("Text is small; summarizing directly...")
#         return summarize_text(text)

#     # For larger text, split into chunks and summarize iteratively
#     chunks = text.split(delineator)
#     summaries = [summarize_text(chunk) for chunk in chunks]

#     # Combine all summaries into a final summary
#     final_summary = summarize_text("\n\n".join(summaries))
#     return final_summary

# if __name__ == "__main__":
#     file_path = "/Users/henrydalton/Documents/GitHub/referendumApi/pipeline/shorttest.txt"

#     start_time = time.time()

#     print("Starting summarization...")
#     final_summary = summarize_large_text(file_path)

#     end_time = time.time()
#     elapsed_time = end_time - start_time

#     hours, remainder = divmod(elapsed_time, 3600)
#     minutes, seconds = divmod(remainder, 60)

#     print("\nFinal Summary:\n", final_summary)
#     print(f"\nTime taken: {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds.")


from langchain_ollama import OllamaLLM

llm = OllamaLLM(model="llama3.1", max_tokens=300)


def test_summarization():
    """Test summarizing a simple input."""
    try:
        response = llm.invoke("Summarize:\nhello")
        print("Response:", response)
    except Exception as e:
        print(f"Error during summarization: {e}")


if __name__ == "__main__":
    test_summarization()
