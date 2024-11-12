from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain


def summarize_text(input_text: str) -> str:
    # Initialize the Llama 3 model through Ollama
    llm = Ollama(model="llama3")  # Use the appropriate model name for Llama 3 in Ollama

    # Create a prompt template for summarization
    prompt_template = PromptTemplate(
        input_variables=["text"], template="Please summarize the following text:\n\n{text}"
    )

    # Set up the LangChain chain with the LLM and prompt template
    chain = LLMChain(llm=llm, prompt=prompt_template)

    # Run the chain with the input text to get the summary
    summary = chain.run({"text": input_text})
    return summary


# Example usage
input_text = "Your text goes here to be summarized."
print(summarize_text(input_text))
