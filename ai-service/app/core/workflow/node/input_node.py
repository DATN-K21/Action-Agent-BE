from ...state import WorkflowTeamState


def InputNode(state: WorkflowTeamState):
    if "node_outputs" not in state:
        state["node_outputs"] = {}
    human_message = None
    if isinstance(state, list):
        human_message = state[-1].content
    elif messages := state.get("all_messages", []):
        human_message = messages[-1].content
    input_node_outputs = {"start": {"query": human_message}}
    state["node_outputs"] = input_node_outputs
    return state
