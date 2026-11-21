*This project has been created as part of the 42 curriculum by mel-wahm.*

# Description
RAG system is about creating a pipeline that read some data, split it to chunks, takes in a query and uses mathematical algorithms to retrieve the most related chunks, to then pass to the llm and get an accurate answer.

Before the LLMs like ChatGPT and Claude had access to seaching the Internet, their information would be limited to the day their training had ended, so when new things happen in the world, the LLMs would need to re-train again, which is extremly expensive and takes a lot of time, this is where RAG comes in handy, instead of re-training the model from the beginning, we pass to llm with the desired data that we want to look into.

Even after the LLMs got access to searching the Internet, the RAG system is still helpful, especially in private data, that, first you can not train the model on, for privacy purposes, and can not find online.

My RAG project does those exact same steps, in exactly four stages:

the pipeline has four stages.

1. **Indexing:** the repository is split into chunks of at most 2000
   characters, using one strategy for Python files and another for
   Markdown/text files, and the result is saved under `data/processed/`.
2. **Retrieval:** using the `bm25` algorithm, we retrieve the best chunks
related to our prompt
3. **Augmentation:** the top chunks are added to the prompt .
4. **Generation:** the model writes the answer using that context.

___

