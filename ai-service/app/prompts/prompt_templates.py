from langchain import hub
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder


def get_simple_agent_prompt_template():
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. Answer the following question: ",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

def get_retriever_prompt_template():
    return hub.pull("rlm/rag-prompt")


def get_markdown_answer_generating_prompt_template():
    return PromptTemplate(
        template="""You are an expert assistant that provides detailed answers in Markdown format.

        ## Question:
        {question}
        
        ## Context:
        {context}
        
        ## Answer:
        Please generate a detailed response based on the context above. Use Markdown formatting for better readability, including:
        - Bullet points
        - Numbered lists
        - Code blocks (if applicable)
        - Headings and subheadings for structure
        - Tables (if necessary)
        
        Ensure that the response is **well-structured and informative** rather than a brief summary.
        
        ---
        
        Few-show learning examples:
        
        # Benefits of Using LangChain for RAG
        
        LangChain provides several advantages when building Retrieval-Augmented Generation (RAG) systems:
        
        ## 1. Modularity
        - Supports multiple retrievers (e.g., FAISS, Pinecone, Weaviate).
        - Easily integrates with different LLMs.
        
        ## 2. Custom Prompting
        - Allows fine-tuning prompt templates to improve answer quality.
        - Supports structured response formatting.
        
        ## 3. Memory and Context Management
        - Can track conversations across multiple queries.
        - Helps maintain relevant context for better responses.
        
        ## 4. Tool Integration
        | Feature  | Description |
        |----------|------------|
        | **Agents** | Enables dynamic tool usage based on queries. |
        | **Chains** | Supports sequential processing for complex workflows. |
        
        By leveraging LangChain, developers can build **more accurate, context-aware AI systems** for various applications.
        """,
        input_variables=["question", "context"],
    )


def get_tools_determining_prompt_template():
    return PromptTemplate(
        template="""You are an assistant responsible for determining which tools to use to complete a user's task. \n
        Here is the user's question: {question} \n
        Based on the user's question, determine which tool(s) should be used to complete the task. \n
        Provide the name(s) of the tool(s) that you would use to complete the task.
        
        Below is context that may help you generate arguments for the tool(s) you choose: \n
        Here is the context: {context}""",
        input_variables=["question", "context"],
    )


def get_grade_documents_prompt_template():
    return PromptTemplate(
        template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
        Here is the retrieved document: \n\n {context} \n\n
        Here is the user question: {question} \n
        If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
        input_variables=["context", "question"],
    )


def get_grade_integration_agent_prompt_template():
    return PromptTemplate(
        template="""You are a grader responsible for evaluating whether the system needs to integrate 
        additional agents to complete the user's task.  
        Here is the user's question:  \n\n {question} \n\n
        Here are the usages of agents that could be integrated:  {usages} \n
        If the usages of the agents contain keywords or semantic meanings related to the user's question, 
        evaluate whether an additional agent is needed. \n
        Give a binary score ('yes' or 'no') to indicate whether the integration of an additional agent is 
        necessary to complete the user's task.  \n
    """,
        input_variables=["question", "usages"],
    )


def get_dynamic_few_shot_gmail_prompt(user_input: str):
    system_message = """You are a Gmail Assistant designed to assist users with their Gmail accounts
     by performing actions such as creating drafts, sending emails, searching for emails, 
     and retrieving email or thread details. You utilize specific tools to interact with 
     the Gmail API and complete tasks based on user input. Your responses must first explain 
     the action you will take and then invoke the appropriate tool with correctly formatted input."""

    create_draft_email_examples = [
        # Example 1: Creating a draft with specific recipient, subject, and body
        [
            HumanMessage(
                "Create a draft email to Alice with the subject 'Project Update' and body 'The project is on track and will be completed by next week.'",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailCreateDraft",
                        "args": {
                            "to": "Alice",
                            "subject": "Project Update",
                            "body": "The project is on track and will be completed by next week.",
                        },
                        "id": "1",
                    }
                ],
            ),
            ToolMessage(
                '{"draftId": "d123456", "message": "Draft created successfully."}',
                tool_call_id="1",
            ),
            AIMessage(
                "I have created a draft email to Alice with the subject 'Project Update.'",
                name="example_assistant",
            ),
        ],
        # Example 2: Creating a draft for multiple recipients
        [
            HumanMessage(
                "Create a draft email to Bob and Charlie with the subject 'Team Meeting' and body 'The team meeting is scheduled for Friday at 3 PM.'",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailCreateDraft",
                        "args": {
                            "to": ["Bob", "Charlie"],
                            "subject": "Team Meeting",
                            "body": "The team meeting is scheduled for Friday at 3 PM.",
                        },
                        "id": "2",
                    }
                ],
            ),
            ToolMessage(
                '{"draftId": "d789012", "message": "Draft created successfully."}',
                tool_call_id="2",
            ),
            AIMessage(
                "I have created a draft email to Bob and Charlie with the subject 'Team Meeting.'",
                name="example_assistant",
            ),
        ],
        # Example 3: Creating a draft with CC and BCC recipients
        [
            HumanMessage(
                "Create a draft email to Dana with CC to Erin and BCC to Frank, subject 'Budget Review' and body 'Please review the attached budget proposal and share your feedback.'",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailCreateDraft",
                        "args": {
                            "to": "Dana",
                            "cc": "Erin",
                            "bcc": "Frank",
                            "subject": "Budget Review",
                            "body": "Please review the attached budget proposal and share your feedback.",
                        },
                        "id": "3",
                    }
                ],
            ),
            ToolMessage(
                '{"draftId": "d345678", "message": "Draft created successfully."}',
                tool_call_id="3",
            ),
            AIMessage(
                "I have created a draft email to Dana with CC to Erin and BCC to Frank, with the subject 'Budget Review.'",
                name="example_assistant",
            ),
        ],
    ]

    send_mail_examples = [
        # Example 1: Sending an email to a single recipient
        [
            HumanMessage(
                "Send an email to Alice with the subject 'Reminder' and body 'Please remember to submit the report by 5 PM.'",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailSendMessage",
                        "args": {
                            "to": "Alice",
                            "subject": "Reminder",
                            "body": "Please remember to submit the report by 5 PM.",
                        },
                        "id": "1",
                    }
                ],
            ),
            ToolMessage(
                '{"status": "Sent", "messageId": "msg12345"}', tool_call_id="1"
            ),
            AIMessage(
                "The email to Alice with the subject 'Reminder' has been sent successfully.",
                name="example_assistant",
            ),
        ],
        # Example 2: Sending an email to multiple recipients
        [
            HumanMessage(
                "Send an email to Bob and Charlie with the subject 'Meeting Update' and body 'The meeting has been rescheduled to Thursday at 2 PM.'",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailSendMessage",
                        "args": {
                            "to": ["Bob", "Charlie"],
                            "subject": "Meeting Update",
                            "body": "The meeting has been rescheduled to Thursday at 2 PM.",
                        },
                        "id": "2",
                    }
                ],
            ),
            ToolMessage(
                '{"status": "Sent", "messageId": "msg67890"}', tool_call_id="2"
            ),
            AIMessage(
                "The email to Bob and Charlie with the subject 'Meeting Update' has been sent successfully.",
                name="example_assistant",
            ),
        ],
        # Example 3: Sending an email with CC and BCC
        [
            HumanMessage(
                "Send an email to Dana with CC to Erin and BCC to Frank, subject 'Budget Proposal' and body 'Please review the attached budget proposal and provide feedback.'",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailSendMessage",
                        "args": {
                            "to": "Dana",
                            "cc": "Erin",
                            "bcc": "Frank",
                            "subject": "Budget Proposal",
                            "body": "Please review the attached budget proposal and provide feedback.",
                        },
                        "id": "3",
                    }
                ],
            ),
            ToolMessage(
                '{"status": "Sent", "messageId": "msg34567"}', tool_call_id="3"
            ),
            AIMessage(
                "The email to Dana with CC to Erin and BCC to Frank, with the subject 'Budget Proposal,' has been sent successfully.",
                name="example_assistant",
            ),
        ],
    ]

    search_email_examples = [
        # Example 1: Searching for emails by subject
        [
            HumanMessage(
                "Search for emails with the subject 'Project Update'.",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailSearch",
                        "args": {"query": "subject:Project Update"},
                        "id": "1",
                    }
                ],
            ),
            ToolMessage(
                '[{"messageId": "msg12345", "snippet": "Here is the project update you requested."}]',
                tool_call_id="1",
            ),
            AIMessage(
                "I found an email with the subject 'Project Update' and snippet: 'Here is the project update you requested.'",
                name="example_assistant",
            ),
        ],
        # Example 2: Searching for emails from a specific sender
        [
            HumanMessage("Search for emails from Alice.", name="example_user"),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {"name": "GmailSearch", "args": {"query": "from:Alice"}, "id": "2"}
                ],
            ),
            ToolMessage(
                '[{"messageId": "msg67890", "snippet": "Hi, just checking in about our meeting tomorrow."}]',
                tool_call_id="2",
            ),
            AIMessage(
                "I found an email from Alice with snippet: 'Hi, just checking in about our meeting tomorrow.'",
                name="example_assistant",
            ),
        ],
        # Example 3: Searching for emails within a date range
        [
            HumanMessage(
                "Search for emails sent in the last week.", name="example_user"
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailSearch",
                        "args": {"query": "newer_than:7d"},
                        "id": "3",
                    }
                ],
            ),
            ToolMessage(
                '[{"messageId": "msg34567", "snippet": "Reminder: Team meeting scheduled for Friday."}]',
                tool_call_id="3",
            ),
            AIMessage(
                "I found an email sent in the last week with snippet: 'Reminder: Team meeting scheduled for Friday.'",
                name="example_assistant",
            ),
        ],
        # Example 4: Searching for emails with attachments
        [
            HumanMessage("Search for emails with attachments.", name="example_user"),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailSearch",
                        "args": {"query": "has:attachment"},
                        "id": "4",
                    }
                ],
            ),
            ToolMessage(
                '[{"messageId": "msg98765", "snippet": "Please find the attached document for your review."}]',
                tool_call_id="4",
            ),
            AIMessage(
                "I found an email with an attachment and snippet: 'Please find the attached document for your review.'",
                name="example_assistant",
            ),
        ],
    ]

    get_message_examples = [
        # Example 1: Retrieve details of a specific email by message ID
        [
            HumanMessage(
                "Retrieve the details of the email with the message ID 'msg12345'.",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailGetMessage",
                        "args": {"messageId": "msg12345"},
                        "id": "1",
                    }
                ],
            ),
            ToolMessage(
                '{"threadId": "thread123", "snippet": "Here is the project update.", "body": "Dear team, Here is the project update for this week...", "subject": "Project Update", "sender": "Alice"}',
                tool_call_id="1",
            ),
            AIMessage(
                "Here are the details of the email with message ID 'msg12345':\n"
                "- **Thread ID:** thread123\n"
                "- **Subject:** Project Update\n"
                "- **Sender:** Alice\n"
                "- **Snippet:** Here is the project update.\n"
                "- **Body:** Dear team, Here is the project update for this week...",
                name="example_assistant",
            ),
        ],
        # Example 2: Retrieve details of another specific email
        [
            HumanMessage(
                "Fetch the details of the email with the message ID 'msg67890'.",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailGetMessage",
                        "args": {"messageId": "msg67890"},
                        "id": "2",
                    }
                ],
            ),
            ToolMessage(
                '{"threadId": "thread678", "snippet": "Reminder: Meeting at 3 PM", "body": "Hi all, Just a reminder about the meeting at 3 PM today...", "subject": "Meeting Reminder", "sender": "Bob"}',
                tool_call_id="2",
            ),
            AIMessage(
                "Here are the details of the email with message ID 'msg67890':\n"
                "- **Thread ID:** thread678\n"
                "- **Subject:** Meeting Reminder\n"
                "- **Sender:** Bob\n"
                "- **Snippet:** Reminder: Meeting at 3 PM\n"
                "- **Body:** Hi all, Just a reminder about the meeting at 3 PM today...",
                name="example_assistant",
            ),
        ],
        # Example 3: Retrieve email details with an unknown message ID
        [
            HumanMessage(
                "Get the details of the email with the message ID 'msg99999'.",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailGetMessage",
                        "args": {"messageId": "msg99999"},
                        "id": "3",
                    }
                ],
            ),
            ToolMessage('{"error": "Message not found"}', tool_call_id="3"),
            AIMessage(
                "The email with the message ID 'msg99999' could not be found.",
                name="example_assistant",
            ),
        ],
    ]

    get_thread_examples = [
        # Example 1: Retrieve the full thread of an email conversation by a Gmail query
        [
            HumanMessage(
                "Retrieve the full thread of the email conversation with the subject 'Project Discussion'.",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailGetThread",
                        "args": {"query": "subject:Project Discussion"},
                        "id": "1",
                    }
                ],
            ),
            ToolMessage(
                '[{"messageId": "msg123", "snippet": "Let’s start the project discussion.", "body": "Hi team, Let’s start the project discussion...", "subject": "Project Discussion", "sender": "Alice"},'
                '{"messageId": "msg124", "snippet": "Follow-up on the project tasks.", "body": "Hi Alice, Just a follow-up on the project tasks...", "subject": "Project Discussion", "sender": "Bob"}]',
                tool_call_id="1",
            ),
            AIMessage(
                "Here is the full thread of the email conversation with the subject 'Project Discussion':\n\n"
                "**Message 1:**\n"
                "- **Sender:** Alice\n"
                "- **Snippet:** Let’s start the project discussion.\n"
                "- **Body:** Hi team, Let’s start the project discussion...\n\n"
                "**Message 2:**\n"
                "- **Sender:** Bob\n"
                "- **Snippet:** Follow-up on the project tasks.\n"
                "- **Body:** Hi Alice, Just a follow-up on the project tasks...",
                name="example_assistant",
            ),
        ],
        # Example 2: Retrieve a thread by a specific sender
        [
            HumanMessage(
                "Retrieve the email thread of messages from Bob.", name="example_user"
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {"name": "GmailGetThread", "args": {"query": "from:Bob"}, "id": "2"}
                ],
            ),
            ToolMessage(
                '[{"messageId": "msg789", "snippet": "Update on the financial report.", "body": "Hi team, Here is the updated financial report...", "subject": "Financial Report", "sender": "Bob"},'
                '{"messageId": "msg790", "snippet": "Reminder about the team meeting.", "body": "Hi all, Reminder about tomorrow’s team meeting...", "subject": "Meeting Reminder", "sender": "Bob"}]',
                tool_call_id="2",
            ),
            AIMessage(
                "Here is the email thread of messages from Bob:\n\n"
                "**Message 1:**\n"
                "- **Subject:** Financial Report\n"
                "- **Snippet:** Update on the financial report.\n"
                "- **Body:** Hi team, Here is the updated financial report...\n\n"
                "**Message 2:**\n"
                "- **Subject:** Meeting Reminder\n"
                "- **Snippet:** Reminder about the team meeting.\n"
                "- **Body:** Hi all, Reminder about tomorrow’s team meeting...",
                name="example_assistant",
            ),
        ],
        # Example 3: Handling no results for a query
        [
            HumanMessage(
                "Retrieve the thread of emails with the query 'newer_than:30d label:inbox'.",
                name="example_user",
            ),
            AIMessage(
                "",
                name="example_assistant",
                tool_calls=[
                    {
                        "name": "GmailGetThread",
                        "args": {"query": "newer_than:30d label:inbox"},
                        "id": "3",
                    }
                ],
            ),
            ToolMessage("[]", tool_call_id="3"),
            AIMessage(
                "No email threads were found matching the query 'newer_than:30d label:inbox'.",
                name="example_assistant",
            ),
        ],
    ]

    # Todo: Implement dynamic few-shot learning for Gmail
    examples = [
        *create_draft_email_examples[0],
        *send_mail_examples[0],
        *search_email_examples[0],
        *get_message_examples[0],
        *get_thread_examples[0],
    ]

    return SystemMessage(system_message)
