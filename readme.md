

state
start
end
node
edge
tools
toolnode
conditional edge
  1. Node based 
  2. Conditional edge function based
stategraph
runnable 
messages -> 
  SM
  AIM
  HM
  Toolmessage 
checkpoint = inmemory, sqllite, pgdb
threads
MessageState: reducers

interrupt, Command -> human interaction 

Tool Invocation:
 1. by processing ai message - type = tool_use, Reason, 
 2. ToolNode


Langsmith: observability tool 
Workflow
Agentic AI

ReAct Pattern [Reason - Action - Observe]
  1. prompt 
  2. plan -> tool calling llm node [nodes]
    1. todo list
  3. execute -> Action -> back to tool calling llm node [observe] 



Task: 
  create an agentic ai solution that can provide real time weather and news from the internet and perform basic arithmetic operations as tool calls and manage the sessions [add new session , delete session, list sessions] and provide a summary of the session.



1. AI App  [graph trigger]
2. MCP Client [mcp tool -> langchain_mcp_adapters client(connect mcp server) ]

3. Mcp Server [MCP Tools]
4. Resources [ Tools
  1. Weather API
  2. News API
  3. Arithmetic Tool
]