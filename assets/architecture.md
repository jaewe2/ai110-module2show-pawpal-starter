# PawPal+ System Architecture Diagram

Export this Mermaid diagram to PNG using https://mermaid.live and save it as `assets/architecture.png`.

```mermaid
flowchart TD
    User(["👤 Pet Owner"])

    subgraph UI["Streamlit UI — app.py"]
        A["Owner / Pet / Task Input"]
        B["Schedule View\n& Conflict Warnings"]
        C["🤖 AI Advisor Panel\n(Analyse / Suggest)"]
    end

    subgraph Core["Core Logic — pawpal_system.py"]
        D["Owner · Pet · Task\ndata classes"]
        E["Scheduler\ngenerate_plan()\ndetect_conflicts()\nsort_by_time()"]
    end

    subgraph AILayer["AI Layer — ai_agent.py"]
        F["KnowledgeBase\n(RAG Retriever)\nkeyword overlap scoring"]
        G["PawPalAgent\n5-step agentic workflow"]
    end

    subgraph KB["knowledge_base/"]
        H["dogs.md"]
        I["cats.md"]
        J["general.md"]
        K["medical.md"]
    end

    subgraph External["External"]
        L["Anthropic Claude API\nclaude-opus-4-7"]
    end

    subgraph Eval["Reliability & Evaluation"]
        M["evaluator.py\nRAG + Agent test harness"]
        N["logs/\npawpal_agent.log\nevaluation_results.json"]
    end

    User -->|"fills in info"| A
    A --> D
    D --> E
    E --> B
    B --> User

    User -->|"clicks Analyse / Suggest"| C
    C --> G

    G -->|"Step 1: build profile"| D
    G -->|"Step 2: retrieve knowledge"| F
    F -->|"keyword search"| H & I & J & K
    F -->|"top-k chunks"| G

    G -->|"Step 3: eval schedule"| E
    G -->|"Step 4: prompt + context"| L
    L -->|"recommendations"| G
    G -->|"Step 5: validate budget"| E
    G -->|"result + confidence"| C
    C --> User

    G -->|"log every call"| N
    M -->|"run test scenarios"| F & G
    M -->|"save results"| N
```

## Component descriptions

| Component | File | Purpose |
|---|---|---|
| Streamlit UI | `app.py` | User-facing interface — input forms, schedule table, AI Advisor panel |
| Core logic | `pawpal_system.py` | Owner, Pet, Task, Scheduler — all rule-based scheduling |
| RAG retriever | `ai_agent.py → KnowledgeBase` | Loads markdown docs, retrieves top-k chunks by keyword overlap |
| Agentic workflow | `ai_agent.py → PawPalAgent` | 5-step reasoning: profile → retrieve → evaluate → recommend → validate |
| Knowledge base | `knowledge_base/*.md` | 4 curated documents: dogs, cats, general, medical |
| Claude API | Anthropic cloud | Generates natural-language recommendations from retrieved context |
| Evaluator | `evaluator.py` | Test harness: KB retrieval tests (offline) + agent tests (live API) |
| Logs | `logs/` | Agent call log + JSON evaluation results for auditability |
