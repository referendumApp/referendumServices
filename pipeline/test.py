from langchain_ollama import OllamaLLM  # Updated import
from langchain_core.output_parsers import StrOutputParser

# Load the Llama3 model with the updated class
llm = OllamaLLM(model="llama3")


# Function to summarize the entire text with explicit instructions
def summarize_text(text):
    """Summarize the entire text with clearer instructions for the model."""
    summary_prompt = (
        "Please provide a concise summary of the following text:\n\n" f"{text}\n\n" "Summary:"
    )
    print("Sending the text to the model for summarization...")  # Debug message

    try:
        summary = llm.invoke(summary_prompt)

        # Check if the summary was received
        if not summary or summary.strip() == text.strip():
            print("Warning: No summary was returned or the model returned the input text.")
            return "[No summary returned or model output was identical to input]"
        else:
            return summary

    except Exception as e:
        print(f"An error occurred: {e}")
        return "[Error during summarization]"


# Run the summarization process on a given string
input_text = input(
    """
    The development of artificial intelligence has revolutionized many fields, 
    from healthcare to transportation. Machine learning algorithms can now recognize 
    patterns in medical images with high accuracy, potentially detecting diseases 
    earlier than human doctors. In transportation, AI is enabling the development 
    of self-driving cars, which promise to make roads safer and reduce traffic 
    congestion. However, these advances also raise important ethical questions 
    about privacy, accountability, and the future of human work. As AI continues 
    to evolve, society must carefully consider how to harness its benefits while 
    addressing potential risks and challenges.
    """
)
output = summarize_text(input_text)
print(f"\nSummarized Text:\n{output}")
