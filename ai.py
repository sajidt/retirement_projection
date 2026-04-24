"""AI chat functionality using Ollama."""

import tkinter as tk
from tkinter import scrolledtext
import threading
import requests


def open_chat_window(root, initial_message=""):
    """
    Open a new window for AI chat using Ollama.
    
    Args:
        root: Tkinter root window
        initial_message: Initial text to preload in the input field
    """
    chat_window = tk.Toplevel(root)
    chat_window.title("AI Chat")
    chat_window.geometry("600x400")
    
    # Initialize conversation
    chat_window.conversation = [{"role": "system", "content": "Act as a financial advisor."}]
    
    # Input frame
    input_frame = tk.Frame(chat_window, height=50)  # Fixed height for input area
    input_frame.pack(side="bottom", fill="x", padx=5, pady=5)
    
    input_entry = tk.Entry(input_frame, font=("Courier New", 10))
    input_entry.pack(side=tk.LEFT, expand=True, fill="x")
    
    send_button = tk.Button(input_frame, text="Send", command=lambda: send_message(chat_window, chat_history, input_entry))
    send_button.pack(side=tk.RIGHT)
    
    # Bind Enter key to send
    input_entry.bind("<Return>", lambda event: send_message(chat_window, chat_history, input_entry))
    
    # Chat history
    chat_history = scrolledtext.ScrolledText(chat_window, wrap=tk.WORD, font=("Courier New", 10))
    chat_history.pack(expand=True, fill="both")
    chat_history.insert(tk.END, "Welcome to AI Chat! Ask me anything about retirement planning.\n\n")
    chat_history.config(state=tk.DISABLED)
    
    # If initial message, send it automatically
    if initial_message:
        chat_window.conversation.append({"role": "user", "content": initial_message})
        def initial_query():
            ai_message = query_ollama(chat_window.conversation)
            chat_window.conversation.append({"role": "assistant", "content": ai_message})
            chat_history.config(state=tk.NORMAL)
            chat_history.insert(tk.END, f"AI: {ai_message}\n\n")
            chat_history.config(state=tk.DISABLED)
            chat_history.see(tk.END)
        threading.Thread(target=initial_query, daemon=True).start()

    


def send_message(chat_window, chat_history, input_entry):
    """
    Send message to Ollama and display response.
    
    Args:
        chat_window: The chat window with conversation attribute
        chat_history: ScrolledText for chat history
        input_entry: Entry widget for user input
    """
    user_message = input_entry.get().strip()
    if not user_message:
        return
    
    # Clear input
    input_entry.delete(0, tk.END)
    
    # Add user message to conversation and history
    chat_window.conversation.append({"role": "user", "content": user_message})
    chat_history.config(state=tk.NORMAL)
    chat_history.insert(tk.END, f"You: {user_message}\n")
    chat_history.config(state=tk.DISABLED)
    chat_history.see(tk.END)
    
    # Send to Ollama in a thread
    def query():
        ai_message = query_ollama(chat_window.conversation)
        chat_window.conversation.append({"role": "assistant", "content": ai_message})
        chat_history.config(state=tk.NORMAL)
        chat_history.insert(tk.END, f"AI: {ai_message}\n\n")
        chat_history.config(state=tk.DISABLED)
        chat_history.see(tk.END)
    
    threading.Thread(target=query, daemon=True).start()


def query_ollama(conversation):
    """
    Send the conversation to Ollama and get the response.
    
    Args:
        conversation: List of message dicts with 'role' and 'content'
    
    Returns:
        str: The AI response
    """
    # Build the prompt from conversation
    prompt = ""
    for msg in conversation:
        if msg["role"] == "system":
            prompt += f"System: {msg['content']}\n\n"
        elif msg["role"] == "user":
            prompt += f"User: {msg['content']}\n\n"
        elif msg["role"] == "assistant":
            prompt += f"Assistant: {msg['content']}\n\n"
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3-chatqa:latest",
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("response", "No response")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}. Make sure Ollama is running."