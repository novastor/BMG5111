#code partly developed from gpt 
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
import io
import csv
import os
import random
from dotenv import load_dotenv
from langchain.chains import ConversationalRetrievalChain
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
pc_key  =  os.getenv("PINECONE_API_KEY")
HARDCODED_SCAN_ID = 'S' + str(random.randint(0, 9))
HARDCODED_DURATION = (random.randint(15, 60))
HARDCODED_PATIENT_ID =random.randint(0, 9)
HARDCODED_CHECK_IN_DATE = "2025-03-25"
hour =  str(random.randint(0, 23))
minute =  str(random.randint(0, 59))
check_in_time = hour+":"+minute
HARDCODED_CHECK_IN_TIME = check_in_time

def convert_output_to_csv(old_output):
    """
    Convert the old output string used from the old code to work with the optimization script without needing to rewrite both of them(not ideal but time-efficient)

    """
    # Assume the old output is comma-separated, e.g., "Head and Neck,Acute stroke,P1,24,MRI"
    parts = old_output.split(',')
    if len(parts) < 5:
        print("actual length")
        print(len(parts))
        raise ValueError("Expected at least 5 comma-separated values in the old output")
    
    # Extract the required parts
    # Using parts[4] for scan_type (the last value)
    scan_type = parts[4].strip()
    
    # Extract priority from parts[2] and remove non-digit characters 
    priority = ''.join(filter(str.isdigit, parts[2]))
    
    # Create an in-memory CSV string
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(["scan_id", "scan_type", "duration", "priority", "patient_id", "check_in_date", "check_in_time"])
    
    # Write row with mapped and hardcoded values
    writer.writerow([
        HARDCODED_SCAN_ID,
        scan_type,
        HARDCODED_DURATION,
        priority,
        HARDCODED_PATIENT_ID,
        HARDCODED_CHECK_IN_DATE,
        HARDCODED_CHECK_IN_TIME
    ])
    
    return output.getvalue().strip()

def search_with_rag(index_name, input_text):
    
    """
    stateful rag function
    Inputs: string pinecone index name for target and string prompt text.
    Output: Generated CSV string.
    """
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    pc_key  =  os.getenv("PINECONE_API_KEY")
    # Reinitialize chat history if needed
    chat_history = []
    # Setup embeddings and Pinecone vector store
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        pinecone_api_key=pc_key
    )

    # Setup chat model
    chat = ChatOpenAI(verbose=True, temperature=0, model_name="gpt-4o-mini", api_key=api_key)

    qa = ConversationalRetrievalChain.from_llm(
        llm=chat, chain_type="stuff", retriever=vectorstore.as_retriever()
    )

    # Prepare prompt and query the chain
    prompt = (
    "Extract the following information from the provided text: \n"
    "1. Condition location (e.g., head, torso, etc.)\n"
    "2. Condition description\n"
    "3. Severity index (P1, P2, etc.)\n"
    "4. Maximum allowable wait time in hours (as a number)\n"
    "5. Machine type used (e.g., CT, MRI, etc.)\n\n"
    "Format the output exactly as follows, with values separated by commas:\n"
    "location,desc,index,time,mach\n\n"
    "For example:\n"
    "Head,Acute stroke,P1,24,MRI\n\n"
    "Only return the extracted values in this format, with no extra text or explanations.\n"
    "Input text:\n"
    )
    prompt += input_text

    res = qa({"question": prompt, "chat_history": chat_history})
    
    old_output = res["answer"]
    
    # Convert the old output to CSV format
    csv_result = convert_output_to_csv(old_output)
    print("\nCSV Output:")
    print(csv_result)
    print("\nCSV Output complete:")
    
    return csv_result

