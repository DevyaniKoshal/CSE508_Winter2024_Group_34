import torch
from llama_index.core import VectorStoreIndex,SimpleDirectoryReader,ServiceContext
from llama_index.llms.huggingface import HuggingFaceLLM
from llama_index.core.prompts.prompts import SimpleInputPrompt
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
# from llama_index import ServiceContext
from llama_index.core import ServiceContext
# from llama_index.embeddings import LangchainEmbedding
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import socket
import pickle
# Define your system prompt, query wrapper prompt, and documents here
documents=SimpleDirectoryReader("/raid/home/arya20498/ir/flask/data").load_data()
system_prompt="""
You are a Q&A assistant. Your goal is to answer questions as
accurately as possible based on the instructions and context provided.
"""
## Default format supportable by LLama2
query_wrapper_prompt=SimpleInputPrompt("<|USER|>{query_str}<|ASSISTANT|>")

# Set up the query engine
llm = HuggingFaceLLM(
    context_window=4096,
    max_new_tokens=256,
    generate_kwargs={"temperature": 0.0, "do_sample": False},
    system_prompt=system_prompt,
    query_wrapper_prompt=query_wrapper_prompt,
    tokenizer_name="meta-llama/Llama-2-7b-chat-hf",
    model_name="meta-llama/Llama-2-7b-chat-hf",
    device_map="auto"
)
embed_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

service_context = ServiceContext.from_defaults(
    chunk_size=1024,
    llm=llm,
    embed_model=embed_model
)
index = VectorStoreIndex.from_documents(documents, service_context=service_context)
query_engine = index.as_query_engine()

def doc_reload():
    documents=SimpleDirectoryReader("/raid/home/arya20498/ir/flask/data").load_data()
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)
    query_engine = index.as_query_engine()
    return query_engine


# Example usage
# pdf_path = 'path_to_your_pdf.pdf'
# spell_checker = update_spellchecker_with_pdf(pdf_path)
# print("Personal dictionary updated. Total unique words:", len(spell_checker.word_frequency))




# Specify the path to your PDF directory
pdf_directory_path = '/data'



# print(query_engine.query("what is attention"))
# Start a server to listen for queries
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('localhost', 6970))
server_socket.listen(1)

print('Query engine server is listening on localhost:6970')

while True:
    print('Waiting for a connection...')
    connection, client_address = server_socket.accept()
    try:
        print('Connection from', client_address)

        # Receive the query from the client
        header = connection.recv(4)
        expected_length = int.from_bytes(header, byteorder='big')
        query_data = b''
        received_length = 0
        while received_length < expected_length:
            packet = connection.recv(1024)
            query_data += packet
            received_length += len(packet)

        query = query_data.decode()
        print(f'Received query: {query}')
        
        if query=="$file$added$":
            query_engine = doc_reload()
            # update_spellchecker_with_pdf(pdf_directory_path)
            response_str = "success"
        else:
            # Process the query and generate the response
            response_obj = query_engine.query(query)
            sim_q = f"generate 3 relevant queries to the query:{query}"
            sim_obj = query_engine.query(sim_q)
            response_str = str(response_obj)  # Convert the Response object to a string
            sim_str = str(sim_obj)
            response_str+=("$$"+sim_str)
        print(f"response: {response_str}")
        # Send the response back to the client
        response_bytes = response_str.encode()
        header = len(response_bytes).to_bytes(4, byteorder='big')
        data = header + response_bytes
        connection.sendall(data)

    finally:
        connection.close()
