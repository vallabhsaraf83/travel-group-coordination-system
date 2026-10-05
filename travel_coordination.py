import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# --- SQLite Connection & Table Setup ---
def get_connection():
    return sqlite3.connect("travel_coordinator.db")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS travel_groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            destination TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            estimated_budget REAL DEFAULT 0.0,
            status TEXT DEFAULT 'Planning'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            role TEXT DEFAULT 'Member',
            emergency_contact TEXT,
            FOREIGN KEY (group_id) REFERENCES travel_groups(group_id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Main App ---
class TravelGroupCoordinatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Travel Coordinator")
        self.root.geometry("800x600")

        self.selected_group_id = None

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self.groups_tab = ttk.Frame(self.notebook)
        self.members_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.groups_tab, text="Groups")
        self.notebook.add(self.members_tab, text="Members")

        self.build_groups_tab()
        self.build_members_tab()
        self.refresh_groups()

    def build_groups_tab(self):
        form_frame = ttk.LabelFrame(self.groups_tab, text="Group Details", padding=10)
        form_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.name_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.budget_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Planning")

        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky="w")
        ttk.Entry(form_frame, textvariable=self.name_var).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(form_frame, text="Destination:").grid(row=1, column=0, sticky="w")
        ttk.Entry(form_frame, textvariable=self.dest_var).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(form_frame, text="Budget:").grid(row=2, column=0, sticky="w")
        ttk.Entry(form_frame, textvariable=self.budget_var).grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(form_frame, text="Status:").grid(row=3, column=0, sticky="w")
        ttk.Combobox(form_frame, textvariable=self.status_var, values=("Planning", "Confirmed", "Completed"), state="readonly").grid(row=3, column=1, padx=5, pady=2)

        btn_box = ttk.Frame(form_frame)
        btn_box.grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(btn_box, text="Add", command=self.add_group).pack(side="left", padx=2)
        ttk.Button(btn_box, text="Delete", command=self.delete_group).pack(side="left", padx=2)

        # Table
        cols = ("ID", "Name", "Destination", "Budget", "Status")
        self.group_tree = ttk.Treeview(self.groups_tab, columns=cols, show="headings", height=8)
        for c in cols:
            self.group_tree.heading(c, text=c)
            self.group_tree.column(c, width=70)
        self.group_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.group_tree.bind("<<TreeviewSelect>>", self.on_group_select)

    def add_group(self):
        name = self.name_var.get().strip()
        dest = self.dest_var.get().strip()
        budget = self.budget_var.get().strip() or "0"

        if not name or not dest:
            messagebox.showwarning("Warning", "Name & Destination required!")
            return

        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO travel_groups (group_name, destination, start_date, end_date, estimated_budget, status) VALUES (?, ?, '2026-10-10', '2026-10-15', ?, ?)", 
                  (name, dest, float(budget), self.status_var.get()))
        conn.commit()
        conn.close()
        self.name_var.set("")
        self.dest_var.set("")
        self.budget_var.set("")
        self.refresh_groups()

    def delete_group(self):
        if not self.selected_group_id:
            return
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM travel_groups WHERE group_id = ?", (self.selected_group_id,))
        conn.commit()
        conn.close()
        self.refresh_groups()

    def refresh_groups(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT group_id, group_name, destination, estimated_budget, status FROM travel_groups")
        rows = c.fetchall()
        self.group_tree.delete(*self.group_tree.get_children())
        for r in rows:
            self.group_tree.insert("", "end", values=r)
        conn.close()
        self.populate_groups_cb()

    def on_group_select(self, event):
        sel = self.group_tree.focus()
        if sel:
            val = self.group_tree.item(sel, "values")
            self.selected_group_id = val[0]

    def build_members_tab(self):
        form = ttk.LabelFrame(self.members_tab, text="Add Member", padding=10)
        form.pack(fill="x", padx=5, pady=5)

        ttk.Label(form, text="Group:").grid(row=0, column=0)
        self.group_cb = ttk.Combobox(form, state="readonly")
        self.group_cb.grid(row=0, column=1, padx=5, pady=2)
        self.group_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_members())

        ttk.Label(form, text="Name:").grid(row=1, column=0)
        self.m_name = tk.StringVar()
        ttk.Entry(form, textvariable=self.m_name).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(form, text="Phone:").grid(row=2, column=0)
        self.m_phone = tk.StringVar()
        ttk.Entry(form, textvariable=self.m_phone).grid(row=2, column=1, padx=5, pady=2)

        ttk.Button(form, text="Add Member", command=self.add_member).grid(row=3, column=0, columnspan=2, pady=5)

        cols = ("ID", "Name", "Phone")
        self.member_tree = ttk.Treeview(self.members_tab, columns=cols, show="headings", height=8)
        for c in cols:
            self.member_tree.heading(c, text=c)
            self.member_tree.column(c, width=100)
        self.member_tree.pack(fill="both", expand=True, padx=5, pady=5)

    def populate_groups_cb(self):
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT group_id, group_name FROM travel_groups")
        self.groups_dict = {f"{r[0]} - {r[1]}": r[0] for r in c.fetchall()}
        self.group_cb["values"] = list(self.groups_dict.keys())
        conn.close()

    def add_member(self):
        grp = self.group_cb.get()
        if not grp or not self.m_name.get():
            return
        gid = self.groups_dict[grp]
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO group_members (group_id, full_name, contact_number) VALUES (?, ?, ?)",
                  (gid, self.m_name.get(), self.m_phone.get()))
        conn.commit()
        conn.close()
        self.m_name.set("")
        self.m_phone.set("")
        self.refresh_members()

    def refresh_members(self):
        grp = self.group_cb.get()
        if not grp:
            return
        gid = self.groups_dict[grp]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT member_id, full_name, contact_number FROM group_members WHERE group_id = ?", (gid,))
        rows = c.fetchall()
        self.member_tree.delete(*self.member_tree.get_children())
        for r in rows:
            self.member_tree.insert("", "end", values=r)
        conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = TravelGroupCoordinatorApp(root)
    root.mainloop()
