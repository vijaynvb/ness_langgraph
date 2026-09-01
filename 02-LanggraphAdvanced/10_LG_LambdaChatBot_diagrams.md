# Ticket Triage Chatbot — Diagrams

A LangGraph agent that resolves support tickets by calling four AWS Lambda functions as tools — fetching ticket and failure details, retrieving fix steps, and optionally asking Amazon Bedrock to explain a failure in plain language.

## 1. Architecture

The notebook process holds the LangGraph state machine and the LLM binding; every tool call leaves the process as a `boto3` invocation against a named Lambda function in AWS. One of those functions, `search_failure_bedrock`, makes a further call out to Amazon Bedrock.

```mermaid
flowchart LR
    User(["User<br/>terminal input()"])

    subgraph LOCAL["Local environment"]
        ENV[".env<br/>AWS + LangSmith credentials"]
    end

    subgraph APP["Notebook process"]
        LOOP["stream_graph_updates()<br/>interaction loop"]
        subgraph SG["LangGraph StateGraph"]
            direction LR
            CHATBOT["chatbot node<br/>llm_with_tools.invoke()"]
            TOOLS["tools node<br/>BasicToolNode"]
            CHATBOT -- "AIMessage has tool_calls" --> TOOLS
            TOOLS -- "ToolMessage(s)<br/>loop back" --> CHATBOT
        end
        LLM["ChatBedrock Novapro<br/>bound to 4 tools"]
        BOTO["boto3 lambda_client<br/>region: us-east-1"]
        CHATBOT <-- "messages" --> LLM
        TOOLS --> BOTO
    end

    subgraph CLOUD["AWS cloud"]
        L1["Lambda\nget_ticket_details"]
        L2["Lambda\nget_failure_details"]
        L3["Lambda\nfix_failure_steps"]
        L4["Lambda\nsearch_failure_bedrock"]
        BR[["Amazon Bedrock<br/>Mistral model"]]
        L4 -- "InvokeModel:<br/>explain failure" --> BR
    end

    LS[("LangSmith<br/>project: tutorial")]

    User -- "types question" --> LOOP
    LOOP -- "print Assistant: ..." --> User
    ENV -.->|"AWS keys"| BOTO
    ENV -.->|"API key"| LS
    LOOP -- "graph.stream(messages)" --> CHATBOT
    CHATBOT -.->|"final answer"| LOOP
    BOTO -- "invoke()" --> L1
    BOTO -- "invoke()" --> L2
    BOTO -- "invoke()" --> L3
    BOTO -- "invoke()" --> L4
    SG -.->|"trace spans"| LS
```

The four LangChain `@tool` functions are thin wrappers: each serializes its arguments to JSON and calls a same-named AWS Lambda function via `lambda_client.invoke()`. Only `search_failure_bedrock` has a second hop, from its Lambda into Amazon Bedrock.

## 2. Request sequence

Walking through the notebook's first example prompt — *"Fetch ticket TICKET12345, get the failure details, then find the fix."* The graph alternates between the chatbot node and the tools node until the model responds with no further tool calls.

```mermaid
sequenceDiagram
    actor User
    participant CLI as Interaction loop
    participant Chatbot as chatbot node
    participant LLM as ChatBedrock Novapro
    participant Tools as tools node / BasicToolNode
    participant Boto as boto3 lambda_client
    participant AWS as AWS Lambda
    participant Bedrock as Amazon Bedrock: Novapro

    User->>CLI: "Fetch ticket TICKET12345,<br/>get the failure details, find the fix"
    CLI->>Chatbot: graph.stream({messages:[user_input]})

    rect rgba(120,120,120,0.06)
    note over Chatbot,Tools: repeats once per tool the model decides to call
    loop until AIMessage has no tool_calls
        Chatbot->>LLM: llm_with_tools.invoke(messages)
        LLM-->>Chatbot: AIMessage (+ tool_call, or final text)
        alt tool_calls present -> route_tools() returns "tools"
            Chatbot->>Tools: invoke(state)
            note right of Tools: search_failure_bedrock called with no args:<br/>backfills failure_code/description from the<br/>earlier get_ticket_details ToolMessage
            Tools->>Boto: tools_by_name[name].invoke(args)
            Boto->>AWS: invoke(FunctionName=name, Payload=json)
            opt name == search_failure_bedrock
                AWS->>Bedrock: InvokeModel — explain failure
                Bedrock-->>AWS: generated explanation
            end
            AWS-->>Boto: response payload
            Boto-->>Tools: JSON result
            Tools-->>Chatbot: ToolMessage(result, tool_call_id)
        else no tool_calls -> route_tools() returns END
            Chatbot-->>CLI: final AIMessage.content
        end
    end
    end

    CLI-->>User: print "Assistant: " + content
```

Every pass through the loop is one `chatbot → tools → chatbot` round trip: the graph only exits to `END` once `route_tools()` sees an `AIMessage` with no `tool_calls`.

## 3. Tools reference

All four tools share the same shape — serialize arguments, invoke a same-named Lambda, return its JSON payload.

| LangChain tool | Lambda function | Called with | Purpose |
|---|---|---|---|
| `get_ticket_details` | `get_ticket_details` | `ticket_id` | Look up a support ticket's stored details, including its failure code. |
| `get_failure_details` | `get_failure_details` | `failure_code` | Return detailed information about a specific failure code. |
| `fix_failure_steps` | `fix_failure_steps` | `failure_code` | Return the resolution / fix steps for a failure code. |
| `search_failure_bedrock` | `search_failure_bedrock` | `failure_info` (dict) | Ask a Bedrock model (Mistral) to explain a failure in natural language; `BasicToolNode` fills in the argument from an earlier `get_ticket_details` result when the model calls it empty. |

## Implementation note

The notebook imports `ChatBedrock` from `langchain_aws` but the `chatbot` node actually instantiates `ChatBedrock Novapro`, a class that isn't imported anywhere in the shown cells. The diagrams above reflect the code as written — the reasoning model is Nova Pro via `ChatBedrock `, and Bedrock is only reached indirectly through the `search_failure_bedrock` Lambda. If Bedrock was meant to be the main model, swap in `ChatBedrock` (and drop the unused import if not).
