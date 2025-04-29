import logging

import tiktoken

GPT4O_INPUT_COST_PER_MILLION = 2.50
GPT4O_OUTPUT_COST_PER_MILLION = 10.00

def estimate_tokens(text: str, model_name: str = "gpt-4o") -> int:
    """
    Estimate number of tokens for a given text using OpenAI tokenizer.
    """
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def estimate_cost(input_tokens: int, output_tokens: int = 500) -> float:
    """
    Estimate cost (in USD) based on input and output tokens.
    Default output is 500 tokens if not known.
    """
    input_cost = (input_tokens / 1_000_000) * GPT4O_INPUT_COST_PER_MILLION
    output_cost = (output_tokens / 1_000_000) * GPT4O_OUTPUT_COST_PER_MILLION
    return input_cost + output_cost

def pretty_print_estimate(text: str):
    input_tokens = estimate_tokens(text)
    est_cost = estimate_cost(input_tokens)

    logging.info(f"Estimated Input Tokens: {input_tokens}")
    logging.info(f"Approximate LLM Cost (USD): ${est_cost:.4f}")

    return input_tokens, est_cost
