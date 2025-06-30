import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, scrolledtext
import shutil
import os
import threading
import importlib.util

# Import query_rag from query_data.py
def import_query_rag():
    spec = importlib.util.spec_from_file_location("query_data", "query_data.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.query_rag

# Run populate_database.py as a script
def run_populate_database():
    spec = importlib.util.spec_from_file_location("populate_database", "populate_database.py")
    module = importlib.util.module_from_spec(spec)
    module.main()

DATA_DIR = "data"

class ChatGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RAG Chat GUI")
        self.query_rag = import_query_rag()
        self.chat_history = []  # List of (user, bot) tuples
        self.selected_chat = None
        self.chats = []  # List of chat sessions
        self.files_to_add = []
        self.setup_ui()
        self.new_chat()  # Automatically create a new chat on startup

    def setup_ui(self):
        self.root.geometry("900x600")
        self.root.configure(bg="#23272f")
        self.left_frame = tk.Frame(self.root, width=250, bg="#181a20")
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.right_frame = tk.Frame(self.root, bg="#23272f")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # New Chat button (on top)
        self.new_chat_btn = tk.Button(self.left_frame, text="New Chat", command=self.new_chat, bg="#6272a4", fg="#f8f8f2", activebackground="#44475a", activeforeground="#f8f8f2", borderwidth=0)
        self.new_chat_btn.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(10, 5))

        # Chat history listbox
        self.chat_listbox = tk.Listbox(self.left_frame, bg="#23272f", fg="#f8f8f2", selectbackground="#44475a", selectforeground="#f8f8f2", highlightthickness=0, borderwidth=0)
        self.chat_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,0))
        self.chat_listbox.bind('<<ListboxSelect>>', self.on_chat_select)

        # Add File button
        self.add_file_btn = tk.Button(self.left_frame, text="Add File", command=self.add_file, bg="#44475a", fg="#f8f8f2", activebackground="#6272a4", activeforeground="#f8f8f2", borderwidth=0)
        self.add_file_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.refresh_btn = tk.Button(self.left_frame, text="Refresh Database", command=self.refresh_database, bg="#44475a", fg="#f8f8f2", activebackground="#6272a4", activeforeground="#f8f8f2", borderwidth=0)
        self.refresh_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0,5))

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(self.right_frame, state='disabled', wrap=tk.WORD, bg="#282a36", fg="#f8f8f2", insertbackground="#f8f8f2", borderwidth=0)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10,0))

        # Entry and send button
        self.entry_frame = tk.Frame(self.right_frame, bg="#23272f")
        self.entry_frame.pack(fill=tk.X, padx=10, pady=10)
        self.user_entry = tk.Entry(self.entry_frame, bg="#282a36", fg="#f8f8f2", insertbackground="#f8f8f2", borderwidth=0)
        self.user_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.user_entry.bind('<Return>', lambda event: self.send_message())  # Send on Enter
        self.send_btn = tk.Button(self.entry_frame, text="Send", command=self.send_message, bg="#44475a", fg="#f8f8f2", activebackground="#6272a4", activeforeground="#f8f8f2", borderwidth=0)
        self.send_btn.pack(side=tk.RIGHT)

    def new_chat(self):
        # Create a new chat session and add it to the list
        chat_name = f"Chat {len(self.chats) + 1}"
        self.chats.append({'name': chat_name, 'history': []})
        self.chat_listbox.insert(tk.END, chat_name)
        self.chat_listbox.selection_clear(0, tk.END)
        self.chat_listbox.selection_set(tk.END)
        self.selected_chat = len(self.chats) - 1
        self.chat_history = []
        self.update_chat_display()

    def add_file(self):
        files = filedialog.askopenfilenames(title="Select files to add")
        if not files:
            return
        os.makedirs(DATA_DIR, exist_ok=True)
        for file in files:
            try:
                shutil.copy(file, DATA_DIR)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add file: {file}\n{e}")
        messagebox.showinfo("Files Added", f"{len(files)} file(s) added to data folder.")

    def refresh_database(self):
        messagebox.showinfo("Populating Database", "Populating the Chroma database with files in the data folder...")
        threading.Thread(target=self.populate_db_thread).start()

    def populate_db_thread(self):
        try:
            run_populate_database()
            messagebox.showinfo("Database Updated", "Chroma database populated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to populate database: {e}")

    def send_message(self):
        user_text = self.user_entry.get().strip()
        if not user_text:
            return
        self.user_entry.delete(0, tk.END)
        self.append_chat(f"You: {user_text}\n")
        threading.Thread(target=self.get_bot_response, args=(user_text,)).start()

    def get_bot_response(self, user_text):
        try:
            response = self.query_rag(user_text)
        except Exception as e:
            response = f"[Error: {e}]"
        self.append_chat(f"Bot: {response}\n")

    def update_chat_display(self):
        self.chat_display.config(state='normal')
        self.chat_display.delete(1.0, tk.END)
        if self.selected_chat is not None and self.chats:
            for entry in self.chats[self.selected_chat]['history']:
                self.chat_display.insert(tk.END, entry)
        self.chat_display.config(state='disabled')

    def append_chat(self, text):
        if self.selected_chat is not None and self.chats:
            self.chats[self.selected_chat]['history'].append(text)
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, text)
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')

    def on_chat_select(self, event):
        selection = self.chat_listbox.curselection()
        if selection:
            self.selected_chat = selection[0]
            self.chat_history = self.chats[self.selected_chat]['history']
            self.update_chat_display()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatGUI(root)
    root.mainloop()
