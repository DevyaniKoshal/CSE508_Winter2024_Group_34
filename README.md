# CSE508 Winter2024: Information Retrieval
## Group 34

### Book Summarizer and QnA ChatBot

#### Baseline
Meta Llama-7B and Microsoft Phi 2. The experiments were performed on Tesla V100-PCIE-32GB with a batch size of 1 due to memory constraints. We trained both the models for 2 epochs using a subset of the dataset (~1000 chapters). 

Fine-tuning such large-scale models is prohibitively expensive given the large-scale data size and number of parameters. This further motivates us to work towards building a RAG-based summarizer by passing the fine-tuning step.

The scripts are available in the Baselines folder.

#### Proposed Method
Retrieval Augemented Generation
This method leverages two components: a Retriever and a Generator. The Retriever extracts relevant passages from a knowledge base (in this case, built from books) based on the input document. The Generator then uses these retrieved passages to create a summary that adheres to the model's token limit, eliminating the need for fine-tuning for each new document. This approach is particularly suitable for long documents.

![image](https://github.com/DevyaniKoshal/CSE508_Winter2024_Group_34/assets/114855347/d5732a0b-fe40-4b16-ad0b-481b645873c0)

Further enhancements have been done by incorporating the following techniques:
1. Time-Weighting
2. Ensemble Technique

Relevant scripts are present in the LangChain directory.

#### Web UI
We created a web-interface for the model using Flask where users can upload their books through Google Drive links and interact with the system for both question answering and summarization functionalties. Users can upload books for on-demand summarization.

The code for this is available in the chatbot directory.


#### Commands to run the website
1. Clone the github repository.
2. Install the dependecies in the requirements.txt file.
3. Parallely run python backend.py and python app.py.
4. Follow the link.

#### Mid Review - Vector database created using Llama Index
#### LangChain - RAG impleemented using LangChain
