# About the Ask Vasu AI Assistant

## What it is

Ask Vasu AI is the assistant on this portfolio website. It is a new personal project built for this portfolio. It is separate from the professional work documented in the experience and project pages, and it is not a claim about past employment.

## How it works

Visitor questions go from the React frontend to a FastAPI backend. The backend embeds the question with an OpenAI embedding model, searches a PostgreSQL database with the pgvector extension for relevant chunks of the approved portfolio knowledge base, and passes only those chunks to an OpenAI chat model with instructions to answer from the evidence and to say so when evidence is missing. Sources are returned with each answer. Conversation history is kept in the visitor's browser and is not stored on the server.

## Honest scope

The assistant answers only from the approved, sanitized portfolio knowledge base. It is an AI assistant representing Vasu Gadde, not Vasu himself.
