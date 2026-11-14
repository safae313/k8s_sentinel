# tools.py
import subprocess
import json
from langchain_core.tools import tool


@tool
def get_k8s_events(namespace: str, pod_name: str) -> str:
    """Récupère les événements Kubernetes récents pour un pod spécifique.
    Utile pour diagnostiquer pourquoi un pod est en CrashLoopBackOff,
    ImagePullBackOff, ou ne démarre pas.

    Args:
        namespace: Le namespace du pod (ex: 'default').
        pod_name: Le nom exact du pod (ex: 'crasher').
    """
    try:
        result = subprocess.run(
            [
                "kubectl", "get", "events",
                "-n", namespace,
                "--field-selector", f"involvedObject.name={pod_name}",
                "--sort-by=.lastTimestamp",
                "-o", "json",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )

        if result.returncode != 0:
            return f"Erreur kubectl: {result.stderr}"

        events = json.loads(result.stdout)
        items = events.get("items", [])

        if not items:
            return f"Aucun événement trouvé pour le pod '{pod_name}' dans le namespace '{namespace}'."

        formatted = []
        for event in items:
            formatted.append(
                f"Type: {event.get('type', 'N/A')} | "
                f"Reason: {event.get('reason', 'N/A')} | "
                f"Message: {event.get('message', 'N/A')} | "
                f"Count: {event.get('count', 'N/A')}"
            )

        return "\n---\n".join(formatted)

    except subprocess.TimeoutExpired:
        return "Erreur: la commande kubectl a expiré après 30 secondes."
    except json.JSONDecodeError:
        return f"Erreur: impossible de parser la sortie JSON. Sortie brute: {result.stdout[:500]}"
    except Exception as e:
        return f"Erreur inattendue: {str(e)}"