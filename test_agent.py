# test_agent.py
from langchain_core.messages import HumanMessage

from agent import graph


if __name__ == "__main__":
    print("🤖 Agent en cours d'investigation...\n")

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Le pod 'crasher' dans le namespace 'default' est en CrashLoopBackOff. Diagnostique la cause racine."
                )
            ]
        },
        {"recursion_limit": 10},
    )

    print("📋 DIAGNOSTIC FINAL :\n")
    print(result["messages"][-1].content)