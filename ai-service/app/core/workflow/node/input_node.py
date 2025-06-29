from ...state import WorkflowTeamState


def InputNode(state: WorkflowTeamState):
    if "node_outputs" not in state:
        state["node_outputs"] = {}
    human_message = None

    # Retrieve the most recent user message if available
    if messages := state.get("all_messages", []):
        human_message = messages[-1].content
    input_node_outputs = {"start": {"query": human_message}}
    state["node_outputs"] = input_node_outputs
    return state
