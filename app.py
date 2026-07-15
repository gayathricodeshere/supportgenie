import os
import json
import random
import chromadb
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# ---------- Setup (cached so it runs once) ----------
@st.cache_resource
def get_client():
    key = os.getenv("GROQ_API_KEY")
    if not key:
        st.error("GROQ_API_KEY not found. Check your .env file.")
        st.stop()
    return Groq(api_key=key)

@st.cache_resource
def get_kb():
    HELP_DOCS = [
        "Standard shipping takes 3-5 business days; express arrives next day.",
        "Returns are accepted within 30 days of delivery for a full refund.",
        "All electronics carry a 1-year manufacturer warranty against defects.",
        "Refunds are processed to the original payment method within 5-7 business days.",
        "Nimbus Prime members get free express shipping on all orders.",
    ]
    col = chromadb.Client().get_or_create_collection("nimbus_help")
    if col.count() == 0:
        col.add(documents=HELP_DOCS, ids=[f"d{i}" for i in range(len(HELP_DOCS))])
    return col

client = get_client()
kb = get_kb()

ORDERS = {
    "NIM-4821": {"status": "In transit", "eta": "2 days", "total": 89.99, "refundable": True},
    "NIM-3310": {"status": "Delivered", "eta": "-", "total": 45.00, "refundable": True},
    "NIM-9002": {"status": "Processing", "eta": "5 days", "total": 210.50, "refundable": False},
}

# ---------- Tools ----------
def lookup_order(oid):
    o = ORDERS.get(oid.upper().strip())
    return o and f"Order {oid}: {o['status']} (ETA {o['eta']}), total ${o['total']}." \
        or f"I couldn't find an order with ID {oid}."

def process_refund(oid):
    o = ORDERS.get(oid.upper().strip())
    if not o:
        return f"No order {oid} found to refund."
    if not o["refundable"]:
        return f"Sorry, order {oid} isn't eligible for a refund."
    return f"Refund of ${o['total']} initiated for {oid} — 5-7 business days."

def create_ticket(summary):
    return (f"I've escalated this to our team (ticket TCK-{random.randint(1000,9999)}). "
            "A human agent will follow up within 24 hours.")

# ---------- Router + RAG ----------
INTENTS = ["policy_question", "order_lookup", "refund_request", "escalate", "off_topic"]

def classify_intent(message):
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content":
                f"Classify into one intent: {INTENTS}. "
                'Return JSON: {"intent": "...", "order_id": "<id or null>"}'},
            {"role": "user", "content": message},
        ],
        temperature=0, response_format={"type": "json_object"},
    )
    return json.loads(resp.choices[0].message.content)

def answer_policy_question(question):
    res = kb.query(query_texts=[question], n_results=3)
    chunks = res["documents"][0]
    if not chunks or res["distances"][0][0] > 1.3:
        return "I'm not certain about that — I'll connect you with a human agent."
    context = "\n".join(f"[{i+1}] {c}" for i, c in enumerate(chunks))
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content":
                "You are SupportGenie for Nimbus. Answer ONLY from context, warmly and "
                "concisely, citing like [1]. If unknown, offer a human."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content

# ---------- Dispatcher with guardrails ----------
def handle_message(message):
    if st.session_state.get("pending_refund"):
        oid = st.session_state.pop("pending_refund")
        if message.strip().lower() in ("yes", "y", "confirm"):
            return process_refund(oid)
        return "Okay, I've cancelled that refund. Anything else?"

    route = classify_intent(message)
    intent, oid = route["intent"], route.get("order_id")

    if intent == "policy_question":
        return answer_policy_question(message)
    if intent == "order_lookup":
        return lookup_order(oid) if oid else "Sure — what's your order ID (like NIM-XXXX)?"
    if intent == "refund_request":
        if not oid:
            return "Happy to help — which order ID should I refund?"
        st.session_state.pending_refund = oid
        return f"You'd like a refund for {oid}. Shall I process it? (yes/no)"
    if intent == "escalate":
        return create_ticket(message)
    return ("I'm SupportGenie — I help with Nimbus orders, returns, shipping, and refunds. "
            "I can't help with that, but I'm glad to assist with your order!")

# ---------- UI ----------
st.set_page_config(page_title="SupportGenie", page_icon="🧞")
st.title("🧞 SupportGenie — Nimbus Support")
st.caption("Try: 'Where is order NIM-4821?', 'What's your return policy?', "
           "'I want a refund for NIM-3310'")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm SupportGenie. How can I help with your Nimbus order today?"}
    ]

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask about orders, returns, shipping, refunds..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = handle_message(prompt)
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})