# When MCP is Boosted by NVIDIA AgentIQ and NIM's Super Power ⚡🧠

This project is an advanced AI-powered application that integrates multiple cutting-edge technologies to create a more dynamic, context-aware, and powerful conversational experience.

## 🚀 Overview

At the core of this stack is **Anthropic MCP (via FastMCP)** and **GPT-4o-mini**, orchestrated with **LangGraph**, and presented via a **Streamlit frontend**. We've supercharged it with **NVIDIA's AgentIQ Workflow** and **NIM Inference Microservice**, bringing in the power of reasoning with **NVIDIA’s Llama3 Nemotron Super 49B** model (R1 version).

### 🔌 Tech Stack

- **🧠 NVIDIA AgentIQ** – Agentic workflow framework with tool-use capabilities
- **📦 NVIDIA NIM** – Model deployment and inference microservice
- **🦙 NVIDIA Llama3 49B R1** – `nvidia/llama-3_3-nemotron-super-49b-v1`
- **🤖 Anthropic MCP** – Powered by FastMCP
- **🔄 GPT-4o-mini** – As the orchestration model
- **🔗 LangGraph** – Graph-based LLM orchestration for tool-calling agents
- **🌐 Streamlit** – For interactive frontend UI
- **📈 LangFuse** – Monitoring and observability for LLM apps

---

## 💡 Features

- Natural and dynamic reasoning with large-scale NVIDIA models
- Tool-using agents enabled by LangGraph and AgentIQ
- Lightweight frontend for chat interaction
- Easy deployment using `aiq` CLI
- Real-time LLM monitoring and observability with LangFuse

---

## ⚙️ Setup & Usage

1. **Run AgentIQ Workflow**
   ```bash
   aiq run --config_file workflow.yaml --input "List five subspecies of Aardvarks"
