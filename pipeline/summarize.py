import time
import os
from langchain_ollama import OllamaLLM

# Initialize the Ollama LLM
llm = OllamaLLM(model="llama3.1", max_tokens=300)  # Adjust max_tokens for faster processing


def summarize_text(text):
    """Summarize the entire text directly if it's short enough."""
    try:
        return llm.invoke(f"Summarize:\n{text}").strip()
    except Exception as e:
        print(f"Error summarizing text: {e}")
        return "[Error in summarizing the text]"


def summarize_large_text(file_path, delineator="•S 4361 PCS"):
    """Summarize text from a file, optimizing for both small and large inputs."""
    print("Reading input text...")
    with open(file_path, "r") as file:
        text = file.read().strip()

    # Directly summarize small text
    if len(text.split()) <= 100:  # Adjust this threshold for "small text"
        print("Text is small; summarizing directly...")
        return summarize_text(text)

    # For larger text, split into chunks and summarize iteratively
    chunks = text.split(delineator)
    summaries = [summarize_text(chunk) for chunk in chunks]

    # Combine all summaries into a final summary
    final_summary = summarize_text("\n\n".join(summaries))
    return final_summary


def log_average_time(file_name, avg_time):
    """Log the average time to a file, creating it if necessary."""
    with open(file_name, "a") as log_file:
        log_file.write(f"Average Time: {avg_time:.2f} seconds\n")


if __name__ == "__main__":
    file_path = "/Users/henrydalton/Documents/GitHub/referendumApi/pipeline/testmore.txt"
    log_file_name = "summarization_times.txt"

    # Check if the log file exists; create if not
    if not os.path.exists(log_file_name):
        with open(log_file_name, "w") as file:
            file.write("Summarization Average Times Log\n")
            file.write("=" * 40 + "\n")

    total_elapsed_time = 0
    runs = 10

    print(f"Executing summarization {runs} times...")

    for run in range(runs):
        start_time = time.time()

        print(f"Run {run + 1}...")
        summarize_large_text(file_path)

        end_time = time.time()
        elapsed_time = end_time - start_time
        total_elapsed_time += elapsed_time

        print(f"Run {run + 1} completed in {elapsed_time:.2f} seconds.")

    # Calculate average time
    average_time = total_elapsed_time / runs
    print(f"\nAverage Time for {runs} runs: {average_time:.2f} seconds.")

    # Log average time to the file
    log_average_time(log_file_name, average_time)
    print(f"Average time logged in {log_file_name}.")
