from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser

# Load the Llama3 model with the updated class
llm = OllamaLLM(model="llama3")


# Function to split text into chunks within the model's context window
def split_text_into_chunks(text, max_token_length):
    """Split text into chunks, each fitting within the model's token limit."""
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
    return chunks


# Function to summarize each chunk and combine the results
def summarize_large_text(text, max_token_length=4096):
    """Summarize a large text by breaking it into chunks."""
    # Step 1: Split the text into manageable chunks
    print("Splitting text into chunks...")
    chunks = split_text_into_chunks(text, max_token_length)

    # Step 2: Summarize each chunk
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        summary_prompt = (
            "Please provide a concise summary of the following text:\n\n" f"{chunk}\n\n" "Summary:"
        )
        print(f"Summarizing chunk {i + 1} of {len(chunks)}...")  # Debug message
        try:
            summary = llm.invoke(summary_prompt)
            if summary:
                chunk_summaries.append(summary.strip())
            else:
                print(f"Warning: No summary returned for chunk {i + 1}.")
        except Exception as e:
            print(f"An error occurred with chunk {i + 1}: {e}")
            chunk_summaries.append("[Error in summarizing chunk]")

    # Step 3: Summarize the combined chunk summaries
    combined_summary_text = "\n\n".join(chunk_summaries)
    print("Creating final summary of the combined chunk summaries...")
    final_summary_prompt = (
        "Please provide a concise summary of the following summarized sections:\n\n"
        f"{combined_summary_text}\n\n"
        "Final Summary:"
    )

    try:
        final_summary = llm.invoke(final_summary_prompt)
        return final_summary if final_summary else "[Final summary could not be generated]"
    except Exception as e:
        print(f"An error occurred during final summarization: {e}")
        return "[Error during final summarization]"


# Example usage
input_text = """
    PHIL-370 Philosophy of Language Professor Welty
ID: 2353896
5/16/2023
On the notion of Linguistic Wholes being prior to their parts
When studying the philosophy of language, the principle of linguistic wholes is an intriguing notion to think about, especially in regard to the parts that make them up, and whether those parts take priority over the wholes they make up or not. The idea that whole linguistic units (such as sentences or utterances) are held prior to their parts (words or components) is known as holism. Beyond being an interesting thought experiment, understanding holism, and holistic structures in language, is important when exploring the meaning of linguistic expressions. To help us explore this subject a bit better, I am utilizing the knowledge and ideas from several thinkers who have formed different stances that deal with holism (directly or indirectly) and the hierarchical structure of language. These thinkers, who I will introduce below, consist of Patanjali, Sabara, Bhartrhari, Locke, Frege, Chomsky, and Zhuangzi.
Patanjali was an ancient Indian philosopher best known for his work on Yoga and the Sutras, the latter being our main point of focus, where he speaks on the nature of words, grammar, and linguistic wholes. He introduces theories on his concept of the "sphota," which refers to the holistic unit of linguistic meaning. According to Patanjali, sphota represents the complete and unifying aspect of language, encompassing the entire sentence or utterance as a meaningful whole.
 Sabara (known as Sabara Swami) was also an Indian philosopher and commentator on the Mimamsa school of Hindu philosophy. His works cover interesting subjects such as the eternality of words and sentences, as well as holism (which is good for us).
Bhartrhari was also an ancient Indian philosopher, as well as a grammarian and poet. He is famous for his work on, and development of, his theory of the sphota, which posits that complete linguistic units hold the primary meaning over their individual parts (relating to holism). In Bhartrhari's view, the understanding of language involves perceiving the unity of the sentence and comprehending the intended meaning of the complete utterance. This implies that linguistic wholes, in terms of complete sentences or discourse, take precedence over their constituent parts in the process of deriving meaning.
John Locke was a 17th-century English philosopher who made large contributions to political theory, epistemology, and philosophy of mind, but he is best known for his ideas on empiricism and social contract theory. Useful to us, he also speaks on Modes and Substances relating to ideas and the combinations thereof.
Gottlob Frege was a German mathematician, logician, and philosopher who is also credited as being the founder of modern analytic philosophy and formal logic. He also postulated that there was something more to meaning than expressions and reference, which he named the sense.
Noam Chomsky is an American linguist, philosopher, cognitive scientist, and political commentator. He is widely recognized as one of the most influential figures in linguistics still living. He has made significant contributions to the study of language

 acquisition, generative grammar, and cognitive aspects of language. He theories also seek to fully integrate linguistics into contemporary science such as biology.
Zhuangzi, also known as Chuang Tzu, was an ancient Chinese philosopher and a central figure in Daoism. His philosophical work, captured in the text "Zhuangzi" (named after him), explores concepts of spontaneity, the unity of opposites, and the pursuit of a harmonious existence in alignment with the Dao. He is arguably most famous for his parable of the “Butterfly Dream” where he questions the distinction between reality and dreams, bringing up bigger questions relating to existence and reality.
With all of our thinkers introduced, we may now attempt to answer the question: Are linguistic wholes prior to their parts? The first to answer this question, I expect, would be Sabara. Much of his philosophy depends on the notion that words are eternal, and from there he makes an obvious connection that words are the main carriers of meaning in regard to communicating:
"[I]n the injunction 'one desiring heaven should perform the Agnihotra', there is not a single Word which expresses the idea that 'heaven results from the performance of the Agnihotra'; this idea is comprehended only from all the three words (a) Agnihotram (b) juhuyats (c) svargakamah, [(c) one desiring heaven (b) should perform (a) the Agnihotra]...[N]o such group of words however is met with in common parlance, on the basis of which usage the meaning of the group could be deduced. Every single word of the group is

 used (in common parlance), and the meanings of these words are eternal; but the group as such is never used in common parlance; hence the meaning of this group (not being eternal) must be either artificial (created) or illusory. . ."
Simplified down, we can confidently say that Sabara believes that the meaning of sentences are derived from the meanings of their component words. That statement seems pretty logically sound, and “makes sense” to most of the people i have introduced it to.
However, Patanjali would probably have some harsh words for Sabara for his interpretation of the carrier of meaning in a sentence. Patanjali’s main argument on the issue of holism is that the sphota is the primary unit of linguistic meaning, and individual words or phonemes derive their meaning from their connection to this larger holistic structure. He suggests that the comprehension of a word depends on understanding its relationship to the whole sentence or context in which it is used. I also speculate Patanjali would argue that sentences represent specific ideas that do not necessarily reflect the sum of the words in the sentence. A small example of this is easy to understand when you look at the sentence “the brown horse runs”. On their own, the words in this sentence have no correlation together, and carry no meaning by themselves that you could attribute to the original sentence without needing every other word, and beyond that, those words must be in the correct order or the meaning they convey is completely different. This makes logical sense to me as well, and the distinction between both Patanjali and Sabara is difficult to grapple with. Ultimately I think what resonates the most from either author is one of Patanjali’s more famous

 quotes: "thing which is one though it resides in many". I would be curious what Sabara would say today when confronted with the notion that the idea of a sentence forms first and the words come together to match the idea.
Something that neither Sabara nor Patanjali really take into account, however, is the actual physical act of communicating language through sound as speech, which Bhartrhari speculates is much more important than they might give credit. When discussing wholes being precedent to their parts, Bhartrhari states that "...the word is apprehended by the mind in which the seed has been sown by the (physical) sounds, and in which ripening (of the speech) has been brought about by the the telling over (of the sounds) (§84)". Here he lays out his argument for the importance of considering the act of speaking and listening (comprehending) when discussing the hierarchy of language. From there he is able to convey his point, which as you’ll see, seems at first to walk the line between both Sabara and Patanjali’s positions, but then solidly sides with Patanjali on the precedence of wholes over parts. When discussing the meaning of sentences, Bhartrhari states that “It (i.e., the meaning of the sentence) is not really localised anywhere in the individual word-meanings or in the aggregate. (Only,) it is apparently divided into the word-meanings (§438)”. This stance appears to give both the sentence and individual words power in the race for meaning. As with Sabara, Bhartrhari agrees that the meaning of a sentence is communicated through the word-meanings, but also like Patanjali, he agrees that the meaning is not localized in the individual words or even the aggregate. From there he seems to step more in line with Patanjali when he puts forward an argument for holism by providing an example of negation that when seen through Sabara’s views, becomes unintelligible:

 “If we recognise na ['no'] as a separate word in the ultimate sense, what does it negate? The sentence Vrkso nasti ['There is no tree'] has a particular negation as its significance. The meaning (of the word vrksa) cannot be considered to be connected in the mind (to the meaning of the particle na), because that would mean the negation of something which exists (§241).”
We can interpret this that If a sentence's meaning were to be made up of parts, as Sabara contends, then a sentence denying that something exists would have nothing to say about that non-existent object, but instead, language users still say something doesn't exist, and that simply does not make sense in the context of Atomism (for our intentions this is the opposite of holism). Bhartrhari Also uses syntax and his insights on semantics to aid his position that wholes are prior to thor parts. He argues that the components of wholes are contextually determined, and that reflection on semantics shows that meanings of wholes aren't sequences of meanings of parts, culminating in his final stance on the subject: “The set-of-relationships (of the word-meanings) which resides in the meaning of the sentence is not localised in any part (of the sentence) (§437).”
Skipping forward a few hundred years, Chomsky, if in the same room as Bhartrhari, may have a go trying to convince Bhartrhari to join Sabara and himself on the side of Atomism. Just as Bhartrhari held an emphasis on semantics and the physicality of language, Chomsky may be most similar in our list of thinkers for his contemporary view of language intersecting the natural sciences, in particular biology.

 Of course, Bhartrhari did not have access to the advances in linguistics and psychology as Chomsky had, but if they were to have a conversation, I believe Chomsky would (after thoroughly catching Bhartrhari up to speed on current scientific literacy) say something akin to his statement below:
“It is reasonable to suppose that in the course of [natural scientific] inquiry, we attempt to construct systems in which well-constructed symbolic objects are intended to pick out objects in the world: molecules, I-languages, and so on...These symbolic systems may well aim towards the Fregean ideal...It is possible that natural language has only syntax and pragmatics; it has a "semantics" only in the sense of "the study of how this instrument, whose formal structure and potentialities of expression are the subject of syntactic investigation, is actually put to use in a speech community", to quote the earliest formulation in generative grammar 40 years ago, influenced by Wittgenstein, Austin and others. (L&N 26-7)”
Chomsky's linguistic framework emphasizes the idea that language is composed of hierarchical structures. He posits that there are deep underlying structures, represented by abstract syntactic rules, which generate the surface structure (the actual sentences we produce and understand). According to Chomsky, the surface structures are derived in whole from the underlying syntactic representations, so while Bhartrhari and Chomsky both speak on underlying structures, Bhartrhari’s stance that the “seed has

 been sown” in regard to sentence meaning may fall victim to Chomsky's view on the internal structures of semantics, and we may have another Atomist in our midst (not that that's a bad thing).
Of course, if all of these thinkers were in a room together, Frege would have probably spoken out by now in support of Patanjali and Bhartrhari, calling out Sabara and Chomsky for their views on Atomism. Frege is a bit all over the place, and would probably make both sides of the argument a bit unhappy, but he holds his own unique view which I think is equally important. While all three of the ancient Indian philosophers agree in part that there are aspects of language that are eternal and timeless, they do not always line up exactly in their assertions, however, Frege would probably get along best with Sabara in that they have somewhat comparable awe for the eternality of words. The only difference being Frege’s unique notion of the sense, which is best described by his quote below:
"A third realm must be recognized. What belongs to this corresponds with ideas, in that it cannot be perceived by the senses, but with things, in that it needs no bearer to the contents of whose consciousness to belong. Thus the thought, for example, which we expressed in the Pythagorean theorem is timelessly true, true independently of whether anyone takes it to be true. It needs no bearer. It is not true for the first time when it is discovered, but is like a

 planet which, already before anyone has seen it, has been in
interaction with other planets." (Frege, "The Thought", p.302)
I am absolutely sure that Sabara and Frege would form a lasting friendship, however, it would be constantly tested, because while this view seems to support a “parts over whole” scenario, Frege does not believe this to be the case, and he would ultimately side with Patanjali and Bhartrhari saying that it is only within the context of an entire sentence that a word acquires its meaning. This is formulated from his famous context principle “An expression has meaning only in a proposition. Every variable can be conceived as a propositional variable.” Another point that Frege is likely to bring up against Sabara and Chomsky is that sometimes the meaning of the sentence is necessary to sort out erroneous uses of words in sentences, which according to Atomism should not happen. Frege argues that sentences are a necessity to understand the meaning and context of words because if you were to replace the entirety of a sentence except for a specific word, the truth or falsity of that statement is completely unpredictable based on the remaining word. This becomes more obvious when you think about it, and sounds eerily similar to Patanjalis notion that while individual words in a sentence may hold valuable information for the overall meaning of the sentence, the words by themselves carry no way to reconstruct the meaning of the sentence by themself. It was as if I gave you the word “chair” and asked if you could reconstruct the sentence “the chair is brown” from the true/false logic (regarding the chair) from the sentence “the chair is moving”.
Moving on to Locke, probably the most ambiguous thinker in our company, he sits in a metaphorical corner far removed from the two sides we’ve seen form in our

 hypothetical philosopher room. As with the three ancient Indian philosophers and Frege, Locke also believes in the eternal nature of linguistics, although just like the rest of them he does not agree necessarily on which specific aspects are eternal. That being said, he concedes that grammatical structure has some kind of counterpart in reality. That is about all he shares in common with the other members, however. Where he differs is his view on what the fundamental carrier of meaning is. On the surface, it seems that he agrees that sentences are the main vessel for meaning above the words that make them up, but then he takes a step back and clarifies that he values some sentences more than others (in regard to being carriers of meaning). He clarifies these sentences as being distinct, saying that non-compound sentences are “the largest expression across the whole of which there's form-matching”, but then goes on to stress the importance that sentences should still relate semantically to the parts that make them up. It seems that Locke believes that there are fundamental ideas that all others are built on but can't get away from the importance of words and their connection to ideas, which becomes evident in his quote below:
“Since all things that exist are only particulars, how come we by general terms; or where find we those general natures they are supposed to stand for? Words become general by being made the signs of general ideas: and ideas become general, by separating from them the circumstances of time and place, and any other ideas that may determine them to this or that particular existence. By this way of abstraction they are made capable of representing more individuals than

 one; each of which having in it a conformity to that abstract
idea, is of that sort.” (III.III.6)
Locke then goes on to state that such complex ideas, whether they be compounded or not, are considered dependent on substances, or are affections thereof.
Last to join our fun Philosopher party is the ancient Chinese philosopher Zhuangzi. Before I go into his stance on the fundamental linguistic unit, I want to say that Zhuangzi is probably the philosopher I agree the most with, not to say that I do not agree with any of the others; I find many of the other thinker’s points intriguing and many of them make sense even if they are contradictory. However, for me, Zhuangzi’s ideas on the matter closely reflect my thoughts while learning about this topic. In his writings, Zhuangzi's perspective implies that linguistic wholes take precedence over their constituent parts. The emphasis in his view is on the overall meaning and intuitive understanding that emerges from the complete linguistic expression, rather than reducing meaning to isolated words or components. In this sense, he is seemingly siding closer with wholism. However, unlike our other philosophers who side with holism, Zhuangzi believes that the linguistic unit of meaning does not lie in the fixed definitions of a sentence, but rather in the dynamic interplay of words, context, and individual perception. For Zhuangzi, language, in general, is a much more metaphysical subject, and thus the carrier unit for meaning also falls under the same notion. In essence, he believes (somewhat vaguely) that grasping a larger picture of linguistics means leaving behind commonly held constructs that, at their best simply label phenomena, and at their worst restrict us from grasping the larger realities of linguistics.

 I feel that I must agree with him based purely on how my view on linguistics becomes a bit clearer when looking through the lens of Zhuangzi’s philosophy. Again, this may simply be because it is the vaguest and least specific viewpoint of our thinkers, but I do feel that there is a somewhat mystical nature about language, one that isn't necessarily specific to humans, but that we are fortunate enough to partake in. Labeling and coming to conclusions about the nature of language of course has its merit and utility in studying both ancient and contemporary literature, so I do concede that my viewpoint is not for everyone, nor is it the most helpful for finding physical truths in language. If I had to choose between holism and Atomism, I would have to side with holism. The notion that wholes are prior to their parts flows smoother in my mind than saying that words are the main carrier of meaning. I agree that words that point out specific objects (as references) may be eternal, but for the communication of ideas, I believe the sentence (utterance is probably a better word since some sentences can be a single word) cannot be broken down into its constituent parts and still carry the same amount of information. Relating to this, I also agree with Locke in that I believe that some sentences have priority over others when conveying information, with that being said I still don't think that words ever have priority over sentences when conveying meaning.

Sources:
Patanjali [300BCE], Mahabhasya, paspasa
Sabara-Bhasya Adhyaya I, Adhikaranas 6 & 7
Bhartrihari [500CE], Vakyapadiya, Canto I
Bhartrihari [500CE], Vakyapadiya, selections from Canto II
Locke, Essay Concerning Human Understanding [1689], Book II, Book III
Frege, "Sense and Reference" and “Letter to Jourdain”
Chomsky, Knowledge of Language
Chomsky, "Language and Nature"
Chuang Tzu [350BCE], Tian Xia 4
Möller, "Zhuangzi's 'Dream of the Butterfly': A Daoist Interpretation"
    """
output = summarize_large_text(input_text, max_token_length=4096)
print(f"\nFinal Summarized Text:\n{output}")
