"""Missing Persons Analysis — India 2023 | GUI App"""

import sqlite3, os, warnings
import pandas as pd, matplotlib.pyplot as plt, matplotlib.patches as mpatches
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

warnings.filterwarnings("ignore")

# ── DATA ─────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
df   = pd.read_csv(os.path.join(BASE, "Missing_person.csv"))
df["total"]  = df["Children_Total_Missing"] + df["Women_Total_Missing"]
df["c_rate"] = (df["Children_Recovered_2023"] / df["Children_Total_Missing"].replace(0,1) * 100).round(1)
df["w_rate"] = (df["Women_Recovered_2023"]    / df["Women_Total_Missing"].replace(0,1)    * 100).round(1)
conn = sqlite3.connect(":memory:"); df.to_sql("mp", conn, if_exists="replace", index=False)

C   = {"ch":"#4C72B0","wo":"#DD8452","red":"#C44E52","grn":"#55A868","pur":"#8172B2","bg":"#F8F9FA"}
fmt = plt.FuncFormatter(lambda v,_: f"{int(v):,}")
BG, BG2 = "#1e1e2e", "#2a2a3e"

def sax(ax, t, xl="", yl=""):
    ax.set_title(t, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel(xl,fontsize=9); ax.set_ylabel(yl,fontsize=9)
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.set_facecolor(C["bg"]); ax.tick_params(labelsize=8)

def lbl(parent, text, **kw): return tk.Label(parent, text=text, bg=kw.pop("bg",BG2), fg=kw.pop("fg","white"), **kw)
def btn(parent, text, cmd, color="#4C72B0", **kw):
    return tk.Button(parent, text=text, command=cmd, bg=color, fg="white", relief="flat",
                     font=("Helvetica",9,"bold"), padx=8, pady=3, **kw)

# ── APP ──────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Missing Persons Analysis — India 2023")
        self.geometry("1200x750"); self.configure(bg=BG)

        lbl(self, "🔍  Missing Persons Data Analysis — India 2023",
            font=("Helvetica",15,"bold"), pady=8).pack(fill="x")

        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG2, foreground="white", padding=[14,6], font=("Helvetica",10,"bold"))
        s.map("TNotebook.Tab", background=[("selected","#4C72B0")])
        s.configure("Treeview", background=BG2, foreground="white", fieldbackground=BG2, rowheight=26, font=("Helvetica",9))
        s.configure("Treeview.Heading", background="#4C72B0", foreground="white", font=("Helvetica",9,"bold"))
        s.map("Treeview", background=[("selected","#4C72B0")])

        nb = ttk.Notebook(self); nb.pack(fill="both", expand=True, padx=10, pady=6)
        tabs = [tk.Frame(nb, bg=BG) for _ in range(5)]
        for t, name in zip(tabs, ["🔎 Search & Filter","📊 Charts","🗄️ SQL Queries","📈 Statistics","✏️ Manage Data"]):
            nb.add(t, text=name)
        self._search(tabs[0]); self._charts(tabs[1]); self._sql(tabs[2]); self._stats(tabs[3]); self._manage(tabs[4])

    # ── TAB 1: SEARCH ────────────────────────────────────────────────
    def _search(self, tab):
        top = tk.Frame(tab, bg=BG2, pady=8, padx=10); top.pack(fill="x")
        lbl(top,"Search State:", font=("Helvetica",10,"bold")).grid(row=0,column=0,padx=5)
        self.sv = tk.StringVar(); self.sv.trace("w", lambda *_: self._fill())
        tk.Entry(top, textvariable=self.sv, width=20, font=("Helvetica",11),
                 bg="#3a3a5e", fg="white", insertbackground="white", relief="flat"
                 ).grid(row=0,column=1,padx=5,ipady=4)
        lbl(top,"Sort by:", font=("Helvetica",10,"bold")).grid(row=0,column=2,padx=8)
        self.sortv = tk.StringVar(value="Total ↓")
        cb = ttk.Combobox(top, textvariable=self.sortv, width=20, state="readonly",
                          values=["Total ↓","Children ↓","Women ↓","C-Rate ↓","W-Rate ↓","State A-Z"])
        cb.grid(row=0,column=3,padx=5); cb.bind("<<ComboboxSelected>>", lambda _: self._fill())
        btn(top,"⟳ Reset", self._reset, "#C44E52").grid(row=0,column=4,padx=10)

        cols = ("State","C-Missing","C-Recovered","C-Rate%","W-Missing","W-Recovered","W-Rate%","Total")
        self.tree = ttk.Treeview(tab, columns=cols, show="headings", height=22)
        for col,w in zip(cols,[155,115,130,75,110,125,75,110]):
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(10,0), pady=8)
        sb.pack(side="left", fill="y", pady=8)
        self.tree.bind("<<TreeviewSelect>>", self._detail)

        self.dp = tk.Frame(tab, bg=BG2, width=210); self.dp.pack(side="right", fill="y", padx=10, pady=8)
        self.dl = lbl(self.dp, "Click a row\nto see details", fg="#aaa", justify="left", wraplength=190)
        self.dl.pack(pady=20, padx=8)
        self._fill()

    def _fill(self):
        sm = {"Total ↓":("total",False),"Children ↓":("Children_Missing_2023",False),
              "Women ↓":("Women_Missing_2023",False),"C-Rate ↓":("c_rate",False),
              "W-Rate ↓":("w_rate",False),"State A-Z":("State/UT",True)}
        col, asc = sm[self.sortv.get()]
        data = df[df["State/UT"].str.lower().str.contains(self.sv.get().lower())].sort_values(col, ascending=asc)
        self.tree.delete(*self.tree.get_children())
        for _,r in data.iterrows():
            self.tree.insert("","end", values=(r["State/UT"],f"{int(r['Children_Missing_2023']):,}",
                f"{int(r['Children_Recovered_2023']):,}",f"{r['c_rate']}%",
                f"{int(r['Women_Missing_2023']):,}",f"{int(r['Women_Recovered_2023']):,}",
                f"{r['w_rate']}%",f"{int(r['total']):,}"))

    def _reset(self): self.sv.set(""); self.sortv.set("Total ↓"); self._fill()

    def _detail(self, _):
        sel = self.tree.focus()
        if not sel: return
        r = df[df["State/UT"]==self.tree.item(sel)["values"][0]].iloc[0]
        self.dl.config(fg="white", text=(
            f"📍 {r['State/UT']}\n\n👦 Children\n  Missing : {int(r['Children_Missing_2023']):,}\n"
            f"  Recovered: {int(r['Children_Recovered_2023']):,}\n  Rate: {r['c_rate']}%\n"
            f"  Unrecov.: {int(r['Children_Unrecovered_End_2023']):,}\n\n"
            f"👩 Women\n  Missing : {int(r['Women_Missing_2023']):,}\n"
            f"  Recovered: {int(r['Women_Recovered_2023']):,}\n  Rate: {r['w_rate']}%\n"
            f"  Unrecov.: {int(r['Women_Unrecovered_End_2023']):,}\n\n📊 Total: {int(r['total']):,}"))

    # ── TAB 2: CHARTS ────────────────────────────────────────────────
    def _charts(self, tab):
        top = tk.Frame(tab, bg=BG2, pady=6); top.pack(fill="x")
        lbl(top,"Chart:", font=("Helvetica",10,"bold")).pack(side="left", padx=10)
        self.cv = tk.StringVar(value="Top 10 Total Missing")
        ttk.Combobox(top, textvariable=self.cv, width=28, state="readonly",
                     values=["Top 10 Total Missing","Children vs Women","Women Recovery Rate",
                             "National Overview","Top 5 Unrecovered","Missing Trend"]
                     ).pack(side="left", padx=5)
        btn(top,"▶ Show", self._draw, "#55A868").pack(side="left", padx=8)
        self.cf = tk.Frame(tab, bg=BG); self.cf.pack(fill="both", expand=True, padx=10, pady=5)
        self._draw()

    def _draw(self):
        for w in self.cf.winfo_children(): w.destroy()
        n = self.cv.get(); fig, ax = plt.subplots(figsize=(10,5)); fig.patch.set_facecolor(C["bg"])

        if n == "Top 10 Total Missing":
            t = df.nlargest(10,"total"); bars = ax.barh(t["State/UT"][::-1], t["total"][::-1], color=C["pur"], edgecolor="white")
            [ax.text(b.get_width()+200,b.get_y()+b.get_height()/2,f'{int(b.get_width()):,}',va='center',fontsize=8) for b in bars]
            ax.xaxis.set_major_formatter(fmt); sax(ax,"Top 10 States — Total Missing 2023","Count","State")

        elif n == "Children vs Women":
            t=df.nlargest(12,"Children_Total_Missing"); x=range(len(t)); w=0.4
            ax.bar([i-w/2 for i in x],t["Children_Missing_2023"],w,label="Children",color=C["ch"],edgecolor="white")
            ax.bar([i+w/2 for i in x],t["Women_Missing_2023"],   w,label="Women",   color=C["wo"],edgecolor="white")
            ax.set_xticks(list(x)); ax.set_xticklabels(t["State/UT"],rotation=35,ha="right",fontsize=8)
            ax.yaxis.set_major_formatter(fmt); ax.legend(); sax(ax,"Children vs Women Missing 2023","State","Count")

        elif n == "Women Recovery Rate":
            ds=df.sort_values("w_rate"); bars=ax.barh(ds["State/UT"],ds["w_rate"],
                color=[C["red"] if r<50 else C["grn"] for r in ds["w_rate"]],edgecolor="white")
            [ax.text(b.get_width()+.5,b.get_y()+b.get_height()/2,f'{b.get_width():.1f}%',va='center',fontsize=7) for b in bars]
            ax.axvline(50,color="black",ls="--",lw=1,alpha=.5)
            ax.legend(handles=[mpatches.Patch(color=C["red"],label="<50% Critical"),mpatches.Patch(color=C["grn"],label=">=50% Good")])
            sax(ax,"Women Recovery Rate (%) by State","Rate (%)","State"); fig.set_size_inches(10,8)

        elif n == "National Overview":
            plt.close(); fig,axes=plt.subplots(1,2,figsize=(10,5)); fig.patch.set_facecolor(C["bg"])
            cu=df["Children_Unrecovered_End_2023"].sum(); wu=df["Women_Unrecovered_End_2023"].sum()
            axes[0].pie([cu,wu],labels=["Children","Women"],autopct="%1.1f%%",colors=[C["ch"],C["wo"]],
                        explode=(.05,.05),startangle=140,textprops={"fontsize":11})
            axes[0].set_title("Unrecovered Share",fontsize=11,fontweight="bold")
            cr=df["Children_Recovered_2023"].sum(); wr=df["Women_Recovered_2023"].sum()
            axes[1].bar([0,1],[cr,wr],label="Recovered",color=C["grn"],edgecolor="white")
            axes[1].bar([0,1],[cu,wu],bottom=[cr,wr],label="Unrecovered",color=C["red"],edgecolor="white")
            axes[1].set_xticks([0,1]); axes[1].set_xticklabels(["Children","Women"])
            axes[1].yaxis.set_major_formatter(fmt); axes[1].legend(); axes[1].set_facecolor(C["bg"])
            axes[1].spines["top"].set_visible(False); axes[1].spines["right"].set_visible(False)
            axes[1].set_title("Recovery Status",fontsize=11,fontweight="bold")
            FigureCanvasTkAgg(fig,self.cf).get_tk_widget().pack(fill="both",expand=True); return

        elif n == "Top 5 Unrecovered":
            t5=df.nlargest(5,"Children_Unrecovered_End_2023"); bars=ax.bar(t5["State/UT"],t5["Children_Unrecovered_End_2023"],color=C["red"],edgecolor="white")
            [ax.text(b.get_x()+b.get_width()/2,b.get_height()+50,f'{int(b.get_height()):,}',ha='center',fontsize=9,fontweight="bold") for b in bars]
            ax.set_xticklabels(t5["State/UT"],rotation=15,ha="right"); ax.yaxis.set_major_formatter(fmt)
            sax(ax,"Top 5 — Unrecovered Children (End 2023)","State","Count")

        elif n == "Missing Trend":
            ds=df.sort_values("Children_Missing_2023",ascending=False)
            ax.plot(ds["State/UT"],ds["Children_Missing_2023"],marker="o",color=C["ch"],lw=2,ms=5)
            ax.fill_between(range(len(ds)),ds["Children_Missing_2023"].values,alpha=.15,color=C["ch"])
            ax.set_xticks(range(len(ds))); ax.set_xticklabels(ds["State/UT"],rotation=45,ha="right",fontsize=7.5)
            ax.yaxis.set_major_formatter(fmt); sax(ax,"Children Missing 2023 — State Trend","State","Count")

        plt.tight_layout()
        c = FigureCanvasTkAgg(fig, self.cf); c.draw(); c.get_tk_widget().pack(fill="both", expand=True)

    # ── TAB 3: SQL ───────────────────────────────────────────────────
    def _sql(self, tab):
        top = tk.Frame(tab, bg=BG2, pady=6, padx=10); top.pack(fill="x")
        lbl(top,"SQL:", font=("Helvetica",10,"bold")).pack(side="left")
        self.se = tk.Text(top, height=3, width=68, font=("Courier",10), bg="#3a3a5e",
                          fg="white", insertbackground="white", relief="flat")
        self.se.pack(side="left", padx=8, ipady=4)
        self.se.insert("end",'SELECT "State/UT", total FROM mp ORDER BY total DESC LIMIT 10')
        btn(top,"▶ Run", self._run, "#55A868").pack(side="left", padx=5)

        pf = tk.Frame(tab, bg=BG); pf.pack(fill="x", padx=10, pady=4)
        lbl(pf,"Quick:", fg="#aaa", bg=BG, font=("Helvetica",9)).pack(side="left")
        for label,sql in [
            ("Top 10",   'SELECT "State/UT", total FROM mp ORDER BY total DESC LIMIT 10'),
            ("Recovery", 'SELECT "State/UT", c_rate, w_rate FROM mp ORDER BY c_rate DESC'),
            ("Unrecov.", 'SELECT "State/UT", Children_Unrecovered_End_2023, Women_Unrecovered_End_2023 FROM mp ORDER BY Women_Unrecovered_End_2023 DESC'),
            ("Totals",   'SELECT SUM(Children_Missing_2023) cm, SUM(Women_Missing_2023) wm, SUM(Children_Recovered_2023) cr, SUM(Women_Recovered_2023) wr FROM mp'),
            ("Zero",     'SELECT "State/UT" FROM mp WHERE Children_Missing_2023=0')]:
            btn(pf, label, lambda s=sql: (self.se.delete("1.0","end"), self.se.insert("end",s), self._run())).pack(side="left",padx=3)

        self.sr = tk.Text(tab, font=("Courier",10), bg=BG2, fg="#00ff99", relief="flat", state="disabled")
        self.sr.pack(fill="both", expand=True, padx=10, pady=8)
        self._run()

    def _run(self):
        try: out = pd.read_sql(self.se.get("1.0","end").strip(), conn).to_string(index=False)
        except Exception as e: out = f"[ERROR] {e}"
        self.sr.config(state="normal"); self.sr.delete("1.0","end"); self.sr.insert("end",out); self.sr.config(state="disabled")

    # ── TAB 4: STATS ─────────────────────────────────────────────────
    def _stats(self, tab):
        cr = df["Children_Recovered_2023"].sum()/df["Children_Missing_2023"].sum()*100
        wr = df["Women_Recovered_2023"].sum()/df["Women_Missing_2023"].sum()*100
        cards = [("Total States","28"),("Children Missing",f"{df['Children_Missing_2023'].sum():,}"),
                 ("Children Recovered",f"{df['Children_Recovered_2023'].sum():,}"),("C-Rate",f"{cr:.1f}%"),
                 ("Women Missing",f"{df['Women_Missing_2023'].sum():,}"),("Women Recovered",f"{df['Women_Recovered_2023'].sum():,}"),
                 ("W-Rate",f"{wr:.1f}%"),("Still Unrecovered",f"{df['Children_Unrecovered_End_2023'].sum()+df['Women_Unrecovered_End_2023'].sum():,}"),
                 ("Most C-Missing",df.loc[df['Children_Missing_2023'].idxmax(),'State/UT']),
                 ("Most W-Missing",df.loc[df['Women_Missing_2023'].idxmax(),'State/UT'])]

        cf = tk.Frame(tab, bg=BG); cf.pack(fill="x", padx=15, pady=12)
        for i,(label,val) in enumerate(cards):
            bg = ["#4C72B0","#DD8452","#55A868","#8172B2","#C44E52"][i%5]
            card = tk.Frame(cf, bg=bg, padx=12, pady=8); card.grid(row=i//5, column=i%5, padx=6, pady=6, sticky="nsew")
            tk.Label(card, text=label, bg=bg, fg="white", font=("Helvetica",8)).pack()
            tk.Label(card, text=val,   bg=bg, fg="white", font=("Helvetica",11,"bold")).pack()

        lbl(tab,"── Descriptive Statistics ──", font=("Helvetica",11,"bold")).pack(pady=(8,4))
        cols = ["Children_Missing_2023","Children_Recovered_2023","Women_Missing_2023","Women_Recovered_2023"]
        txt = tk.Text(tab, font=("Courier",10), bg=BG2, fg="#00ff99", relief="flat", height=11)
        txt.pack(fill="both", expand=True, padx=15, pady=(0,12))
        txt.insert("end", df[cols].describe().round(1).to_string()); txt.config(state="disabled")

    # ── TAB 5: MANAGE DATA ───────────────────────────────────────────
    def _manage(self, tab):
        # ── Header
        hdr = tk.Frame(tab, bg="#4C72B0", pady=6); hdr.pack(fill="x")
        tk.Label(hdr, text="✏️  Manage Dataset — Add / Modify / Delete Records",
                 bg="#4C72B0", fg="white", font=("Helvetica",12,"bold")).pack()

        body = tk.Frame(tab, bg=BG); body.pack(fill="both", expand=True, padx=10, pady=8)

        # ── LEFT: Record table for selection
        left = tk.Frame(body, bg=BG); left.pack(side="left", fill="both", expand=True)
        lbl(left, "📋  All Records  (click to select)", bg=BG, font=("Helvetica",10,"bold")).pack(anchor="w", pady=(0,4))

        mgcols = ("State","C-Miss","C-Rec","W-Miss","W-Rec")
        self.mg_tree = ttk.Treeview(left, columns=mgcols, show="headings", height=20)
        for col, w in zip(mgcols, [170, 100, 100, 100, 100]):
            self.mg_tree.heading(col, text=col); self.mg_tree.column(col, width=w, anchor="center")
        mgsb = ttk.Scrollbar(left, orient="vertical", command=self.mg_tree.yview)
        self.mg_tree.configure(yscrollcommand=mgsb.set)
        self.mg_tree.pack(side="left", fill="both", expand=True)
        mgsb.pack(side="left", fill="y")
        self.mg_tree.bind("<<TreeviewSelect>>", self._mg_select)
        self._mg_refresh_tree()

        # ── RIGHT: Form panel
        right = tk.Frame(body, bg=BG2, width=320, padx=16, pady=12)
        right.pack(side="right", fill="y", padx=(10,0))
        right.pack_propagate(False)

        lbl(right, "📝  Record Form", font=("Helvetica",11,"bold"), bg=BG2).pack(anchor="w", pady=(0,10))

        # Field definitions: (label, internal_key, csv_col_name)
        self._mg_fields = [
            ("State / UT",               "state",    "State/UT"),
            ("Children Missing 2023",    "cm23",     "Children_Missing_2023"),
            ("Children Recovered 2023",  "cr23",     "Children_Recovered_2023"),
            ("Children Unrecovered",     "cu23",     "Children_Unrecovered_End_2023"),
            ("Children Total Missing",   "cttl",     "Children_Total_Missing"),
            ("Women Missing 2023",       "wm23",     "Women_Missing_2023"),
            ("Women Recovered 2023",     "wr23",     "Women_Recovered_2023"),
            ("Women Unrecovered",        "wu23",     "Women_Unrecovered_End_2023"),
            ("Women Total Missing",      "wttl",     "Women_Total_Missing"),
        ]
        self._mg_vars = {}
        for label, key, _ in self._mg_fields:
            row = tk.Frame(right, bg=BG2); row.pack(fill="x", pady=3)
            tk.Label(row, text=label+":", bg=BG2, fg="#aaaacc",
                     font=("Helvetica",8), width=22, anchor="w").pack(side="left")
            var = tk.StringVar()
            tk.Entry(row, textvariable=var, bg="#3a3a5e", fg="white",
                     insertbackground="white", relief="flat",
                     font=("Helvetica",9), width=14).pack(side="left", ipady=3, padx=(4,0))
            self._mg_vars[key] = var

        # ── Status message
        self._mg_status = tk.StringVar(value="")
        tk.Label(right, textvariable=self._mg_status, bg=BG2, fg="#00ff99",
                 font=("Helvetica",8), wraplength=280, justify="left").pack(pady=(8,4))

        # ── Action buttons
        btnbar = tk.Frame(right, bg=BG2); btnbar.pack(fill="x", pady=(6,2))
        btn(btnbar, "➕  Add Record",    self._mg_add,    "#55A868").pack(fill="x", pady=3)
        btn(btnbar, "💾  Save Changes",  self._mg_modify, "#4C72B0").pack(fill="x", pady=3)
        btn(btnbar, "🗑️  Delete Record", self._mg_delete, "#C44E52").pack(fill="x", pady=3)
        btn(btnbar, "🧹  Clear Form",    self._mg_clear,  "#8172B2").pack(fill="x", pady=3)
        btn(btnbar, "💿  Export CSV",    self._mg_export, "#DD8452").pack(fill="x", pady=6)

        # Guide note at bottom
        tk.Label(right,
                 text="ℹ️  Select a row to load it.\nFill all fields, then Add or Save.",
                 bg=BG2, fg="#666688", font=("Helvetica",8), justify="left").pack(anchor="w", pady=(4,0))

    # ── Manage helpers ────────────────────────────────────────────────
    def _mg_refresh_tree(self):
        self.mg_tree.delete(*self.mg_tree.get_children())
        for _, r in df.iterrows():
            self.mg_tree.insert("", "end", values=(
                r["State/UT"],
                f"{int(r['Children_Missing_2023']):,}",
                f"{int(r['Children_Recovered_2023']):,}",
                f"{int(r['Women_Missing_2023']):,}",
                f"{int(r['Women_Recovered_2023']):,}",
            ))

    def _mg_select(self, _):
        sel = self.mg_tree.focus()
        if not sel: return
        state_name = self.mg_tree.item(sel)["values"][0]
        r = df[df["State/UT"] == state_name]
        if r.empty: return
        r = r.iloc[0]
        mapping = {
            "state": "State/UT", "cm23": "Children_Missing_2023",
            "cr23": "Children_Recovered_2023", "cu23": "Children_Unrecovered_End_2023",
            "cttl": "Children_Total_Missing", "wm23": "Women_Missing_2023",
            "wr23": "Women_Recovered_2023", "wu23": "Women_Unrecovered_End_2023",
            "wttl": "Women_Total_Missing",
        }
        for key, col in mapping.items():
            self._mg_vars[key].set(str(int(r[col])) if col != "State/UT" else r[col])
        self._mg_status.set(f"✅ Loaded: {state_name}")

    def _mg_get_form(self):
        """Returns (state_name, dict_of_numeric_fields) or raises ValueError."""
        state = self._mg_vars["state"].get().strip()
        if not state:
            raise ValueError("State / UT cannot be empty.")
        nums = {}
        num_keys = [
            ("cm23","Children_Missing_2023"), ("cr23","Children_Recovered_2023"),
            ("cu23","Children_Unrecovered_End_2023"), ("cttl","Children_Total_Missing"),
            ("wm23","Women_Missing_2023"), ("wr23","Women_Recovered_2023"),
            ("wu23","Women_Unrecovered_End_2023"), ("wttl","Women_Total_Missing"),
        ]
        for key, col in num_keys:
            val = self._mg_vars[key].get().strip()
            if not val:
                raise ValueError(f"Field '{col}' cannot be empty.")
            try: nums[col] = int(val)
            except ValueError: raise ValueError(f"'{col}' must be a whole number.")
        return state, nums

    def _mg_recompute_row(self, row_dict):
        """Recompute derived columns for a row dict."""
        cm = row_dict.get("Children_Total_Missing", 1) or 1
        wm = row_dict.get("Women_Total_Missing", 1) or 1
        row_dict["total"]  = row_dict["Children_Total_Missing"] + row_dict["Women_Total_Missing"]
        row_dict["c_rate"] = round(row_dict["Children_Recovered_2023"] / cm * 100, 1)
        row_dict["w_rate"] = round(row_dict["Women_Recovered_2023"]    / wm * 100, 1)
        return row_dict

    def _mg_sync(self):
        """Push df back into sqlite and refresh all views."""
        global df
        df.to_sql("mp", conn, if_exists="replace", index=False)
        self._mg_refresh_tree()
        self._fill()        # refresh search tab

    def _mg_add(self):
        global df
        try:
            state, nums = self._mg_get_form()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e)); return

        if state in df["State/UT"].values:
            messagebox.showerror("Duplicate", f"'{state}' already exists.\nUse 'Save Changes' to modify it."); return

        row = {"State/UT": state, **nums}
        row = self._mg_recompute_row(row)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        self._mg_sync()
        self._mg_status.set(f"✅ Added: {state}")

    def _mg_modify(self):
        global df
        try:
            state, nums = self._mg_get_form()
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e)); return

        if state not in df["State/UT"].values:
            if not messagebox.askyesno("Not Found", f"'{state}' not found. Add as new record?"):
                return
            self._mg_add(); return

        idx = df.index[df["State/UT"] == state][0]
        for col, val in nums.items():
            df.at[idx, col] = val
        row_dict = df.loc[idx].to_dict()
        row_dict = self._mg_recompute_row(row_dict)
        for col, val in row_dict.items():
            df.at[idx, col] = val
        self._mg_sync()
        self._mg_status.set(f"💾 Updated: {state}")

    def _mg_delete(self):
        global df
        state = self._mg_vars["state"].get().strip()
        if not state:
            messagebox.showerror("Error", "Select a row first."); return
        if state not in df["State/UT"].values:
            messagebox.showerror("Not Found", f"'{state}' not found in dataset."); return
        if not messagebox.askyesno("Confirm Delete", f"Permanently delete '{state}'?"):
            return
        df = df[df["State/UT"] != state].reset_index(drop=True)
        self._mg_sync()
        self._mg_clear()
        self._mg_status.set(f"🗑️ Deleted: {state}")

    def _mg_clear(self):
        for var in self._mg_vars.values():
            var.set("")
        self._mg_status.set("🧹 Form cleared.")

    def _mg_export(self):
        path = os.path.join(BASE, "Missing_person_updated.csv")
        export_cols = [f[2] for f in self._mg_fields]  # original CSV columns
        df[export_cols].to_csv(path, index=False)
        self._mg_status.set(f"💿 Exported to:\n{os.path.basename(path)}")
        messagebox.showinfo("Exported", f"Saved to:\n{path}")


App().mainloop()