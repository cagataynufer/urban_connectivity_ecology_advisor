# Urban Connectivity & Ecology Advisor 🌿

**Urban Connectivity & Ecology Advisor** is a modular, multi-agent system built to support advanced decision-making in urban planning and ecological resilience. Designed specifically for **Munich**, the system analyzes complex spatial, environmental, and community-based interactions by simulating collaborative expert agents, each grounded in real planning data, vector retrieval, and structured reasoning.

This repository contains all components necessary to run the system, including:
- Specialized domain agents for ecology, infrastructure, and policy
- A manager to synthesize agent outputs into academic responses
- A self-supervised evaluator for factual and logical consistency
- A memory-aware secretary for persistent learning across sessions

---

## The System

The architecture comprises **six intelligent agents**, each with a distinct responsibility:

### Core Agents

- **Ecology & Land Use Agent**  
  Evaluates biodiversity, green infrastructure, and land-use zoning plans. Returns mitigation strategies with ecological impact justifications.

- **Urban Connectivity & Resilience Agent**  
  Focuses on transport, street networks, and spatial flow. Uses graph metrics (e.g. betweenness, clustering) to highlight intervention points.

- **Community & Policies Agent**  
  Provides social feasibility insights, framing suggestions in the context of policy constraints or public sentiment. Always responds last to shape tone.

### System Agents

- **Manager Agent**  
  Orchestrates the agent pipeline. It decides agent order by comparing the query to vectorized prompt descriptions, gathers responses, and produces a unified academic-style essay response, along with a heatmap of agents.

- **Evaluator Agent**  
  Performs two evaluation passes:  
  1. **Factual Accuracy** using all vectorstores  
  2. **Logical Coherence** for structural and semantic alignment  
  If issues are found, it sends reroute instructions identifying the faulty agent and the correction needed.
  The Evaluator has read-access to **all** domain stores, along with its own.

- **Secretary Agent**  
  Maintains both **short-term (session)** and **long-term memory** using vector embeddings. While it does not contain an LLM, it stores query-response interactions to improve continuity and recall over time.
  The Secretary logs each interaction into a shared memory vectorstore and persists session metadata to TinyDB.

---

## How It Works

1. **Query Dispatching**  
   The Manager checks vector similarity between the user query and agent descriptions to determine a starting agent.

2. **Sequential Reasoning**  
   Each domain agent responds in order, building context step-by-step. The Community Agent always goes last.

3. **Synthesis**  
   The Manager compiles all outputs into a structured final answer, citing source evidence and providing academic justification.

4. **Evaluation**  
   The Evaluator cross-checks the essay:
   - If it passes factual and semantic checks → the result is returned.
   - If any issue is detected → reroute is triggered.

5. **Rerouting Cycle**  
   Evaluation feedback identifies the faulty agent. That agent receives a reroute with updated context and token filters. A new essay is synthesized and re-evaluated. This repeats up to **5 times**.

6. **Retrieval Adaptation**  
   After each failed round, the system increases the agent's `top_p` (nucleus sampling threshold) by `+0.02`, broadening retrieval coverage. This balances strict precision with broader recall in difficult queries. Nucleus sampling is added on top of the greedy search to control for flexibility.

---

## Architecture Details

| Component | Description |
|----------|-------------|
| **LLM** | `mistralai/Mixtral-8x7B-Instruct-v0.1`, loaded in 4-bit with `bitsandbytes` |
| **Embedder** | `intfloat/multilingual-e5-large`, used for all semantic retrieval + truncation |
| **Memory** | ChromaDB vectorstore per agent + separate persistent memory via Secretary |
| **Truncation Engine** | Custom `SemanticTruncator` applies block-wise filtering for context, RAG, and agent prompts |

Agents operate with individually tailored truncation profiles for different sections (agent output, retrievals, final prompt, prior context) and vectorstore connections. 

---

# Data

This system relies on a meticulously curated and semantically embedded dataset stack, all scoped to the city of Munich, and built using both government-grade documents and infrastructure-level graph data.

---

## Government Reports (PDF)

Each domain agent — **Ecology & Land Use**, **Urban Connectivity & Resilience**, and **Community & Policies** — was embedded with vector databases built from a total of **74 official PDF documents**. These were primarily sourced from:

- [muenchen.de](https://muenchen.de)  
- [muenchen-transparent.de](https://muenchen-transparent.de)  
- [stadt.muenchen.de](https://stadt.muenchen.de)

Documents ranged from short reports to over 450-page municipal plans. Extraction was performed using advanced chunking and OCR-aware processing.


Each chunk retained **page and paragraph-level metadata**, and was embedded using the `intfloat/multilingual-e5-large` model. Chunks were then uploaded to Hugging Face and indexed with **ChromaDB**.

- Chunking with Paragraph-Aware Embedding  
- PDF Tables included  
- Metadata includes page + paragraph references  

---

## Urban Graph Dataset: `munich_graph_network`

A custom vector database was built on top of **OpenStreetMap’s graph data** for Munich. Nodes and paths were enriched with:

- **Centrality metrics** (closeness, betweenness, eigenvector, pagerank, etc.)
- **Semantic CoT narratives**, generated using:
  - Randomized tone (technical, narrative, metaphorical, etc.)
  - Perspective (resident, policy, ecology)
  - Keyword focus (zoning, biodiversity, retrofitting, etc.)

The result is a natural language traversal of the city’s infrastructure, capturing not just topological but ecological, emotional, and strategic implications of various urban segments.

- Over 70,000+ CoT entries planned  
- Graph segments narrativized with diverse perspectives  
- Based on shortest-path traversal with embedded commentary  

---

## Long-Term and Session Memory

- All session logs (queries + outputs + evaluations) are stored via **TinyDB**  
- `SecretaryAgent` pushes these logs to Hugging Face as zipped archives (`tinydb_logs.zip`)  
- Vector memory is continuously updated and refreshed every 20 queries  
- Past sessions are used to augment current context retrieval when available  

---

## Dataset Links (Hugging Face)

- Ecology & Land Use: `cagatayn/ecology_land_use`  
- Urban Connectivity & Resilience: `cagatayn/urban`  
- Community & Policies: `cagatayn/community_policies`  
- Evaluator (Critical Reports): `cagatayn/evaluator`  
- Munich Urban Graph Network: `cagatayn/munich_graph_network`

---

## Example

### Query

"Which transit-adjacent zones within Munich could yield the highest combined ecological and commuter benefit if partially de-sealed and retrofitted with biodiversity-supporting infrastructure? Please identify at least three viable sites, estimate the potential reduction in impervious surface area (in %), and explain how this would affect both urban connectivity and climate resilience based on graph metrics and planning constraints."

### Answer

The identified priority zones lie along Isarring between Ostbahnhof station and Brudermühlstraße Bridge [^eco_zone], which currently features wide roads and limited greenery. These areas align well with the objectives set out in our initial prompt. Each proposed site meets multiple criteria for environmental improvement through measures such as micro-habitat creation and vegetation growth support [^urban_connect]. As an added bonus, all chosen locations already contain footpaths suitable for upgrades like cool paving materials and permeable surfaces [^community_feasible]. We can thus anticipate increased urban connectivity thanks to new bicycle lanes and enhanced sidewalk conditions, alongside better heat dissipation due to additional tree coverage and water retention systems [^climate_resiliency].

Our analysis reveals three optimal intervention points, presented below according to their respective scores across ecological impact, network benefits, and implementation feasibility considerations. Note that while some discrepancies exist among individual rankings provided by different specialists involved in this project, overall trends remain consistent throughout (see Table 1).

**Table 1: Priority Zones Ranking**

| Zone   | Ecological Tag Score | Network Benefits Score | Implementation Feasibility Score | Total Numeric Score |
|--------|-----------------------|-------------------------|----------------------------------|----------------------|
| Site A | High                  | Very high               | Medium                           | 78%                 |
| Site B | Moderately high       | High                    | Low                              | 59%                 |
| Site C | Moderately high       | Moderately high         | Moderately high                  | 66%                 |

Site A ranks first given its substantial ecological value coupled with strong positive impacts predicted for transport networks and adaptive capacity improvements. This location corresponds to the segment directly abutting Ostbahnhof's southern entrance, where significant reductions in impervious surface area (-45%) seem achievable without compromising essential traffic flows [^eco_impact]. By implementing nature-based solutions such as rain gardens and native plant species installations here, planners aim to foster healthy ecosystem dynamics supporting local fauna diversity and improved air quality indices [^urban_connect]. Additionally, integrating sustainable drainage techniques promises flood prevention advantages during extreme weather events, thereby enhancing climatic resilience prospects for nearby communities [^climate_resiliency].

Despite slightly inferior ratings compared to Site A, both Sites B and C present promising opportunities worthy of consideration too. At Site B - located near the junction connecting Friedenstrasse and Grafinger Strasse - modest estimated gains in habitat complexity (+15%) should still contribute positively towards regional biodiversity goals over time. Furthermore, boosting accessibility via expanded bike paths stands to alleviate congestion pressures elsewhere around town, fostering more equitable mobility patterns [^community_feasible]. Meanwhile, although facing stiff competition from other options available, Site C offers reasonable compromise outcomes worth pursuing further. Situated adjacent to Brudermühlbrücke bridge, it boasts decent potential for creating miniature wildlife corridors linking fragmented habitats together. Although projected decreases in sealed surfaces hover just below 10%, expected enhancements to thermal comfort levels offer tangible rewards for locals frequenting surrounding streets [^climate_resiliency].

In conclusion, leveraging synergies among various stakeholder perspectives allows us to pinpoint three prime candidates deserving attention moving forward. While varying degrees of uncertainty surround exact figures quoted earlier, consensus emerges regarding general suitability across selected focal areas. To maximize chances of success, city officials ought to emphasize coordinated efforts spanning technical expertise, participatory engagement, and sustained funding commitments going ahead. In doing so, they stand poised to deliver meaningful progress toward twin aims of fostering robust urban ecosystem health and ensuring safe, enjoyable transportation experiences for everyone involved.

[^eco_zone]: Munich Biodiversity Overlay Plan §4.3  
[^urban_connect]: Urban Connectivity Master Report §8.1  
[^community_feasible]: Community Infrastructure Feasibility Study (München Transparent, 2022)  
[^climate_resiliency]: Stadtklima Strategic Action Plan §6.4  
[^eco_impact]: Ecological Retrofit Scenarios for Transit Zones, Technical Addendum B

---

## Setup

This repository is designed for Colab or local Python environments (Python ≥ 3.10) with GPU acceleration.  
It depends on Hugging Face–hosted vector stores, large language models, and several utilities.

### 1. Clone the Repository

```bash
git clone https://github.com/cagataynufer/urban_connectivity_ecology_advisor.git
```

### 2. Install Requirements

Install dependencies listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Authenticate with Hugging Face

This project uses private Hugging Face vector stores and memory logs. You must authenticate before downloading them.

In `main.py`, include:

```python
from huggingface_hub import login
import os

hf_token = os.getenv("HF_TOKEN")  # Set this as an environment variable or replace directly
if hf_token:
    login(token=hf_token)
    print("Logged into Hugging Face.")
else:
    print("Hugging Face token not found. Please set HF_TOKEN in your environment.")
```

Alternatively, in Colab:

```python
from huggingface_hub import login
from google.colab import userdata

hf_token = userdata.get("HF_TOKEN")
login(hf_token)
```

### 4. Run the System

Once everything is set up, test the pipeline with:

```python
from pipeline import execute_full_pipeline

result = execute_full_pipeline("Which road segments in Munich disrupt ecological continuity?")
print(result["essay"])
```

### 5. Vectorstores (Auto-Downloaded)

These will be automatically downloaded using `snapshot_download()`:

- `cagatayn/ecology_land_use`
- `cagatayn/urban`
- `cagatayn/community_policies`
- `cagatayn/evaluator`
- `cagatayn/munich_graph_network`
- `cagatayn/secretary`

---

## Limitations

While this system demonstrates a rich orchestration of multi-agent reasoning and semantic memory, several constraints currently shape its performance:

### 1. Model Constraints

This project uses `mistralai/Mixtral-8x7B-Instruct-v0.1`, one of the most capable open-source models for deep reasoning tasks. However:

- Quantization via `bitsandbytes` (4-bit) is used to fit model loading within Google Colab’s 40GB A100 VRAM limit.
- This compression reduces generation fidelity under high logical or arithmetic complexity.
- Some highly nested prompts may lead to shallow or imprecise outputs due to reduced attention depth under quantized decoding.

### 2. Token Budget Limitations

- Mixtral technically supports up to 32k tokens, but stability significantly declines above ~24k in practice.
- This system operates around **8k–12k tokens** per full prompt (across synthesis, evaluation, memory, and retrieval).
- Expanding token windows for richer memory context is theoretically possible, but impractical under current GPU and runtime limitations.

### 3. Urban Graph Representation

- The sample of the original Munich road network extracted from OpenStreetMap contains over **90,000 nodes** and **110,000+ edges**.
- Due to low semantic diversity in raw graph data, the full graph is not directly embedded.
- Instead, a semantically enriched, narrative-style dataset was constructed, covering **70,000+ Chain-of-Thought (CoT) entries** simulating meaningful paths, metrics, and urban insights.

### 4. Multilingual Embedding Tradeoffs

- Since many planning documents are only available in German, the system uses `intfloat/multilingual-e5-large` as the embedding model.
- This enables robust semantic search across multilingual documents, but may slightly underperform compared to monolingual models in English-only reasoning contexts.

### 5. Resource & Runtime Limits

- The project is run entirely on a **single A100 GPU via Google Colab**.
- There is no distributed inference or multi-GPU setup.
- All agent interactions, vectorstore downloads, memory updates, and rerouting cycles happen within one runtime loop, meaning occasional slowdowns or memory bottlenecks may occur on large queries.

---

## Citations & Data Sources

This system is powered by publicly available planning documents, urban strategies, and ecological development reports published by the City of Munich.

### Key Municipal Sources

- [muenchen.de](https://www.muenchen.de) — official urban planning and green infrastructure initiatives  
- [muenchen-transparent.de](https://www.muenchen-transparent.de) — transparency portal for city development policies and archives  
- [stadt.muenchen.de](https://stadt.muenchen.de) — regional governance and sustainability documentation  

Additional data includes infrastructure zoning maps, ecosystem evaluation guidelines, and mobility policy reports obtained through public PDFs and online government archives.

> This repository is non-commercial and was created solely for academic and research purposes.  
> No commercial use or redistribution of original documents is intended.
