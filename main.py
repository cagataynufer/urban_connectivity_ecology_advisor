# -*- coding: utf-8 -*-
"""main.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1lkl3zEaJ9cGZuz9MjN6H8CIEtawlP6lG
"""

from huggingface_hub import login
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
from core.embedder import E5Embedder
from core.llm_wrapper import DirectLLMWrapper
import uuid
from core.vectorstore import load_chroma_vectorstore
from utils.prompt_loader import load_prompt
from agents.domainagents import DomainAgent
from agents.secretaryagent import SecretaryAgent
from tinydb import TinyDB
from agents.manageragent import ManagerAgent
from agents.evaluatoragent import EvaluatorAgent
from langchain.vectorstores import Chroma as LCChroma
from pipeline import execute_full_pipeline

# Session ID for memory tracking
session_id = str(uuid.uuid4())[:8]

# Add your token here
hf_token = os.environ.get("HF_TOKEN")

if hf_token:
    login(token=hf_token)
    print("Logged into Hugging Face.")
else:
    print("Hugging Face token not found. Please set HF_TOKEN in your environment.")

# Model initialization
model_name = "mistralai/Mixtral-8x7B-Instruct-v0.1"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map={"": "cuda"},
    trust_remote_code=True
)

# Custom E5 Embedder
embedding_model = E5Embedder("intfloat/multilingual-e5-large")

# Urban, Ecology, and Evaluator LLM
llm_main_agents = DirectLLMWrapper(
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=1200,
    temperature=0.67,
    top_p=0.85,
    repetition_penalty=1.1,
    do_sample=True,
    return_full_text=False
)
# Community LLM
llm_community_agent = DirectLLMWrapper(
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=568,
    temperature=0.67,
    top_p=0.85,
    repetition_penalty=1.1,
    do_sample=True,
    return_full_text=False
)

# Manager LLM
llm_manager = DirectLLMWrapper(
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=1500,
    temperature=0.75,
    top_p=0.85,
    repetition_penalty=1.25,
    do_sample=True,
    return_full_text=False
)

# Extracting vectorstore: semantically and contextually enriched Munich graph with metrics (used by ecology + urban)
munich_graph_vs = load_chroma_vectorstore(
    "cagatayn/munich_graph_network",
    embedding_model,
    collection_name="urban_connectivity_agent_cot"
)

# Base vectorstore repo references for each domain agent
vectorstores = {
    "ecology": "cagatayn/ecology_land_use",
    "urban": "cagatayn/urban",
    "community": "cagatayn/community_policies"
}

# Loading prompt templates
ecology_prompt = load_prompt("prompts/ecology_prompt.txt")
urban_prompt = load_prompt("prompts/urban_prompt.txt")
community_prompt = load_prompt("prompts/community_prompt.txt")
manager_prompt = load_prompt("prompts/manager_prompt.txt")
evaluator_prompt = load_prompt("prompts/evaluator_prompt.txt")

domain_agents = {
    "ecology": DomainAgent(
        name="ecology",
        prompt_template=ecology_prompt,
        vectorstore_repo=vectorstores["ecology"],
        llm=llm_main_agents,
        embedding_model=embedding_model,
        tokenizer = tokenizer,
        truncation_profiles=TRUNCATION_PROFILES,
        extra_vectorstores=[munich_graph_vs]
    ),
    "urban": DomainAgent(
        name="urban",
        prompt_template=urban_prompt,
        vectorstore_repo=vectorstores["urban"],
        llm=llm_main_agents,
        embedding_model=embedding_model,
        tokenizer = tokenizer,
        truncation_profiles=TRUNCATION_PROFILES,
        extra_vectorstores=[munich_graph_vs]
    ),
    "community": DomainAgent(
        name="community",
        prompt_template=community_prompt,
        vectorstore_repo=vectorstores["community"],
        llm=llm_community_agent,
        embedding_model=embedding_model,
        tokenizer = tokenizer,
        truncation_profiles=TRUNCATION_PROFILES,
        extra_vectorstores=[]
    )
}

# Initializing memory manager
secretary = SecretaryAgent(
    repo_id="cagatayn/secretary",
    embedder=embedding_model
)

# Pulling latest memory logs
secretary.pull_latest_tinydb_log()
os.makedirs(os.path.dirname(secretary.tinydb_log_path), exist_ok=True)

# Shared DB for Manager & Evaluator to log into
shared_db = TinyDB(secretary.tinydb_log_path)

evaluator = EvaluatorAgent(
    llm=llm_main_agents,
    vectorstore_repo="cagatayn/evaluator",
    retriever_k=30,
    embedding_model=embedding_model,
    agents=domain_agents,
    domain_prompt=evaluator_prompt,
    vectorstores={k: v.vectorstore for k, v in domain_agents.items()},
    db=shared_db,
    tokenizer=tokenizer,
    truncation_profiles=TRUNCATION_PROFILES
)

manager = ManagerAgent(
    llm=llm_manager,
    prompt_template=manager_prompt,
    agents=domain_agents,
    evaluator=evaluator,
    embedding_model=embedding_model,
    db=shared_db,
    session_id=session_id,
    tokenizer=tokenizer,
    truncation_profiles=TRUNCATION_PROFILES
)

# RAG continuity between sessions
wrapped_memory_vectorstore = LCChroma(
    persist_directory=secretary.local_path,
    embedding_function=embedding_model
)

for agent in manager.agents.values():
    agent.memory_vectorstore = wrapped_memory_vectorstore
    agent.session_memory_vectorstore = wrapped_memory_vectorstore
)

if __name__ == "__main__":
    query = (
        "Which transit-adjacent zones within Munich could yield the highest combined ecological and commuter benefit if partially de-sealed and retrofitted with biodiversity-supporting infrastructure? Please identify at least three viable sites, estimate the potential reduction in impervious surface area (in %), and explain how this would affect both urban connectivity and climate resilience based on graph metrics and planning constraints."
    )

    result = execute_full_pipeline(
        user_query=query,
        manager=manager,
        evaluator=evaluator,
        secretary=secretary,
        shared_db=shared_db,
        max_retries=5
    )

    # Main Essay
    print("\n Final Essay:\n" + "="*60)
    print(result["essay"])

    # Evaluation
    print("\n🔍 Evaluation Summary:\n" + "="*60)
    print("Passed:", result["passed"])
    print("Retries:", result["retries"])
    print("Evaluation Details:", result["evaluations"]["final_logic_result"][:500] + "...")
    print("Evaluation Details (factual):", result["evaluations"]["final_factual_result"][:500] + "...")

    # 🪪 Session ID
    print("\n Session ID:", result["session_id"])