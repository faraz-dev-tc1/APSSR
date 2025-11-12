"""
Hierarchical rule tree structure with dynamic addressing
"""
from typing import Dict, List, Optional
import uuid as uuid_lib

from src.models.document import Rule, Amendment
from src.utils.logger import get_logger


logger = get_logger("rule_tree")


class RuleNode:
    """Node in the rule tree"""

    def __init__(
        self,
        uuid: str,
        display_number: str,
        content: str,
        level: int = 0,
        parent_uuid: Optional[str] = None
    ):
        """Initialize rule node"""
        self.uuid = uuid
        self.display_number = display_number
        self.content = content
        self.level = level
        self.parent_uuid = parent_uuid
        self.children: List[RuleNode] = []
        self.amendment_history: List[Amendment] = []

    def add_child(self, child: 'RuleNode'):
        """Add child node"""
        child.parent_uuid = self.uuid
        self.children.append(child)

    def remove_child(self, child_uuid: str) -> bool:
        """Remove child node by UUID"""
        for i, child in enumerate(self.children):
            if child.uuid == child_uuid:
                del self.children[i]
                return True
        return False

    def find_child(self, display_number: str) -> Optional['RuleNode']:
        """Find child by display number"""
        for child in self.children:
            if child.display_number == display_number:
                return child
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'uuid': self.uuid,
            'display_number': self.display_number,
            'content': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'level': self.level,
            'children_count': len(self.children),
            'amendment_history': [
                {
                    'go_id': a.go_id,
                    'action': a.action.value,
                    'date': a.date.isoformat() if a.date else None
                }
                for a in self.amendment_history
            ]
        }


class RuleTree:
    """Hierarchical tree structure for rules with dynamic addressing"""

    def __init__(self):
        """Initialize rule tree"""
        self.root = RuleNode(
            uuid=str(uuid_lib.uuid4()),
            display_number="ROOT",
            content="",
            level=-1
        )
        self.uuid_map: Dict[str, RuleNode] = {self.root.uuid: self.root}
        self.display_map: Dict[str, str] = {}  # display_number -> uuid

    def add_rule(self, rule: Rule, parent_uuid: Optional[str] = None) -> RuleNode:
        """
        Add rule to tree

        Args:
            rule: Rule to add
            parent_uuid: Parent node UUID (None for root-level rules)

        Returns:
            Created RuleNode
        """
        # Create node
        node = RuleNode(
            uuid=rule.uuid,
            display_number=rule.display_number,
            content=rule.content,
            level=rule.level,
            parent_uuid=parent_uuid
        )

        # Add to maps
        self.uuid_map[node.uuid] = node
        self.display_map[node.display_number] = node.uuid

        # Add to parent
        if parent_uuid:
            parent = self.uuid_map.get(parent_uuid)
            if parent:
                parent.add_child(node)
        else:
            self.root.add_child(node)

        logger.debug(f"Added rule {node.display_number} (UUID: {node.uuid})")
        return node

    def find_by_uuid(self, uuid: str) -> Optional[RuleNode]:
        """Find node by UUID"""
        return self.uuid_map.get(uuid)

    def find_by_display_number(self, display_number: str) -> Optional[RuleNode]:
        """Find node by display number"""
        uuid = self.display_map.get(display_number)
        if uuid:
            return self.uuid_map.get(uuid)
        return None

    def find_by_path(self, path: List[str]) -> Optional[RuleNode]:
        """
        Find node by hierarchical path

        Args:
            path: List like ["rule-22", "sub-rule-2", "clause-e"]

        Returns:
            RuleNode or None
        """
        if not path:
            return None

        # Start from root
        current = self.root

        for component in path:
            # Parse component (e.g., "rule-22" -> "22")
            parts = component.split('-', 1)
            if len(parts) < 2:
                return None

            component_type, component_num = parts[0], parts[1]

            # Find child with this display number
            found = False
            for child in current.children:
                # Match on display number
                if component_num in child.display_number:
                    current = child
                    found = True
                    break

            if not found:
                logger.warning(f"Could not find node for path component: {component}")
                return None

        return current

    def remove_node(self, uuid: str) -> bool:
        """Remove node and all descendants"""
        node = self.find_by_uuid(uuid)
        if not node:
            return False

        # Remove from parent
        if node.parent_uuid:
            parent = self.find_by_uuid(node.parent_uuid)
            if parent:
                parent.remove_child(uuid)

        # Remove from maps
        self._remove_from_maps(node)

        logger.debug(f"Removed node {node.display_number} (UUID: {uuid})")
        return True

    def _remove_from_maps(self, node: RuleNode):
        """Recursively remove node and children from maps"""
        # Remove node
        if node.uuid in self.uuid_map:
            del self.uuid_map[node.uuid]
        if node.display_number in self.display_map:
            del self.display_map[node.display_number]

        # Remove children
        for child in node.children:
            self._remove_from_maps(child)

    def insert_node(
        self,
        node: RuleNode,
        parent_uuid: str,
        position: str = "after",
        reference_display_number: Optional[str] = None
    ) -> bool:
        """
        Insert node at specific position

        Args:
            node: Node to insert
            parent_uuid: Parent node UUID
            position: "before", "after", or "replace"
            reference_display_number: Reference sibling for before/after

        Returns:
            Success boolean
        """
        parent = self.find_by_uuid(parent_uuid)
        if not parent:
            logger.error(f"Parent UUID not found: {parent_uuid}")
            return False

        # Add to maps
        self.uuid_map[node.uuid] = node
        self.display_map[node.display_number] = node.uuid

        # Set parent
        node.parent_uuid = parent_uuid

        if position == "replace":
            # Replace existing child
            if reference_display_number:
                for i, child in enumerate(parent.children):
                    if child.display_number == reference_display_number:
                        parent.children[i] = node
                        return True
            parent.add_child(node)

        elif position == "before":
            # Insert before reference
            if reference_display_number:
                for i, child in enumerate(parent.children):
                    if child.display_number == reference_display_number:
                        parent.children.insert(i, node)
                        return True
            parent.children.insert(0, node)

        elif position == "after":
            # Insert after reference
            if reference_display_number:
                for i, child in enumerate(parent.children):
                    if child.display_number == reference_display_number:
                        parent.children.insert(i + 1, node)
                        return True
            parent.add_child(node)

        else:
            # Default: append
            parent.add_child(node)

        logger.debug(f"Inserted node {node.display_number} at position {position}")
        return True

    def renumber_nodes(self, parent_uuid: str, start_index: int = 0):
        """
        Renumber child nodes following legal conventions

        Args:
            parent_uuid: Parent node UUID
            start_index: Index to start renumbering from
        """
        parent = self.find_by_uuid(parent_uuid)
        if not parent:
            return

        # Get children to renumber
        children = parent.children[start_index:]

        for i, child in enumerate(children, start=start_index):
            old_display = child.display_number

            # Determine new number based on level
            if child.level == 0:
                # Main rule level: 1, 2, 3, ...
                new_display = str(i + 1)
            # Could add more sophisticated renumbering logic here

            # Update display number
            if old_display != new_display:
                # Remove old mapping
                if old_display in self.display_map:
                    del self.display_map[old_display]

                # Update node
                child.display_number = new_display

                # Add new mapping
                self.display_map[new_display] = child.uuid

                logger.debug(f"Renumbered {old_display} -> {new_display}")

    def get_all_rules(self) -> List[RuleNode]:
        """Get all rule nodes (excluding root)"""
        all_nodes = []
        self._collect_nodes(self.root, all_nodes)
        return all_nodes

    def _collect_nodes(self, node: RuleNode, collection: List[RuleNode]):
        """Recursively collect all nodes"""
        for child in node.children:
            collection.append(child)
            self._collect_nodes(child, collection)

    def to_dict(self) -> Dict:
        """Convert tree to dictionary"""
        return {
            'total_rules': len(self.uuid_map) - 1,  # Exclude root
            'rules': [node.to_dict() for node in self.get_all_rules()]
        }
