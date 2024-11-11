from transformers import pipeline


def summarize_text(text, max_length=130, min_length=30):
    """
    Summarize the given text using a pre-trained model.
    """
    # Initialize the summarization pipeline
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

    # Generate summary
    summary = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    return summary[0]["summary_text"]


# Example usage
if __name__ == "__main__":
    text = """
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
    print("\nSummarizing")
    result = summarize_text(text)
    print("\nOriginal text:")
    print(text)
    print("\nGenerated summary:")
    print(result)
