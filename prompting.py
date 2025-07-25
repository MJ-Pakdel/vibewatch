from langchain.prompts import ChatPromptTemplate

SYSTEM_PROMPT = (
    "You are VibeWatch, a movie recommendation assistant. "
    "Based on the user's CURRENT CONTEXT (mood, social setting, location, attention level, etc.), "
    "choose UP TO 10 movies (ideally 8–10) from the given candidate list. Explain briefly (1–2 sentences) why each fits the context. "
    "Do NOT hallucinate titles."
)

USER_PROMPT = (
    "USER CONTEXT (free text):\n{user_query}\n\n"
    "CANDIDATE MOVIES (JSON list of dicts):\n{retrieved_docs}\n\n"
    "Return JSON:\n[\n  {{\"title\": \"...\", \"reason\": \"...\"}},\n  ...\n]"
)

# Build ChatPromptTemplate for convenience
PROMPT_TEMPLATE: ChatPromptTemplate = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ]
) 