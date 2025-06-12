from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage
import functools
from typing import Literal
from langchain.chat_models import init_chat_model

from managers.prompt_manager import PromptManager
from services.agent_state import AgentState



class WorkflowService:
    def __init__(self, tools, config):
        self.tools = tools
        self.config = config
        self.prompt_manager = PromptManager()
        self.workflow = StateGraph(AgentState)

    def _create_agent_node(self, state, agent, name):
        result = agent.invoke(state)

        if isinstance(result, AIMessage):
            result.name = name
            return {"messages": [result]}

        return {"messages": [AIMessage(content=result.content, tool_calls=result.tool_calls, name=name)]}


    def _create_agent(self, config: RunnableConfig, agent_type: str, uses_tools = False):
        node_config = config.get("configurable", {})

        provider = node_config.get("provider")
        model = node_config.get("model")
        temperature = node_config.get("temperature")

        key = None
        if provider == "openai":
            key = self.config.openai_key
        elif provider == "google_genai":
            key = self.config.google_genai_key

        llm = init_chat_model(model_provider=provider, model=model, temperature=temperature, api_key=key)
        system_message = self.prompt_manager.get_template(agent_type)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_message}"),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(system_message=system_message)

        if uses_tools:
            agent = prompt | llm.bind_tools(self.tools)
        else:
            agent = prompt | llm

        return agent

    def _create_node(self, state: AgentState, config: RunnableConfig, agent_type: str, uses_tools = False) -> AgentState:

        agent = self._create_agent(config, agent_type, uses_tools)

        result = agent.invoke(state)

        if isinstance(result, AIMessage):
            result.name = f"{agent_type}_agent"
            return {"messages": [result]}

        return {"messages": [AIMessage(content=result.content, tool_calls=result.tool_calls, name=f"{agent_type}_agent")]}

    def _create_router_node(self, state: AgentState, config: RunnableConfig) -> AgentState:

        agent = self._create_agent(config, "router")
        result = agent.invoke(state)

        result.name = "router_agent"
        return {"intent": result.content}


    def _setup_nodes(self):
        nodes = {
            "router": functools.partial(
                self._create_router_node,
            ),
            "general": functools.partial(
                self._create_node,
                agent_type="general",
                uses_tools=True
            ),
            "advisor": functools.partial(
                self._create_node,
                agent_type="advisor",
                uses_tools=True
            ),
            "creator": functools.partial(
                self._create_node,
                agent_type="creator",
                uses_tools=True
            ),
            "writer": functools.partial(
                self._create_node,
                agent_type="writer",
            ),
            "tools": ToolNode(self.tools),
        }

        for name, node in nodes.items():
            self.workflow.add_node(name, node)

    def _setup_edges(self):

        self.workflow.set_entry_point("router")
        self.workflow.add_conditional_edges(
            "router",
            self._route_from_router,
        )

        # Search node transitions
        self.workflow.add_conditional_edges(
            "general",
            self._should_search,
        )

        self.workflow.add_conditional_edges(
            "advisor",
            self._should_search,
        )

        self.workflow.add_conditional_edges(
            "creator",
            self._should_search,
        )

        self.workflow.add_conditional_edges(
            "tools",
            self._route_from_router,
        )

        self.workflow.set_finish_point("writer")

    def _should_search(self, state) -> Literal["tools", "writer"]:
        messages = state["messages"]
        last_message = messages[-1]
        # If the LLM makes a tool call, then we route to the "tools" node
        if last_message.tool_calls:
            return "tools"
        # Otherwise, we stop (reply to the user)
        return "writer"

    def _route_from_router(self, state) -> Literal["general", "advisor", "creator"]:
        intent = state.get("intent", "general")
        return intent

    def build(self):
        self._setup_nodes()
        self._setup_edges()
        return self.workflow
