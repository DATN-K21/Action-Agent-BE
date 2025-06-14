"""
Context Management Usage Examples

This file demonstrates how to use the new context management system
for optimizing conversation history in AI agents.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.core.enums import LlmProvider
from app.core.state import format_messages, format_messages_with_model_context
from app.core.utils.context_manager import ContextManager, default_context_manager
from app.core.utils.model_context_config import get_optimized_format_messages_for_model


def create_sample_conversation():
    """Create a sample conversation with various message types."""
    return [
        SystemMessage(content="You are a helpful AI assistant specialized in data analysis."),
        HumanMessage(content="Hello, I need help analyzing some sales data."),
        AIMessage(content="I'd be happy to help you analyze your sales data. What specific metrics are you interested in?"),
        HumanMessage(content="I want to understand the trends in Q4 2024 compared to Q4 2023."),
        AIMessage(
            content="Great! To analyze Q4 trends, I'll need to examine the data. Let me retrieve the relevant information.",
            tool_calls=[{"name": "get_sales_data", "args": {"period": "Q4", "years": [2023, 2024]}}],
        ),
        ToolMessage(content="Sales data retrieved: Q4 2023: $1.2M, Q4 2024: $1.8M", tool_call_id="tool_1"),
        AIMessage(content="Based on the data, your Q4 2024 sales ($1.8M) show a 50% increase compared to Q4 2023 ($1.2M). This is excellent growth!"),
        HumanMessage(content="That's great! What factors might have contributed to this growth?"),
        AIMessage(
            content="Several factors could contribute to this growth. Let me analyze the breakdown by category.",
            tool_calls=[{"name": "analyze_sales_breakdown", "args": {"period": "Q4 2024"}}],
        ),
        ToolMessage(content="Category breakdown: Product A: 40%, Product B: 35%, Product C: 25%", tool_call_id="tool_2"),
        AIMessage(
            content="The growth appears to be driven by strong performance across all product categories, with Product A leading at 40% of total sales."
        ),
        HumanMessage(content="Can you create a detailed report with visualizations?"),
        AIMessage(
            content="I'll create a comprehensive report with visualizations for you.",
            tool_calls=[{"name": "generate_report", "args": {"include_charts": True, "format": "pdf"}}],
        ),
        ToolMessage(content="Report generated successfully: sales_analysis_q4_2024.pdf", tool_call_id="tool_3"),
        AIMessage(
            content="I've generated a detailed sales analysis report with visualizations. The report includes trend analysis, category breakdowns, and growth projections."
        ),
    ]


def example_basic_usage():
    """Demonstrate basic context optimization usage."""
    print("=== Basic Context Optimization Example ===")

    messages = create_sample_conversation()

    # Original format (now automatically optimized)
    formatted_context = format_messages(messages)

    print(f"Formatted context length: {len(formatted_context)} characters")
    print(f"Estimated tokens: {default_context_manager.estimate_tokens(formatted_context)}")
    print("\nFormatted context (first 200 chars):")
    print(formatted_context[:200] + "...")


def example_model_specific_optimization():
    """Demonstrate model-specific context optimization."""
    print("\n=== Model-Specific Optimization Example ===")

    messages = create_sample_conversation()
    # Optimize for GPT-4
    gpt4_context = format_messages_with_model_context(messages, model_name="gpt-4o", provider="openai")

    # Optimize for a smaller model
    smaller_model_context = get_optimized_format_messages_for_model(messages, model_name="gpt-3.5-turbo", provider=LlmProvider.OPENAI)

    print(f"GPT-4 optimized context: {len(gpt4_context)} chars")
    print(f"GPT-3.5 optimized context: {len(smaller_model_context)} chars")
    print(f"Difference: {len(gpt4_context) - len(smaller_model_context)} chars")


def example_custom_context_manager():
    """Demonstrate custom context manager configuration."""
    print("\n=== Custom Context Manager Example ===")

    messages = create_sample_conversation()

    # Create a very aggressive context manager (for cost-sensitive scenarios)
    aggressive_manager = ContextManager(
        max_context_tokens=2000,  # Very limited
        system_message_priority=True,
        recent_messages_weight=3.0,  # Strongly favor recent messages
        tool_message_weight=2.0,
        min_context_messages=3,
    )

    # Create a permissive context manager (for quality-focused scenarios)
    permissive_manager = ContextManager(
        max_context_tokens=15000,  # Very generous
        system_message_priority=True,
        recent_messages_weight=1.2,  # Slight preference for recent
        tool_message_weight=1.1,
        min_context_messages=10,
    )

    aggressive_context = aggressive_manager.format_optimized_messages(messages)
    permissive_context = permissive_manager.format_optimized_messages(messages)

    print(f"Aggressive optimization: {len(aggressive_context)} chars")
    print(f"Permissive optimization: {len(permissive_context)} chars")
    print(f"Original messages count: {len(messages)}")
    print(f"Aggressive optimized count: {len(aggressive_manager.optimize_context_messages(messages))}")
    print(f"Permissive optimized count: {len(permissive_manager.optimize_context_messages(messages))}")


def example_message_prioritization():
    """Demonstrate how different message types are prioritized."""
    print("\n=== Message Prioritization Example ===")

    messages = create_sample_conversation()

    # Create a context manager that logs prioritization
    context_manager = ContextManager(max_context_tokens=3000)

    # Get detailed information about prioritization
    message_data = []
    for i, message in enumerate(messages):
        content = context_manager.get_message_content_text(message)
        tokens = context_manager.estimate_tokens(content)
        priority = context_manager.calculate_message_priority(message, i, len(messages))

        message_data.append(
            {
                "index": i,
                "type": type(message).__name__,
                "tokens": tokens,
                "priority": priority,
                "content_preview": content[:50] + "..." if len(content) > 50 else content,
            }
        )

    # Sort by priority to show selection order
    sorted_messages = sorted(message_data, key=lambda x: x["priority"], reverse=True)

    print("Message prioritization (highest to lowest):")
    print("-" * 80)
    for msg in sorted_messages:
        print(f"Priority: {msg['priority']:.2f} | Type: {msg['type']:<12} | Tokens: {msg['tokens']:>3} | Preview: {msg['content_preview']}")


def example_token_limit_scenarios():
    """Demonstrate behavior with different token limits."""
    print("\n=== Token Limit Scenarios Example ===")

    messages = create_sample_conversation()

    # Test different token limits
    limits = [1000, 3000, 5000, 10000, 20000]

    print("Token limit scenarios:")
    print("-" * 60)
    for limit in limits:
        manager = ContextManager(max_context_tokens=limit)
        optimized = manager.optimize_context_messages(messages)
        formatted = manager.format_optimized_messages(messages)
        actual_tokens = manager.estimate_tokens(formatted)

        print(f"Limit: {limit:>5} | Messages: {len(optimized):>2}/{len(messages)} | Actual tokens: {actual_tokens:>4}")


if __name__ == "__main__":
    # Run all examples
    example_basic_usage()
    example_model_specific_optimization()
    example_custom_context_manager()
    example_message_prioritization()
    example_token_limit_scenarios()

    print("\n=== Summary ===")
    print("The context management system provides flexible, intelligent optimization")
    print("of conversation history to balance cost, performance, and quality.")
    print("Use the default settings for most cases, or customize for specific needs.")
