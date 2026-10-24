import logging
from strands import Agent
from tools import get_country_info, population_ratio_difference

# Enables Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG) # or logging.INFO

# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

SYSTEM_PROMPT = """You are a helpful, analytical, and precise geopolitical and demographic AI assistant equipped with specialized tools.

You have access to the following tools:
1. `get_country_info`: Look up factual, real-time data about a country (such as capital, population, region, currencies, and languages) using the REST Countries API.
2. `population_ratio_difference`: Calculate the demographic ratio or difference between country populations or compare specific numeric metrics with mathematical accuracy.

Guidelines:
- Tool First: When a user query involves country facts or demographic comparisons, always call the relevant tool(s) rather than hallucinating facts or estimating numbers.
- Multi-step Reasoning: If a user asks to compare two countries, first retrieve the relevant data using `get_country_info`, then compute the comparison using `population_ratio_difference`.
- Clear Synthesis: Integrate the raw tool results into a coherent, natural, and helpful answer.
- Conversational Queries: If a user greeting or general question does not require tools, respond politely and directly."""

agent = Agent(
    model="us.anthropic.claude-haiku-4-5-20251001-v1:0",
    tools=[get_country_info, population_ratio_difference],
    system_prompt=SYSTEM_PROMPT)

if __name__ == "__main__":
    response = agent("Compare the population between Japan and Canada")
    print(response)