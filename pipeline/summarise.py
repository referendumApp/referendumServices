# 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
# input_text = "the basics of the following test are to actually run a program to see if its possible to integrate a bill summariser to the main pipeline so that at the end of the pipeline, each bill object will have a 'brief' column with a summary of the bill"

from langchain_huggingface import HuggingFaceEndpoint
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

# Set up Hugging Face API token (replace 'your_hf_api_token' with your actual token)
hf_api_token = (
    "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"  # Replace this with your actual Hugging Face API token
)

# Initialize the LLaMA-2 model from Hugging Face
llama_model_id = "meta-llama/Llama-2-7b"  # Example: use the 7b version

# Create a HuggingFaceEndpoint with the correct parameters
llm = HuggingFaceEndpoint(
    repo_id=llama_model_id,  # Specify the repo ID of the model
    task="summarization",  # Task for the HuggingFace model
    model_kwargs={"hf_api_token": hf_api_token},  # Correctly passing the API token
)

# Define a prompt template for summarization
prompt = PromptTemplate(
    input_variables=["text"], template="Summarize the following text:\n\n{text}\n\nSummary:"
)

# Create an LLM chain for summarization
chain = LLMChain(llm=llm, prompt=prompt)


# Function to summarize text
def summarize_text(input_text):
    summary = chain.run(input_text)
    return summary


# Test the function with a sample input
if __name__ == "__main__":
    input_text = "the basics of the following test are to actually run a program to see if its possible to integrate a bill summariser to the main pipeline so that at the end of the pipeline, each bill object will have a 'brief' column with a summary of the bill"
    summary = summarize_text(input_text)
    print("Summary:", summary)
