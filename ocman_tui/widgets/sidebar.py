"""
Sidebar widget for projects and sessions navigation.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path

from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from rich.text import Text

from ..core import db_list_projects, db_list_sessions, db_search_sessions

# Readable subtext color for secondary labels (ids, dir tags, empty states).
# Uses the Catppuccin subtext tone already in the TUI palette rather than Rich
# "dim" (the ANSI faint attribute), which is low-contrast/near-invisible on some
# terminals. Accessibility: never de-emphasize via reduced contrast.
_SUBTEXT = "#a6adc8"

class SidebarWidget(Tree):
    """A tree view that lists projects, sessions, and nested subagent sessions."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Projects", **kwargs)
        self.root.expand()
        self.show_root = False

    def load_data(self, filter_query: Optional[str] = None) -> None:
        """Query projects and sessions from SQLite and build the tree hierarchy.

        B2-07: when ``filter_query`` is a non-empty string, restrict the tree to sessions that
        match the query (by content or title, case-insensitive) and to the projects that
        contain at least one such session. An empty/None query shows the full tree.
        """
        self.clear()

        query = (filter_query or "").strip()
        match_ids: Optional[set[str]] = None
        if query:
            try:
                hits = db_search_sessions(query)
                match_ids = {h["id"] for h in hits}
            except Exception:
                match_ids = set()
            if not match_ids:
                self.root.add_leaf(Text(f"No sessions match {query!r}", style=f"italic {_SUBTEXT}"))
                return

        try:
            projects = db_list_projects()
        except Exception:
            projects = []

        if not projects:
            self.root.add_leaf(Text("No projects found", style=f"italic {_SUBTEXT}"))
            return

        # Auto-detect CWD matching project
        cwd_str = str(Path.cwd().resolve())

        for proj in projects:
            proj_id = proj["id"]
            proj_name = proj["name"] or Path(proj["directory"]).name or "Unnamed"
            proj_dir = proj["directory"]

            # Fetch and sort sessions
            try:
                all_sessions = db_list_sessions(proj_id)
            except Exception:
                all_sessions = []

            # B2-07: when filtering, keep only matching sessions and skip projects with none.
            if match_ids is not None:
                all_sessions = [s for s in all_sessions if s["id"] in match_ids]
                if not all_sessions:
                    continue

            # Add directory hint
            label = Text(proj_name)
            if proj_dir == cwd_str:
                label.append(" (CWD)", style="bold #89b4fa")
            else:
                label.append(f" [{Path(proj_dir).name}]", style=_SUBTEXT)

            proj_node = self.root.add(label, data={"type": "project", "id": proj_id, "dir": proj_dir})

            if not all_sessions:
                proj_node.add_leaf(Text("No sessions", style=f"italic {_SUBTEXT}"))
                continue

            # When filtering, matching sessions are shown as a flat list (nesting is a
            # non-filtered nicety that does not survive a partial match cleanly).
            if match_ids is not None:
                for s in all_sessions:
                    title = s.get("title") or "(untitled)"
                    node_label = Text(title)
                    node_label.append(f" [{s['id'][:8]}]", style=_SUBTEXT)
                    proj_node.add_leaf(node_label, data={"type": "session", "id": s["id"], "data": s})
                continue

            # Build a mapping of session_id -> node for nesting
            session_map: Dict[str, TreeNode] = {}
            # We will also keep track of nested subagent sessions to process
            children_to_add: List[Dict[str, Any]] = []

            # Add root sessions first
            for s in all_sessions:
                parent_id = s.get("parent_id")
                if not parent_id:
                    # It's a root session
                    title = s.get("title") or "(untitled)"
                    node_label = Text(title)
                    node_label.append(f" [{s['id'][:8]}]", style=_SUBTEXT)
                    
                    session_node = proj_node.add(node_label, data={"type": "session", "id": s["id"], "data": s})
                    session_map[s["id"]] = session_node
                else:
                    children_to_add.append(s)

            # Re-process child sessions to nest them under their parent sessions
            # Sort children by created time so they are ordered properly
            children_to_add.sort(key=lambda x: x.get("created") or 0)
            
            # Loop multiple times to allow multi-level nesting of children
            for attempt in range(3): # Support up to 3 levels of nesting
                for s in children_to_add:
                    if s["id"] in session_map:
                        continue
                    parent_id = s.get("parent_id")
                    if parent_id in session_map:
                        parent_node = session_map[parent_id]
                        title = s.get("title") or "(untitled)"
                        node_label = Text("⤷ ")
                        node_label.append(title)
                        node_label.append(f" [{s['id'][:8]}]", style=_SUBTEXT)
                        
                        session_node = parent_node.add(node_label, data={"type": "session", "id": s["id"], "data": s})
                        session_map[s["id"]] = session_node
                    else:
                        if attempt == 2:
                            # If we still can't resolve it on the last attempt, add it to project node directly
                            title = s.get("title") or "(untitled)"
                            node_label = Text("⤷ (orphan) ")
                            node_label.append(title)
                            node_label.append(f" [{s['id'][:8]}]", style=_SUBTEXT)
                            
                            session_node = proj_node.add(node_label, data={"type": "session", "id": s["id"], "data": s})
                            session_map[s["id"]] = session_node
        
        # Expand the first project node if there are any
        for child in self.root.children:
            child.expand()
