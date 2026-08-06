"""Prompt-to-paper desktop GUI (Tkinter, stdlib only -- nothing extra to install).

One window with a "Generate a Paper..." button. Clicking it opens a form:
  1. A free-text prompt box.
  2. Choose the ALMA data source: type it in yourself, or let Claude match
     your prompt against an already-vetted candidate pool (topic_lookup.py /
     Stage 10), restricted to unpublished (default), published, or both,
     per your choice -- the scientific-category/keyword dropdowns update to
     match whichever publication status is selected.
  3. Choose an AI provider: Claude (default), or ChatGPT as a fallback for
     when Claude usage/tokens run out (not implemented yet -- see
     llm.call_chatgpt).
  4. Choose a Claude model (Fable 5 costs API credits; the rest are included
     with a Claude subscription). Only applies to the Claude provider.
  5. Choose scope: a fast single-pass Quick Summary, Idea + Methods only, or
     a Full paper (real ALMA download + analysis, only works for HCN(1-0)
     datasets, and only available on the Claude provider).
  6. Optionally also generate a Beginner-Friendly Plan -- a plain-language
     companion PDF (project goal, prerequisite skills, first-week
     walkthrough) aimed at an undergraduate or high-school reader, since the
     idea/methods/paper text above assumes an experienced thesis student.
Generation runs on a background thread so the window stays responsive; if
search mode picks an ALMA project code, it's shown back to you to confirm
(or cancel) before anything is downloaded or generated, since an LLM-guessed
project code is the one part of this flow that could plausibly be wrong.

Usage:
    python gui_app.py
"""
from __future__ import annotations

import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from topic_lookup import available_categories_and_keywords, default_source_repo, list_candidates
from wizard import MODELS, PROVIDERS, PUBLICATION_FILTERS, SCOPES, WizardConfig, _make_call_llm, generate, resolve

NGC4429_ALIASES = {"ngc4429", "ngc 4429"}

# --- Dark theme -------------------------------------------------------
BG = "#0c0c0c"
PANEL_BG = "#1a1a1a"
ENTRY_BG = "#161616"
FG = "#eaeaea"
MUTED = "#8a8a8a"
BORDER = "#2c2c2c"
ACCENT = "#5b9dff"
ACCENT_ACTIVE = "#7fb1ff"
ACCENT_FG = "#0c0c0c"
DANGER = "#ff6b6b"
FONT = "Segoe UI"


def _apply_dark_theme(root: tk.Tk) -> None:
    """Style the whole app (every Toplevel shares one ttk.Style, since it's
    process-wide) as a clean, near-black theme with a single accent color
    for primary actions. 'clam' is used as the base theme because Windows's
    native themes ('vista'/'winnative') ignore most color overrides."""
    style = ttk.Style(root)
    style.theme_use("clam")
    root.option_add("*Font", (FONT, 10))

    style.configure(".", background=BG, foreground=FG, fieldbackground=ENTRY_BG,
                     bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                     troughcolor=PANEL_BG, focuscolor=ACCENT, font=(FONT, 10))

    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED)
    style.configure("Danger.TLabel", background=BG, foreground=DANGER)
    style.configure("Header.TLabel", background=BG, foreground=FG, font=(FONT, 16, "bold"))
    style.configure("Bold.TLabel", background=BG, foreground=FG, font=(FONT, 10, "bold"))

    style.configure("TLabelframe", background=BG, bordercolor=BORDER, relief="solid", borderwidth=1)
    style.configure("TLabelframe.Label", background=BG, foreground=FG, font=(FONT, 10, "bold"))

    style.configure("TEntry", fieldbackground=ENTRY_BG, foreground=FG, insertcolor=FG,
                     bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, relief="flat", padding=6)
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure("TCombobox", fieldbackground=ENTRY_BG, background=PANEL_BG, foreground=FG,
                     arrowcolor=FG, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                     selectbackground=ENTRY_BG, selectforeground=FG, padding=6)
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", ENTRY_BG), ("disabled", "#141414")],
        foreground=[("disabled", MUTED)],
        background=[("active", "#242424"), ("readonly", ENTRY_BG)],
        arrowcolor=[("disabled", MUTED)],
    )
    # The dropdown popdown list is a plain Tk Listbox, not a ttk widget, so
    # ttk.Style can't reach it -- it has to go through the option database
    # instead, or it renders with Tk's default white background/black text.
    root.option_add("*TCombobox*Listbox.background", ENTRY_BG)
    root.option_add("*TCombobox*Listbox.foreground", FG)
    root.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", ACCENT_FG)

    style.configure("TButton", background=PANEL_BG, foreground=FG, bordercolor=BORDER,
                     lightcolor=PANEL_BG, darkcolor=PANEL_BG, relief="flat", padding=(12, 6))
    style.map(
        "TButton",
        background=[("disabled", "#141414"), ("active", "#242424")],
        foreground=[("disabled", MUTED)],
    )

    style.configure("Accent.TButton", background=ACCENT, foreground=ACCENT_FG, bordercolor=ACCENT,
                     relief="flat", padding=(16, 8), font=(FONT, 10, "bold"))
    style.map(
        "Accent.TButton",
        background=[("disabled", "#26364f"), ("active", ACCENT_ACTIVE)],
        foreground=[("disabled", "#6c6c6c")],
    )

    style.configure("TRadiobutton", background=BG, foreground=FG, focuscolor=BG,
                     indicatorbackground=ENTRY_BG, indicatorforeground=FG)
    style.map(
        "TRadiobutton",
        foreground=[("disabled", MUTED), ("active", FG)],
        # clam's default "active" (hover) state paints the whole label area
        # with the theme's own light/white highlight color, which we never
        # overrode -- that made the (already light-colored) label text
        # unreadable while hovering. Pin both background and foreground for
        # "active" explicitly so hovering an option never hides its text.
        background=[("active", BG)],
        # clam's radiobutton indicator element takes indicatorbackground/-foreground,
        # not indicatorcolor (that option doesn't exist on this Tk build's clam
        # theme -- confirmed via style.element_options -- so it was silently
        # ignored, leaving every dot the theme's own default white).
        indicatorbackground=[("selected", ACCENT), ("!selected", ENTRY_BG)],
    )

    style.configure("TCheckbutton", background=BG, foreground=FG, focuscolor=BG,
                     indicatorbackground=ENTRY_BG, indicatorforeground=FG)
    style.map(
        "TCheckbutton",
        foreground=[("disabled", MUTED), ("active", FG)],
        background=[("active", BG)],
        indicatorbackground=[("selected", ACCENT), ("!selected", ENTRY_BG)],
    )

    root.configure(bg=BG)


def _style_text(widget) -> None:
    """Apply the dark theme to a plain tk.Text / scrolledtext.ScrolledText
    widget -- these are classic tk widgets, not ttk, so they need direct
    color options rather than a ttk.Style rule."""
    widget.configure(
        background=ENTRY_BG, foreground=FG, insertbackground=FG,
        selectbackground=ACCENT, selectforeground=ACCENT_FG,
        relief="flat", borderwidth=0,
        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
        padx=8, pady=6,
    )


class ConfirmSourceDialog(tk.Toplevel):
    """Modal dialog shown after search-mode picks a candidate, before any
    download/generation starts. Fields are editable in case the match (or
    the manually-typed values) need a tweak."""

    def __init__(self, parent, resolved):
        super().__init__(parent)
        self.title("Confirm ALMA data source")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.result = None  # set to the (possibly edited) field dict, or stays None on Cancel

        pad = {"padx": 10, "pady": 5}
        ttk.Label(self, text=resolved.source_note, wraplength=480, style="Muted.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", **pad
        )

        self.vars = {
            "project_code": tk.StringVar(value=resolved.project_code),
            "pi": tk.StringVar(value=resolved.pi),
            "target": tk.StringVar(value=resolved.target),
        }
        for row_i, (key, label) in enumerate([("project_code", "ALMA project code"), ("pi", "PI"), ("target", "Target")], start=1):
            ttk.Label(self, text=label + ":").grid(row=row_i, column=0, sticky="e", **pad)
            ttk.Entry(self, textvariable=self.vars[key], width=40).grid(row=row_i, column=1, sticky="w", **pad)

        ttk.Label(self, text="Data description:").grid(row=4, column=0, sticky="ne", **pad)
        self.desc_box = scrolledtext.ScrolledText(self, width=60, height=10, wrap="word")
        _style_text(self.desc_box)
        self.desc_box.insert("1.0", resolved.data_description)
        self.desc_box.grid(row=4, column=1, sticky="w", **pad)
        ttk.Label(
            self,
            text="Check any spectral line frequencies/wavelengths above before continuing: are they "
                 "labeled rest-frame or observed-frame, and are approximate values marked as such? "
                 "Whatever this box says is what the generated idea/methods/paper will treat as given. "
                 "If you edit Target above, keep the ALMA archive's exact target_name spelling (e.g. "
                 "\"NGC4429\", not \"NGC 4429\") -- 'Full paper' scope's download will fail on a "
                 "human-friendly respelling even if it looks equivalent.",
            wraplength=480, style="Muted.TLabel",
        ).grid(row=5, column=0, columnspan=2, sticky="w", **pad)

        btns = ttk.Frame(self)
        btns.grid(row=6, column=0, columnspan=2, pady=14)
        ttk.Button(btns, text="Confirm & Continue", style="Accent.TButton", command=self._confirm).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=self._cancel).pack(side="left", padx=6)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.transient(parent)
        self.grab_set()

    def _confirm(self):
        self.result = {
            "project_code": self.vars["project_code"].get().strip(),
            "pi": self.vars["pi"].get().strip(),
            "target": self.vars["target"].get().strip(),
            "data_description": self.desc_box.get("1.0", "end").strip(),
        }
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class WizardForm(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Generate a Paper")
        self.geometry("700x780")
        self.minsize(560, 420)
        self.configure(bg=BG)

        self.mode_var = tk.StringVar(value="search")
        self.publication_filter_var = tk.StringVar(value=PUBLICATION_FILTERS[0][0])
        self.provider_var = tk.StringVar(value=PROVIDERS[0][0])
        self.model_var = tk.StringVar(value=MODELS[0][0])
        self.scope_var = tk.StringVar(value="idea_methods")
        self.project_dir_var = tk.StringVar(value="")
        self.project_code_var = tk.StringVar(value="")
        self.pi_var = tk.StringVar(value="")
        self.target_var = tk.StringVar(value="")
        self.distance_var = tk.StringVar(value="")
        self.velocity_var = tk.StringVar(value="")
        self.beginner_plan_var = tk.BooleanVar(value=False)

        # Each publication-status filter gets its own independent category/
        # keyword selection (and its own slice of the local candidate pool),
        # not one shared pair that gets reloaded on toggle -- see
        # _toggle_publication_filter's docstring for why.
        self._pub_pool: dict[str, tuple[list[str], dict[str, list[str]], str | None]] = {}
        self.category_vars: dict[str, tk.StringVar] = {}
        self.keyword_vars: dict[str, tk.StringVar] = {}
        for filter_key, _label, _note in PUBLICATION_FILTERS:
            categories, keywords_by_category, load_error = self._load_category_keyword_options(filter_key)
            self._pub_pool[filter_key] = (categories, keywords_by_category, load_error)
            first_keywords = keywords_by_category.get(categories[0], []) if categories else []
            self.category_vars[filter_key] = tk.StringVar(value=categories[0] if categories else "")
            self.keyword_vars[filter_key] = tk.StringVar(value=first_keywords[0] if first_keywords else "")

        self._msg_queue: "queue.Queue[tuple]" = queue.Queue()
        self._confirm_event = threading.Event()
        self._confirm_result = None
        self._worker: threading.Thread | None = None

        self._build_form()
        self.after(150, self._poll_queue)

    # --- category/keyword options ---------------------------------------

    @staticmethod
    def _load_category_keyword_options(publication_filter: str):
        """Scientific category / science keyword dropdown options, derived
        from whatever's already ingested in the local candidate pool under
        the chosen publication-status filter (free -- local file reads only,
        no Claude call) rather than the full official ALMA vocabulary, so
        every combination offered is guaranteed to match at least one real
        candidate under that filter. Failure (e.g. the sibling checkout isn't
        present) is caught here and surfaced as a message in the form itself,
        not a crash at import/construction time."""
        try:
            candidates = list_candidates(default_source_repo(), publication_filter)
            categories, keywords_by_category = available_categories_and_keywords(candidates)
            if not categories:
                return [], {}, (
                    f"No scientific categories found in the local candidate pool for publication "
                    f"status {publication_filter!r} -- try a different publication-status filter, or "
                    "use manual mode instead."
                )
            return categories, keywords_by_category, None
        except Exception as exc:  # noqa: BLE001 -- surfaced in the form, not swallowed
            return [], {}, f"Couldn't load scientific categories/keywords ({exc}) -- use manual mode instead."

    def _on_category_selected(self, filter_key, event=None):
        # Auto-select the first keyword for the new category rather than
        # clearing it -- confirmed live that clearing it back to blank on
        # every category change reproduces the exact "the keyword dropdown
        # looks broken" symptom this whole default-selection fix exists for.
        _categories, keywords_by_category, _load_error = self._pub_pool[filter_key]
        keywords = keywords_by_category.get(self.category_vars[filter_key].get(), [])
        self._keyword_combos[filter_key].configure(values=keywords)
        self.keyword_vars[filter_key].set(keywords[0] if keywords else "")

    def _toggle_publication_filter(self):
        """Show only the currently selected publication-status filter's
        category/keyword dropdown pair.

        Each filter keeps its own pair (built once at construction from that
        filter's own slice of the local candidate pool) rather than one
        shared pair reloaded on toggle -- confirmed live that a shared pair
        can *look* unaffected by the filter choice when the newly selected
        pool's alphabetically-first category/keyword happen to coincide with
        the previous filter's (the local pool has only ~3 published-verdict
        entries total against 14 unpublished, so that collision was common)
        even though the underlying options genuinely differ. Separate,
        persistent per-filter selections make the difference visible and let
        switching back and forth restore whatever was previously picked for
        that filter instead of resetting it every time."""
        selected = self.publication_filter_var.get()
        for filter_key, frame in self._pub_frames.items():
            if filter_key == selected:
                frame.pack(fill="x", pady=(6, 0))
            else:
                frame.pack_forget()

    # --- form layout --------------------------------------------------

    def _build_form(self):
        # The full form (prompt box, source/model/scope sections, log) needs
        # more vertical space than most screens can show at once, so it's
        # built inside a scrollable canvas rather than a fixed-height frame
        # -- the window stays a reasonable default size, and every control
        # (including Generate and the log) stays reachable by scrolling.
        canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        outer = ttk.Frame(canvas, padding=16)
        window_id = canvas.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window_id, width=e.width))

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        ttk.Label(outer, text="What do you want a paper about?", style="Bold.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Optional. In search mode, matching is now primarily driven by the Scientific "
                 "category + Science keyword you pick below; this prompt is extra context used to "
                 "break ties if more than one candidate fits that category/keyword. In manual mode "
                 "it's just extra context too.",
            wraplength=620, style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 6))
        self.prompt_box = scrolledtext.ScrolledText(outer, width=70, height=4, wrap="word")
        _style_text(self.prompt_box)
        self.prompt_box.pack(fill="x", pady=(0, 14))

        # --- data source mode ---
        src_frame = ttk.LabelFrame(outer, text="ALMA data source", padding=12)
        src_frame.pack(fill="x", pady=(0, 12))
        ttk.Radiobutton(
            src_frame, text="I'll specify it myself (project code / PI / target / description)",
            variable=self.mode_var, value="manual", command=self._toggle_mode,
        ).pack(anchor="w", pady=2)
        ttk.Radiobutton(
            src_frame, text="Let Claude find one for me, matched to my prompt above",
            variable=self.mode_var, value="search", command=self._toggle_mode,
        ).pack(anchor="w", pady=2)
        ttk.Label(
            src_frame,
            text="Search mode matches against an already-vetted local pool of ALMA datasets -- not a "
                 "live search of the whole archive/web. You'll be shown the match to confirm before "
                 "anything downloads.",
            wraplength=600, style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        self.search_frame = ttk.Frame(src_frame)

        pub_frame = ttk.Frame(self.search_frame)
        pub_frame.pack(fill="x", pady=(6, 8))
        ttk.Label(pub_frame, text="Publication status to match against:", style="Bold.TLabel").pack(anchor="w")
        for filter_key, label, note in PUBLICATION_FILTERS:
            ttk.Radiobutton(
                pub_frame, text=label, variable=self.publication_filter_var, value=filter_key,
                command=self._toggle_publication_filter,
            ).pack(anchor="w", pady=(4, 0))
            ttk.Label(pub_frame, text=note, style="Muted.TLabel", wraplength=600).pack(anchor="w", padx=22)

        # One category/keyword dropdown pair per publication-status filter --
        # see _toggle_publication_filter's docstring for why they're kept
        # separate rather than sharing one pair that gets reloaded.
        self._pub_frames: dict[str, ttk.Frame] = {}
        self._category_combos: dict[str, ttk.Combobox] = {}
        self._keyword_combos: dict[str, ttk.Combobox] = {}
        for filter_key, _label, _note in PUBLICATION_FILTERS:
            categories, keywords_by_category, load_error = self._pub_pool[filter_key]
            frame = ttk.Frame(self.search_frame)
            self._pub_frames[filter_key] = frame

            row = ttk.Frame(frame)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text="Scientific category:", width=32, anchor="w").pack(side="left")
            category_combo = ttk.Combobox(
                row, textvariable=self.category_vars[filter_key], values=categories, state="readonly",
            )
            category_combo.pack(side="left", fill="x", expand=True)
            category_combo.bind("<<ComboboxSelected>>", lambda event, fk=filter_key: self._on_category_selected(fk, event))
            self._category_combos[filter_key] = category_combo

            row = ttk.Frame(frame)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text="Science keyword:", width=32, anchor="w").pack(side="left")
            first_keywords = keywords_by_category.get(categories[0], []) if categories else []
            keyword_combo = ttk.Combobox(
                row, textvariable=self.keyword_vars[filter_key], values=first_keywords, state="readonly",
            )
            keyword_combo.pack(side="left", fill="x", expand=True)
            self._keyword_combos[filter_key] = keyword_combo

            if load_error:
                ttk.Label(frame, text=load_error, style="Danger.TLabel", wraplength=600).pack(anchor="w", pady=(4, 0))
            else:
                ttk.Label(
                    frame,
                    text="Both are required for search mode. Pick a category first to narrow the "
                         "keyword list to keywords that actually occur with it in the local pool.",
                    style="Muted.TLabel", wraplength=600,
                ).pack(anchor="w", pady=(4, 0))

        self._toggle_publication_filter()  # show only the default filter's dropdown pair

        self.manual_frame = ttk.Frame(src_frame)
        for label, var in [
            ("ALMA project code (e.g. 2023.1.01214.S):", self.project_code_var),
            ("PI name:", self.pi_var),
            ("Target name:", self.target_var),
        ]:
            row = ttk.Frame(self.manual_frame)
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=label, width=32, anchor="w").pack(side="left")
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
        ttk.Label(
            self.manual_frame,
            text="Target name must match the ALMA archive's own target_name field exactly (e.g. "
                 "\"NGC4429\", not \"NGC 4429\") -- 'Full paper' scope downloads real data by querying "
                 "the archive with this exact string, and a human-friendly spelling that doesn't match "
                 "will fail with \"No public member OUS found\" even though the project code and PI are "
                 "correct. If you're not sure of the exact spelling, use search mode instead, which "
                 "pulls target names straight from the archive's own records.",
            wraplength=600, style="Muted.TLabel",
        ).pack(anchor="w", pady=(2, 6))
        ttk.Label(self.manual_frame, text="Data description (what you know about this dataset):").pack(
            anchor="w", pady=(6, 4)
        )
        ttk.Label(
            self.manual_frame,
            text="If you list spectral line frequencies/wavelengths, say whether each is rest-frame or "
                 "observed-frame (redshifted/Doppler-shifted), and flag approximate ones as such (e.g. "
                 "\"~218.5 GHz, observed frame, approximate\") -- everything typed here is treated as "
                 "given fact by the generated idea, methods, and paper text, caveats included.",
            wraplength=600, style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 4))
        self.data_desc_box = scrolledtext.ScrolledText(self.manual_frame, width=60, height=6, wrap="word")
        _style_text(self.data_desc_box)
        self.data_desc_box.pack(fill="x")

        # --- provider choice ---
        provider_frame = ttk.LabelFrame(outer, text="AI provider", padding=12)
        provider_frame.pack(fill="x", pady=(0, 12))
        for provider_key, label, note in PROVIDERS:
            ttk.Radiobutton(provider_frame, text=label, variable=self.provider_var, value=provider_key,
                             command=self._toggle_provider).pack(anchor="w", pady=(2, 0))
            ttk.Label(provider_frame, text=note, style="Muted.TLabel", wraplength=600).pack(anchor="w", padx=22)

        # --- model choice ---
        self.model_frame = ttk.LabelFrame(outer, text="Claude model", padding=12)
        self.model_frame.pack(fill="x", pady=(0, 12))
        for model_id, label, note in MODELS:
            ttk.Radiobutton(self.model_frame, text=label, variable=self.model_var, value=model_id).pack(
                anchor="w", pady=(4, 0)
            )
            ttk.Label(self.model_frame, text=note, style="Muted.TLabel", wraplength=600).pack(anchor="w", padx=22)

        # --- scope choice ---
        scope_frame = ttk.LabelFrame(outer, text="What to generate", padding=12)
        scope_frame.pack(fill="x", pady=(0, 12))
        self.scope_radios: dict[str, ttk.Radiobutton] = {}
        for scope_key, label, note in SCOPES:
            radio = ttk.Radiobutton(scope_frame, text=label, variable=self.scope_var, value=scope_key,
                                     command=self._toggle_scope)
            radio.pack(anchor="w", pady=(2, 0))
            self.scope_radios[scope_key] = radio
            ttk.Label(scope_frame, text=note, style="Muted.TLabel", wraplength=600).pack(anchor="w", padx=22)

        ttk.Checkbutton(
            scope_frame, text="Also generate a Beginner-Friendly Plan", variable=self.beginner_plan_var,
        ).pack(anchor="w", pady=(10, 0))
        ttk.Label(
            scope_frame,
            text="A plain-language companion PDF for a reader new to research -- an undergraduate or "
                 "even a high-school student. Explains the project's goal and what you should have "
                 "accomplished by the end, the basic skills you'll need (e.g. Python, basic "
                 "astrophysics concepts), and what a typical first week of the project would look "
                 "like. Adds one extra PDF alongside whatever scope you picked above.",
            style="Muted.TLabel", wraplength=600,
        ).pack(anchor="w", padx=22, pady=(0, 4))

        self.full_paper_frame = ttk.Frame(scope_frame)
        row = ttk.Frame(self.full_paper_frame)
        row.pack(fill="x", pady=3)
        ttk.Label(row, text="Distance (Mpc, optional):", width=32, anchor="w").pack(side="left")
        ttk.Entry(row, textvariable=self.distance_var, width=12).pack(side="left")
        row2 = ttk.Frame(self.full_paper_frame)
        row2.pack(fill="x", pady=3)
        ttk.Label(row2, text="Systemic velocity (km/s, optional):", width=32, anchor="w").pack(side="left")
        ttk.Entry(row2, textvariable=self.velocity_var, width=12).pack(side="left")
        ttk.Label(
            self.full_paper_frame,
            text="Leave both blank and Claude will look them up (shown in the log below before use).",
            style="Muted.TLabel", wraplength=600,
        ).pack(anchor="w", pady=(2, 0))

        # --- project dir + generate ---
        row = ttk.Frame(outer)
        row.pack(fill="x", pady=(0, 12))
        ttk.Label(row, text="Project folder (optional):", width=32, anchor="w").pack(side="left")
        ttk.Entry(row, textvariable=self.project_dir_var).pack(side="left", fill="x", expand=True)

        self.generate_btn = ttk.Button(outer, text="Generate", style="Accent.TButton", command=self._on_generate)
        self.generate_btn.pack(pady=(2, 12))

        ttk.Label(outer, text="Progress", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        self.log_box = scrolledtext.ScrolledText(outer, width=70, height=10, wrap="word", state="disabled")
        _style_text(self.log_box)
        self.log_box.pack(fill="both", expand=True)

        self.results_frame = ttk.Frame(outer)
        self.results_frame.pack(fill="x", pady=(10, 0))

        self._toggle_mode()
        self._toggle_provider()
        self._toggle_scope()

    def _toggle_mode(self):
        if self.mode_var.get() == "manual":
            self.manual_frame.pack(fill="x", pady=(6, 0))
            self.search_frame.pack_forget()
        else:
            self.manual_frame.pack_forget()
            self.search_frame.pack(fill="x", pady=(6, 0))

    def _toggle_provider(self):
        # ChatGPT isn't implemented yet (llm.call_chatgpt raises) and, even once it
        # is, only ever covers idea+methods-shaped work -- 'Full paper' needs Claude
        # for the real-data analysis writeup. Model choice is Claude-only too, so
        # both are disabled rather than just left clickable-but-wrong.
        is_chatgpt = self.provider_var.get() == "chatgpt"
        model_state = "disabled" if is_chatgpt else "normal"
        for child in self.model_frame.winfo_children():
            if isinstance(child, ttk.Radiobutton):
                child.configure(state=model_state)

        full_paper_radio = self.scope_radios.get("full_paper")
        if full_paper_radio is not None:
            full_paper_radio.configure(state="disabled" if is_chatgpt else "normal")
        if is_chatgpt and self.scope_var.get() == "full_paper":
            self.scope_var.set("quick_summary")
        self._toggle_scope()

    def _toggle_scope(self):
        if self.scope_var.get() == "full_paper":
            self.full_paper_frame.pack(fill="x", pady=(4, 0))
        else:
            self.full_paper_frame.pack_forget()

    # --- logging helpers ------------------------------------------------

    def _log(self, text: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_running(self, running: bool):
        state = "disabled" if running else "normal"
        self.generate_btn.configure(state=state)

    # --- generate flow ---------------------------------------------------

    def _on_generate(self):
        try:
            cfg = self._collect_config()
        except ValueError as exc:
            messagebox.showerror("Missing information", str(exc))
            return

        for child in self.results_frame.winfo_children():
            child.destroy()
        self._set_running(True)
        self._log("Starting...")

        self._worker = threading.Thread(target=self._run_worker, args=(cfg,), daemon=True)
        self._worker.start()

    def _collect_config(self) -> WizardConfig:
        prompt_text = self.prompt_box.get("1.0", "end").strip()
        mode = self.mode_var.get()
        scope = self.scope_var.get()
        provider = self.provider_var.get()

        if provider == "chatgpt" and scope == "full_paper":
            raise ValueError(
                "The ChatGPT provider doesn't support 'Full paper' scope -- switch the provider "
                "back to Claude, or pick 'Quick Summary' / 'Idea + Methods' instead."
            )

        publication_filter = self.publication_filter_var.get()
        category = self.category_vars[publication_filter].get().strip()
        keyword = self.keyword_vars[publication_filter].get().strip()
        if mode == "search" and not (category and keyword):
            raise ValueError("Pick both a Scientific category and a Science keyword -- both are required for search mode.")

        distance_mpc = None
        systemic_velocity_kms = None
        if scope == "full_paper":
            d, v = self.distance_var.get().strip(), self.velocity_var.get().strip()
            if d or v:
                if not (d and v):
                    raise ValueError("Give both distance and systemic velocity, or leave both blank to look them up.")
                try:
                    distance_mpc, systemic_velocity_kms = float(d), float(v)
                except ValueError:
                    raise ValueError("Distance and systemic velocity must be plain numbers.")
            elif mode == "manual" and self.target_var.get().strip().lower().replace("  ", " ") in NGC4429_ALIASES:
                distance_mpc, systemic_velocity_kms = 16.5, 1104.0

        return WizardConfig(
            mode=mode,
            scope=scope,
            model=self.model_var.get(),
            provider=provider,
            prompt_text=prompt_text,
            category=category,
            keyword=keyword,
            publication_filter=publication_filter,
            project_code=self.project_code_var.get().strip(),
            pi=self.pi_var.get().strip(),
            target=self.target_var.get().strip(),
            data_description=self.data_desc_box.get("1.0", "end").strip(),
            distance_mpc=distance_mpc,
            systemic_velocity_kms=systemic_velocity_kms,
            project_dir=self.project_dir_var.get().strip(),
            beginner_plan=self.beginner_plan_var.get(),
        )

    def _run_worker(self, cfg: WizardConfig):
        cc = _make_call_llm(cfg.provider, cfg.model or None, lambda msg: self._msg_queue.put(("LOG", msg)))
        try:
            self._msg_queue.put(("LOG", "Resolving ALMA data source..."))
            resolved = resolve(cfg, call_claude_fn=cc)

            if cfg.mode == "search":
                self._confirm_event.clear()
                self._msg_queue.put(("CONFIRM", resolved))
                self._confirm_event.wait()
                if self._confirm_result is None:
                    self._msg_queue.put(("LOG", "Cancelled -- nothing downloaded or generated."))
                    self._msg_queue.put(("IDLE", None))
                    return
                resolved.project_code = self._confirm_result["project_code"]
                resolved.pi = self._confirm_result["pi"]
                resolved.target = self._confirm_result["target"]
                resolved.data_description = self._confirm_result["data_description"]

            result = generate(cfg, resolved, progress=lambda msg: self._msg_queue.put(("LOG", msg)))
            self._msg_queue.put(("DONE", result))
        except Exception as exc:  # noqa: BLE001 -- surfaced to the user, not swallowed
            self._msg_queue.put(("ERROR", str(exc)))

    def _poll_queue(self):
        try:
            while True:
                kind, payload = self._msg_queue.get_nowait()
                if kind == "LOG":
                    self._log(payload)
                elif kind == "CONFIRM":
                    dialog = ConfirmSourceDialog(self, payload)
                    self.wait_window(dialog)
                    self._confirm_result = dialog.result
                    self._confirm_event.set()
                elif kind == "IDLE":
                    self._set_running(False)
                elif kind == "DONE":
                    self._set_running(False)
                    self._show_results(payload)
                elif kind == "ERROR":
                    self._set_running(False)
                    self._log(f"ERROR: {payload}")
                    messagebox.showerror("Generation failed", payload)
        except queue.Empty:
            pass
        self.after(150, self._poll_queue)

    def _show_results(self, result):
        if result.status == "short_circuited":
            self._log(f"Stopped: publication verdict was {result.literature_verdict}.")
            ttk.Label(
                self.results_frame,
                text=f"No PDFs generated -- publication verdict: {result.literature_verdict}.",
                style="Danger.TLabel",
            ).pack(anchor="w")
            self._add_start_over_button()
            return

        self._log(f"Done. {len(result.pdfs)} PDF(s) in {result.project_dir}")
        ttk.Label(self.results_frame, text="Generated", style="Bold.TLabel").pack(anchor="w", pady=(0, 4))
        for pdf_path in result.pdfs:
            row = ttk.Frame(self.results_frame)
            row.pack(fill="x", anchor="w", pady=2)
            ttk.Label(row, text=Path(pdf_path).name, width=32, anchor="w").pack(side="left")
            ttk.Button(row, text="Open", command=lambda p=pdf_path: _open_path(p)).pack(side="left", padx=6)
        btn_row = ttk.Frame(self.results_frame)
        btn_row.pack(anchor="w", pady=(8, 0))
        ttk.Button(
            btn_row, text="Open project folder", command=lambda: _open_path(result.project_dir)
        ).pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="Start Over", command=self._start_over).pack(side="left")

    def _add_start_over_button(self):
        ttk.Button(self.results_frame, text="Start Over", command=self._start_over).pack(anchor="w", pady=(8, 0))

    def _start_over(self):
        """Reset the form to a blank state without closing the window --
        lets the user immediately try a different prompt/data source/model
        if the generated idea wasn't what they wanted, rather than having to
        close and reopen the whole wizard."""
        self.prompt_box.delete("1.0", "end")
        self.data_desc_box.delete("1.0", "end")
        self.project_code_var.set("")
        self.pi_var.set("")
        self.target_var.set("")
        for filter_key, (categories, keywords_by_category, _load_error) in self._pub_pool.items():
            first_keywords = keywords_by_category.get(categories[0], []) if categories else []
            self.category_vars[filter_key].set(categories[0] if categories else "")
            self.keyword_vars[filter_key].set(first_keywords[0] if first_keywords else "")
            self._keyword_combos[filter_key].configure(values=first_keywords)
        self.publication_filter_var.set(PUBLICATION_FILTERS[0][0])
        self._toggle_publication_filter()
        self.project_dir_var.set("")
        self.distance_var.set("")
        self.velocity_var.set("")
        self.beginner_plan_var.set(False)
        self.mode_var.set("search")
        self.provider_var.set(PROVIDERS[0][0])
        self.scope_var.set("idea_methods")
        self._toggle_mode()
        self._toggle_provider()
        self._toggle_scope()
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
        for child in self.results_frame.winfo_children():
            child.destroy()
        self._set_running(False)


def _open_path(path: str):
    if sys.platform == "win32":
        os.startfile(path)  # noqa: S606 -- user-initiated, opening our own generated output
    else:
        os.system(f'xdg-open "{path}"')


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ALMA Thesis Planner")
        self.geometry("440x260")
        _apply_dark_theme(self)

        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="ALMA Thesis Planner", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Label(
            frame,
            text="Turn a research prompt into an idea, methods plan, and "
                 "(optionally) a real-data paper -- as PDFs.",
            wraplength=360, justify="center", style="Muted.TLabel",
        ).pack(pady=(0, 20))
        ttk.Button(frame, text="Generate a Paper...", style="Accent.TButton", command=self._open_form).pack()

    def _open_form(self):
        WizardForm(self)


if __name__ == "__main__":
    MainWindow().mainloop()
