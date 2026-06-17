"""
Sidebar widget for projects and sessions navigation.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path

from textual.widgets import Tree
from textual.widgets.tree import TreeNode
from rich.text import Text

from ..core import db_list_projects, db_list_sessions

class SidebarWidget(Tree):
    """A tree view that lists projects, sessions, and nested subagent sessions."""

    def __init__(self, **kwargs) -> None:
        super().__init__("Projects", **kwargs)
        self.root.expand()
        self.show_root = False

    def load_data(self) -> None:
        """Query projects and sessions from SQLite and build the tree hierarchy."""
        self.clear()
        
        try:
            projects = db_list_projects()
        except Exception:
            projects = []

        if not projects:
            self.root.add_leaf(Text("No projects found", style="dim italic"))
            return

        # Auto-detect CWD matching project
        cwd_str = str(Path.cwd().resolve())

        for proj in projects:
            proj_id = proj["id"]
            proj_name = proj["name"] or Path(proj["directory"]).name or "Unnamed"
            proj_dir = proj["directory"]

            # Add directory hint
            label = Text(proj_name)
            if proj_dir == cwd_str:
                label.append(" (CWD)", style="bold #89b4fa")
            else:
                label.append(f" [{Path(proj_dir).name}]", style="dim")

            proj_node = self.root.add(label, data={"type": "project", "id": proj_id, "dir": proj_dir})

            # Fetch and sort sessions
            try:
                all_sessions = db_list_sessions(proj_id)
            except Exception:
                all_sessions = []

            if not all_sessions:
                proj_node.add_leaf(Text("No sessions", style="dim italic"))
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
                    node_label.append(f" [{s['id'][:8]}]", style="dim")
                    
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
                        node_label.append(f" [{s['id'][:8]}]", style="dim")
                        
                        session_node = parent_node.add(node_label, data={"type": "session", "id": s["id"], "data": s})
                        session_map[s["id"]] = session_node
                    else:
                        if attempt == 2:
                            # If we still can't resolve it on the last attempt, add it to project node directly
                            title = s.get("title") or "(untitled)"
                            node_label = Text("⤷ (orphan) ")
                            node_label.append(title)
                            node_label.append(f" [{s['id'][:8]}]", style="dim")
                            
                            session_node = proj_node.add(node_label, data={"type": "session", "id": s["id"], "data": s})
                            session_map[s["id"]] = session_node
        
        # Expand the first project node if there are any
        for child in self.root.children:
            child.expand()
