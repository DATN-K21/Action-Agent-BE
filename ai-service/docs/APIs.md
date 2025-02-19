# APIs Documentation
This documentation explains how to utilize the APIs offered by the project to interact with the system and perform different operations.

For complete API details, visit http://localhost:5001/docs after deploying the project.

The following code examples are written in Python and are intended to be executed in a Jupyter Notebook.

## 1. Flow to use APIs
### 1.1 Start conversation
1. Create a user to get user id.
2. Use the user id to create a thread.
3. Use the thread id to start a conversation.
### 1.2 Start with an extension
1. Create a user to get user id.
2. Use the user id to initiate connection to external app (like: Gmail, Slack, etc.).
3. Use a user id to create thread id.
4. Use the thread id to start a conversation.

## 2. Chatbot APIs
### 2.1 Chat API (post - /chatbot/chat)
#### a. Input schema
```json
{
  "threadId": "string",
  "input": "string"
}

```
#### b. Successful output schema
```json
{
  "status": "integer",
  "data": {
    "threadId": "string",
    "output": "string"
  }
}
```

**Example:**
```json
{
    "status": 200,
    "data": {
        "threadId": "abc",
        "output": "It seems like you're trying to input a prompt or question. Please feel free to type out any question or topic you're interested in, and I'll be happy to help!"
    }
}
```

#### c. Error output schema
```json
{
  "status": "integer",
  "message": "string"
}
```

#### d. Validate error output schema
```json
   {
      "detail": [
        {
          "loc": [
            "string",
            0
          ],
          "msg": "string",
          "type": "string"
        }
      ]
    }
```



### 2.2 Stream API (post - /chatbot/stream)
#### a. Input schema
```json
{
  "threadId": "string",
  "input": "string"
}

```
#### b. Handle stream response
* Example code to handle stream response
```python
import requests
import json

url = "http://localhost:5001/chatbot/stream"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}
data = {
    "threadId": "abc",
    "input": "Hello world"
}

response = requests.post(url, json=data, headers=headers)

res = []
if response.status_code == 200:
    # Iterate over the response
    for line in response.iter_lines():
        if line:  # filter out keep-alive new lines
            string_line = line.decode("utf-8")
            # Only look at where data i returned
            if string_line.startswith('data'):
                json_string = string_line[len('data: '):]
                # Get the json response - contains a list of all messages
                messages = json.loads(json_string)
                if isinstance(messages, list) and len(messages) > 0:
                    # Get the content from the last message
                    # If you want to display multiple messages (eg if agent takes intermediate steps) you will need to change this logic
                    if 'type' in messages[-1] and messages[-1]['type'].lower() == 'ai':
                        print(messages[-1]['content'])
else:
    print(f"Failed to retrieve data: {response.status_code}")
```
* Output of the above code
```text
Hello
Hello,
Hello, world
Hello, world!
Hello, world! How
Hello, world! How can
Hello, world! How can I
Hello, world! How can I assist
Hello, world! How can I assist you
Hello, world! How can I assist you today
Hello, world! How can I assist you today?
Hello, world! How can I assist you today? If
Hello, world! How can I assist you today? If you
Hello, world! How can I assist you today? If you have
Hello, world! How can I assist you today? If you have any
Hello, world! How can I assist you today? If you have any questions
Hello, world! How can I assist you today? If you have any questions or
Hello, world! How can I assist you today? If you have any questions or topics
Hello, world! How can I assist you today? If you have any questions or topics you'd
Hello, world! How can I assist you today? If you have any questions or topics you'd like
Hello, world! How can I assist you today? If you have any questions or topics you'd like to
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore,
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to share
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to share them
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to share them with
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to share them with me
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to share them with me!
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to share them with me!
Hello, world! How can I assist you today? If you have any questions or topics you'd like to explore, feel free to share them with me!
```

## 3. RAG APIs
### 3.1. Ingest API (post - /rag/ingest)
#### a. Input schema
* **files:** List of files to be ingested (required)
* **threadId:** Thread id to which the files are to be ingested (required)

**Example**:
```bash
curl -X 'POST' \
  'http://localhost:5001/rag/ingest' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'files=@Lab Final Project Report.docx;type=application/pdf' \
  -F 'threadId=abc'
```

#### b. Successful output schema
```json
{
  "status": 200,
  "data": {
    "threadId": "abc",
    "isSuccess": true,
    "output": "Files ingested successfully"
  }
}
```

#### c. Error output schema
```json
{
  "status": "integer",
  "message": "string"
}
```

#### d. Validate error output schema
```json
   {
      "detail": [
        {
          "loc": [
            "string",
            0
          ],
          "msg": "string",
          "type": "string"
        }
      ]
    }
```


### 3.2. Chat API (post - /rag/chat)
[The same as Chat API in Chatbot APIs.](#21-chat-api-post---chatbotchat)

### 3.3. Stream API (post - /rag/stream)
* Example code to handle stream response
```python
import requests
import json

url = "http://localhost:5001/rag/stream"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}
data = {
    "threadId": "abc",
    "input": "Give me information about the Lab Final Project report"
}

response = requests.post(url, json=data, headers=headers)

res = []
if response.status_code == 200:
    # Iterate over the response
    for line in response.iter_lines():
        if line:  # filter out keep-alive new lines
            string_line = line.decode("utf-8")
            # Only look at where data i returned
            if string_line.startswith('data'):
                json_string = string_line[len('data: '):]
                # Get the json response - contains a list of all messages
                messages = json.loads(json_string)
                if isinstance(messages, list) and len(messages) > 0:
                    if 'type' in messages[-1] and messages[-1]['type'].lower() == 'ai':
                        if 'tool_calls' in messages[-1] and len(messages[-1]['tool_calls']) > 0:
                            # Print tool_calls information
                            print(messages[-1]['tool_calls'])
                        else:
                            # Print message
                            print(messages[-1]['content']) 
else:
    print(f"Failed to retrieve data: {response.status_code}")
```

* Output of the above code
```text
[{'name': 'retriever_tool', 'args': {}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': ''}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': 'Lab'}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': 'Lab Final'}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': 'Lab Final Project'}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': 'Lab Final Project report'}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': 'Lab Final Project report'}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': 'Lab Final Project report'}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]
[{'name': 'retriever_tool', 'args': {'query': 'Lab Final Project report'}, 'id': 'call_KSiiodgC7N1Bkwr0aTRWn0jG', 'type': 'tool_call'}]

The
The Lab
The Lab Final
The Lab Final Project
The Lab Final Project report
The Lab Final Project report for
The Lab Final Project report for the
The Lab Final Project report for the Advanced
The Lab Final Project report for the Advanced Web
The Lab Final Project report for the Advanced Web Application
The Lab Final Project report for the Advanced Web Application Development
The Lab Final Project report for the Advanced Web Application Development course
The Lab Final Project report for the Advanced Web Application Development course involves
The Lab Final Project report for the Advanced Web Application Development course involves creating
The Lab Final Project report for the Advanced Web Application Development course involves creating an
The Lab Final Project report for the Advanced Web Application Development course involves creating an online
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform.
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control.
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in s
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints,
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates,
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different aspects
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different aspects of
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different aspects of the
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different aspects of the platform
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different aspects of the platform.
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different aspects of the platform.
The Lab Final Project report for the Advanced Web Application Development course involves creating an online movie streaming platform. The project utilizes modern technologies like React for the frontend and includes features such as user authentication and role-based access control. The project is structured in sprints, with specific user stories and due dates, and involves a team of students working collaboratively on different aspects of the platform.
```

## 4. Search APIs
### 4.1. Search API (post - /search/chat)
[The same as Chat API in Chatbot APIs.](#21-chat-api-post---chatbotchat)
### 4.2. Stream API (post - /search/stream)

* Example code to handle stream response
```python
import requests
import json

url = "http://localhost:5001/search/stream"
headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}
data = {
    "threadId": "abcd",
    "input": "Give me information about computer from wiki"
}

response = requests.post(url, json=data, headers=headers)

res = []
if response.status_code == 200:
    # Iterate over the response
    for line in response.iter_lines():
        if line:  # filter out keep-alive new lines
            string_line = line.decode("utf-8")
            # Only look at where data i returned
            if string_line.startswith('data'):
                json_string = string_line[len('data: '):]
                # Get the json response - contains a list of all messages
                messages = json.loads(json_string)
                if isinstance(messages, list) and len(messages) > 0:
                    if 'type' in messages[-1] and messages[-1]['type'].lower() == 'ai':
                        if 'tool_calls' in messages[-1] and len(messages[-1]['tool_calls']) > 0:
                            # Print tool_calls information
                            print(messages[-1]['tool_calls'])
                        else:
                            # Print message
                            print(messages[-1]['content']) 
else:
    print(f"Failed to retrieve data: {response.status_code}")
```

* Output of the above code
```text
[{'name': 'tavily_search_tool', 'args': {}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': ''}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site:'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site:en'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site:en.wikipedia'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site:en.wikipedia.org'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site:en.wikipedia.org'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site:en.wikipedia.org'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]
[{'name': 'tavily_search_tool', 'args': {'query': 'Computer site:en.wikipedia.org'}, 'id': 'call_4aPghnBaTRZUVTDQDjQeP1iz', 'type': 'tool_call'}]

A
A computer
A computer is
A computer is a
A computer is a programmable
A computer is a programmable digital
A computer is a programmable digital electronic
A computer is a programmable digital electronic device
A computer is a programmable digital electronic device capable
A computer is a programmable digital electronic device capable of
A computer is a programmable digital electronic device capable of performing
A computer is a programmable digital electronic device capable of performing a
A computer is a programmable digital electronic device capable of performing a variety
A computer is a programmable digital electronic device capable of performing a variety of
A computer is a programmable digital electronic device capable of performing a variety of tasks
A computer is a programmable digital electronic device capable of performing a variety of tasks,
A computer is a programmable digital electronic device capable of performing a variety of tasks, including
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing.
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer"
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations,
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 194
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945.
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers,
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs,
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word processing
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word processing and
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word processing and internet
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word processing and internet browsing
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word processing and internet browsing.
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word processing and internet browsing.
A computer is a programmable digital electronic device capable of performing a variety of tasks, including calculations and data processing. The term "computer" originally referred to a human who performed calculations, but its modern usage as a machine dates back to 1945. Personal computers, or PCs, are designed for individual use and are commonly used for tasks like word processing and internet browsing.
```

## 5. Multi-Agent APIs (Low performance - Not recommended for production)
...

## 6. Gmail extension APIs
### 6.1. Execute gmail extension API (ws - /chat/{user_id}/{thread_id}/{max_recursion})
* Example code to handle Gmail extension API response
```python
import websockets
import json
import asyncio
import nest_asyncio

nest_asyncio.apply()

async def connect_to_server():
    uri = "ws://localhost:5001/gmail/chat/3fa85f64-5717-4562-b3fc-2c963f66afa6/abc/5"
    async with websockets.connect(uri) as websocket:
        # Send query to server
        await websocket.send("Summary latest emails by fetch emails tool")

        # Wait for a response(json) from the server
        response = await websocket.recv()
        data = json.loads(response)
        print("[Output] ", data["output"]) # output is tool_calls for human review if interrupt is true. If interrupt is false, output is a message
        
        
        if data['interrupted']:   
            print("\n-------------------------\n")

            # Human review: using "continue" to execute tool and "refuse" to end the process
            await websocket.send("continue")
            message_response = await websocket.recv()
            message_data = json.loads(message_response)
            print("[Output]", message_data["output"])
            
async def main():
    await connect_to_server()
    
# Run the client
asyncio.run(main())
```

* Output of the above code
```text
[Output]  {'question': 'Continue executing the tool call?', 'tool_calls': [{'name': 'GMAIL_FETCH_EMAILS', 'args': {'max_results': 5}, 'id': 'call_v0zJEHtW2Roz1hPe5dnQNwyW', 'type': 'tool_call'}]}

-------------------------

[Output] ['The latest emails retrieved include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about two new messages, another security alert from Google, a LinkedIn News Asia post about professional boundaries, and a Google Developer Program email about new features in Android Studio.']
```
### 6.2. Stream gmail extension API (ws - /stream/{user_id}/{thread_id}/{max_recursion})
* Example code to handle Stream Gmail extension API response
```python
import websockets
import json
import asyncio
import nest_asyncio

nest_asyncio.apply()

async def connect_to_server():
    uri = "ws://localhost:5001/gmail/stream/3fa85f64-5717-4562-b3fc-2c963f66afa6/abcdefghi/5"
    async with websockets.connect(uri) as websocket:
        # Send query to server
        await websocket.send("Summary latest emails by fetch emails tool")

        # Wait for a response(json) from the server
        call_tools_message = False # To check interrupt
        
        while True:
            line_response = await websocket.recv()
            dictionary = json.loads(line_response)
            
            if dictionary['event'] == 'data':
                data = json.loads(dictionary['data'])
                if isinstance(data, list) and len(data) > 0:
                    message = data[-1]
                    if message['type'] == 'ai':
                        if 'tool_calls' in message and len(message['tool_calls']) > 0:
                            call_tools_message = True
                            print(message['tool_calls'])
                        else:
                            print(message['content'])
                
            if dictionary['event'] == 'end':
                break
            
        
        if call_tools_message:   
            print("\n-------------------------\n")
            # Human review: using "continue" to execute tool and "refuse" to end the process
            await websocket.send("continue")
            
            while True:
                line_response = await websocket.recv()
                dictionary = json.loads(line_response)

                if dictionary['event'] == 'data':
                    data = json.loads(dictionary['data'])
                    if isinstance(data, list) and len(data) > 0:
                        message = data[-1]
                        if message['name'] is not None and message['name'].lower() == 'tool':
                            continue
                        if message['type'] == 'ai':
                            print(message['content'])

                if dictionary['event'] == 'end':
                    break

            
async def main():
    await connect_to_server()
    
# Run the client
asyncio.run(main())
```

* Output of the above code
```text
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {'max_results': 5}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {'max_results': 5}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]
[{'name': 'GMAIL_FETCH_EMAILS', 'args': {'max_results': 5}, 'id': 'call_FjJkm8iAlDVbPpRIYwmFuuA5', 'type': 'tool_call'}]

-------------------------


The
The latest
The latest emails
The latest emails retrieved
The latest emails retrieved by
The latest emails retrieved by the
The latest emails retrieved by the fetch
The latest emails retrieved by the fetch emails
The latest emails retrieved by the fetch emails tool
The latest emails retrieved by the fetch emails tool include
The latest emails retrieved by the fetch emails tool include a
The latest emails retrieved by the fetch emails tool include a security
The latest emails retrieved by the fetch emails tool include a security alert
The latest emails retrieved by the fetch emails tool include a security alert from
The latest emails retrieved by the fetch emails tool include a security alert from Google
The latest emails retrieved by the fetch emails tool include a security alert from Google about
The latest emails retrieved by the fetch emails tool include a security alert from Google about Com
The latest emails retrieved by the fetch emails tool include a security alert from Google about Compos
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account,
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a Linked
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates,
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features,
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a Linked
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post about
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post about setting
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post about setting professional
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post about setting professional boundaries
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post about setting professional boundaries.
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post about setting professional boundaries.
The latest emails retrieved by the fetch emails tool include a security alert from Google about Composio accessing a Google account, a LinkedIn notification about new messages and professional updates, a Google Developer Program email about upgrading Android Studio for AI features, and a LinkedIn News Asia post about setting professional boundaries.
```

## 7. User APIs

## 8. Thread APIs

## 9. Connected apps APIs

