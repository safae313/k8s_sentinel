# agent.py
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from tools import get_k8s_events

load_dotenv()


# 1. ÉTAT : le carnet de bord qui circule entre les nœuds
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# 2. OUTILS + LLM
tools = [get_k8s_events]

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
llm_with_tools = llm.bind_tools(tools)


# 3. NŒUD "agent" : le cerveau qui réfléchit
def agent_node(state: AgentState):
    system_prompt = SystemMessage(content="""Tu es un expert SRE Kubernetes.
Ton rôle est de diagnostiquer la cause racine d'un incident sur un pod.

RÈGLES STRICTES :
1. Tu DOIS appeler l'outil get_k8s_events(namespace, pod_name) AVANT de répondre.
2. Concentre ton analyse sur les événements de type "Warning".
3. Ignore les événements "Normal" (Scheduled, Pulled, Created, Started) : c'est du bruit de routine.
4. Utilise le champ "Count" pour distinguer un incident ponctuel (Count faible) d'une boucle (Count élevé).
5. Déduis la cause racine à partir du "Reason" et du "Message" des Warning.
6. Sois concis, factuel, en français. Ne propose pas de correctif YAML pour l'instant.""")

    messages = [system_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


# 4. CONSTRUCTION DU GRAPHE
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

builder.add_conditional_edges(
    "agent",
    tools_condition,
    {"tools": "tools", END: END},
)

builder.add_edge("tools", "agent")

graph = builder.compile()