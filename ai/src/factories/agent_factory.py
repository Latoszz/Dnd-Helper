from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from ai.src.managers.prompt_manager import PromptManager


class AgentFactory:
    def __init__(self, tools, llm_factory):
        self.tools = tools
        self.llm_factory = llm_factory
        self.prompt_manager = PromptManager()

    def create_agent_node(self, agent_type: str):
        system_message = self.prompt_manager.get_template(agent_type)

        prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_message}"),
            MessagesPlaceholder(variable_name="messages"),
        ]).partial(system_message=system_message)

        def node(state):
            model = state.get("model", "gpt-4o-mini")
            temperature = state.get("temperature", 0.5)

            # 🔥 dynamiczne tworzenie LLM w locie
            llm = self.llm_factory.get_model(model, temperature)

            agent = prompt | (llm.bind_tools(self.tools) if agent_type == "search" else llm)

            result = agent.invoke(state)

            # 👇 owijamy AIMessage jeśli potrzeba
            if isinstance(result, AIMessage):
                result.name = f"{agent_type}_agent"
                return {"messages": [result]}
            return {"messages": [AIMessage(content=result.content, name=f"{agent_type}_agent")]}

        return node