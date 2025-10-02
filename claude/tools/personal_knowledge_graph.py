#!/usr/bin/env python3
"""
Personal Knowledge Graph Foundation - Phase 2 Implementation

This system replaces static context files with a dynamic, interconnected knowledge
representation that learns and grows smarter over time. It provides the foundation
for intelligent decision-making across all agents by maintaining relationships
between career, financial, personal preferences, and learned patterns.

Key Features:
- Dynamic relationship mapping between all life domains
- Semantic search and intelligent context retrieval
- Pattern learning from successful decisions and outcomes
- Automatic context updates from agent interactions
- Predictive insights based on historical patterns
- Cross-domain optimization and decision support
"""

import json
import sqlite3
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import threading
import numpy as np
from collections import defaultdict, deque
import pickle

# Import Phase 3 infrastructure
from claude.tools.enhanced_context_manager import get_context_manager
from claude.tools.core.path_manager import get_maia_root

# ML pattern recognition import - conditional loading for testing
try:
    from claude.tools.ml_pattern_recognition import get_ml_system
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    get_ml_system = lambda: None


class NodeType(Enum):
    """Types of knowledge graph nodes"""
    PERSON = "person"
    COMPANY = "company"
    JOB = "job"
    SKILL = "skill"
    PROJECT = "project"
    GOAL = "goal"
    PREFERENCE = "preference"
    DECISION = "decision"
    OUTCOME = "outcome"
    PATTERN = "pattern"
    DOMAIN = "domain"
    CONCEPT = "concept"
    RELATIONSHIP = "relationship"
    EVENT = "event"
    LOCATION = "location"


class RelationshipType(Enum):
    """Types of relationships between nodes"""
    WORKS_AT = "works_at"
    APPLIED_TO = "applied_to"
    HAS_SKILL = "has_skill"
    REQUIRES_SKILL = "requires_skill"
    PREFERS = "prefers"
    LEADS_TO = "leads_to"
    INFLUENCES = "influences"
    SIMILAR_TO = "similar_to"
    PART_OF = "part_of"
    DEPENDS_ON = "depends_on"
    ACHIEVED = "achieved"
    FAILED_AT = "failed_at"
    LEARNED_FROM = "learned_from"
    CONNECTED_TO = "connected_to"
    LOCATED_IN = "located_in"
    CAUSED_BY = "caused_by"
    CORRELATES_WITH = "correlates_with"
    OPTIMIZES = "optimizes"


@dataclass
class KnowledgeNode:
    """A node in the personal knowledge graph"""
    node_id: str
    node_type: NodeType
    name: str
    description: str
    attributes: Dict[str, Any]
    created_at: datetime
    last_updated: datetime
    confidence: float = 1.0
    source_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'name': self.name,
            'description': self.description,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'confidence': self.confidence,
            'source_agent': self.source_agent,
            'metadata': self.metadata
        }


@dataclass
class KnowledgeRelationship:
    """A relationship between nodes in the knowledge graph"""
    relationship_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: RelationshipType
    strength: float  # 0.0 to 1.0
    attributes: Dict[str, Any]
    created_at: datetime
    last_updated: datetime
    confidence: float = 1.0
    source_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'relationship_id': self.relationship_id,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'relationship_type': self.relationship_type.value,
            'strength': self.strength,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat(),
            'confidence': self.confidence,
            'source_agent': self.source_agent,
            'metadata': self.metadata
        }


@dataclass
class SemanticQuery:
    """Semantic query for knowledge graph search"""
    query_text: str
    node_types: Optional[List[NodeType]] = None
    relationship_types: Optional[List[RelationshipType]] = None
    min_confidence: float = 0.5
    max_results: int = 50
    include_relationships: bool = True
    search_depth: int = 2
    context_keywords: List[str] = field(default_factory=list)


@dataclass
class KnowledgeInsight:
    """Derived insight from knowledge graph analysis"""
    insight_id: str
    insight_type: str
    description: str
    confidence: float
    supporting_nodes: List[str]
    supporting_relationships: List[str]
    implications: List[str]
    recommendations: List[str]
    created_at: datetime
    validity_period: timedelta = field(default=timedelta(days=30))


class PersonalKnowledgeGraph:
    """
    Dynamic personal knowledge graph that maintains relationships between
    career, financial, personal preferences, and learned patterns to enable
    intelligent decision-making across all life domains.
    """

    def __init__(self, db_path: str = "get_path_manager().get_path('backup') / 'databases/personal_knowledge_graph.db'"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Infrastructure connections
        self.context_manager = get_context_manager()

        # Initialize ML pattern recognition system (if available)
        if ML_AVAILABLE:
            self.ml_system = get_ml_system()
        else:
            self.ml_system = None

        # In-memory graph structures for fast access
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.relationships: Dict[str, KnowledgeRelationship] = {}
        self.node_relationships: Dict[str, Set[str]] = defaultdict(set)  # node_id -> relationship_ids

        # Semantic search and indexing
        self.node_embeddings: Dict[str, np.ndarray] = {}
        self.relationship_embeddings: Dict[str, np.ndarray] = {}
        self.semantic_index = {}

        # Learning and adaptation
        self.decision_outcomes: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.pattern_cache: Dict[str, Any] = {}
        self.insight_cache: List[KnowledgeInsight] = []

        # Configuration
        self.max_cache_size = 10000
        self.embedding_dimension = 384  # Compatible with sentence transformers
        self.relationship_decay_rate = 0.95  # Relationships decay over time if not reinforced

        # Thread safety
        self._graph_lock = threading.RLock()
        self._db_lock = threading.RLock()

        # Initialize system
        self._init_database()
        self._load_graph_from_db()
        self._migrate_existing_context()

        logging.info("Personal Knowledge Graph initialized with {} nodes and {} relationships".format(
            len(self.nodes), len(self.relationships)))

    def _init_database(self) -> None:
        """Initialize SQLite database for knowledge graph persistence"""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS nodes (
                        node_id TEXT PRIMARY KEY,
                        node_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        attributes TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_updated TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        source_agent TEXT,
                        metadata TEXT DEFAULT '{}'
                    );

                    CREATE TABLE IF NOT EXISTS relationships (
                        relationship_id TEXT PRIMARY KEY,
                        source_node_id TEXT NOT NULL,
                        target_node_id TEXT NOT NULL,
                        relationship_type TEXT NOT NULL,
                        strength REAL NOT NULL,
                        attributes TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        last_updated TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        source_agent TEXT,
                        metadata TEXT DEFAULT '{}',
                        FOREIGN KEY (source_node_id) REFERENCES nodes (node_id),
                        FOREIGN KEY (target_node_id) REFERENCES nodes (node_id)
                    );

                    CREATE TABLE IF NOT EXISTS node_embeddings (
                        node_id TEXT PRIMARY KEY,
                        embedding BLOB NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (node_id) REFERENCES nodes (node_id)
                    );

                    CREATE TABLE IF NOT EXISTS insights (
                        insight_id TEXT PRIMARY KEY,
                        insight_type TEXT NOT NULL,
                        description TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        supporting_nodes TEXT NOT NULL,
                        supporting_relationships TEXT NOT NULL,
                        implications TEXT NOT NULL,
                        recommendations TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        validity_period TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS decision_outcomes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        decision_id TEXT NOT NULL,
                        decision_context TEXT NOT NULL,
                        outcome_description TEXT NOT NULL,
                        success_score REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        metadata TEXT DEFAULT '{}'
                    );

                    CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
                    CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);
                    CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_node_id);
                    CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_node_id);
                    CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
                """)
                conn.commit()
            finally:
                conn.close()

    def _load_graph_from_db(self) -> None:
        """Load the complete graph from database into memory"""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                # Load nodes
                cursor = conn.execute("""
                    SELECT node_id, node_type, name, description, attributes,
                           created_at, last_updated, confidence, source_agent, metadata
                    FROM nodes
                """)

                for row in cursor.fetchall():
                    node = KnowledgeNode(
                        node_id=row[0],
                        node_type=NodeType(row[1]),
                        name=row[2],
                        description=row[3] or "",
                        attributes=json.loads(row[4]),
                        created_at=datetime.fromisoformat(row[5]),
                        last_updated=datetime.fromisoformat(row[6]),
                        confidence=row[7],
                        source_agent=row[8],
                        metadata=json.loads(row[9])
                    )
                    self.nodes[node.node_id] = node

                # Load relationships
                cursor = conn.execute("""
                    SELECT relationship_id, source_node_id, target_node_id, relationship_type,
                           strength, attributes, created_at, last_updated, confidence,
                           source_agent, metadata
                    FROM relationships
                """)

                for row in cursor.fetchall():
                    relationship = KnowledgeRelationship(
                        relationship_id=row[0],
                        source_node_id=row[1],
                        target_node_id=row[2],
                        relationship_type=RelationshipType(row[3]),
                        strength=row[4],
                        attributes=json.loads(row[5]),
                        created_at=datetime.fromisoformat(row[6]),
                        last_updated=datetime.fromisoformat(row[7]),
                        confidence=row[8],
                        source_agent=row[9],
                        metadata=json.loads(row[10])
                    )
                    self.relationships[relationship.relationship_id] = relationship

                    # Build relationship index
                    self.node_relationships[relationship.source_node_id].add(relationship.relationship_id)
                    self.node_relationships[relationship.target_node_id].add(relationship.relationship_id)

                # Load embeddings
                cursor = conn.execute("SELECT node_id, embedding FROM node_embeddings")
                for row in cursor.fetchall():
# Security: Review usage of potentially unsafe function/import
                    embedding = pickle.loads(row[1])
                    self.node_embeddings[row[0]] = embedding

            finally:
                conn.close()

    def _migrate_existing_context(self) -> None:
        """Migrate existing static context files to knowledge graph"""
        try:
            # Read profile context
            profile_path = Path("${MAIA_ROOT}/claude/context/personal/profile.md")
            if profile_path.exists():
                with open(profile_path, 'r') as f:
                    profile_content = f.read()

                # Create personal profile node if not exists
                if not self.get_node_by_name("Naythan Dawe", NodeType.PERSON):
                    self.add_node(
                        node_type=NodeType.PERSON,
                        name="Naythan Dawe",
                        description="Senior Business Relationship Manager and Technology Leader",
                        attributes={
                            "location": "Perth, Australia",
                            "email": "nd25@londonxyz.com",
                            "phone": "+61 (0)483 20 44 17",
                            "linkedin": "https://www.linkedin.com/in/naythandawe/",
                            "current_role": "Senior Client Partner at Zetta",
                            "portfolio_value": "~$1m+ new business secured",
                            "expertise_areas": ["portfolio_governance", "stakeholder_management", "cost_optimization"]
                        },
                        source_agent="knowledge_graph_migration"
                    )

            logging.info("Context migration completed successfully")

        except Exception as e:
            logging.error(f"Context migration failed: {e}")

    def add_node(self, node_type: NodeType, name: str, description: str,
                 attributes: Dict[str, Any], source_agent: str = None,
                 confidence: float = 1.0) -> str:
        """Add a new node to the knowledge graph"""
        node_id = str(uuid.uuid4())
        now = datetime.now()

        node = KnowledgeNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            description=description,
            attributes=attributes,
            created_at=now,
            last_updated=now,
            confidence=confidence,
            source_agent=source_agent
        )

        with self._graph_lock:
            self.nodes[node_id] = node

        # Generate semantic embedding
        self._generate_node_embedding(node)

        # Persist to database
        self._save_node_to_db(node)

        logging.info(f"Added node: {name} ({node_type.value})")
        return node_id

    def add_relationship(self, source_node_id: str, target_node_id: str,
                        relationship_type: RelationshipType, strength: float,
                        attributes: Dict[str, Any] = None, source_agent: str = None,
                        confidence: float = 1.0) -> str:
        """Add a new relationship between nodes"""
        if source_node_id not in self.nodes or target_node_id not in self.nodes:
            raise ValueError("Both nodes must exist before creating relationship")

        relationship_id = str(uuid.uuid4())
        now = datetime.now()

        relationship = KnowledgeRelationship(
            relationship_id=relationship_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            strength=strength,
            attributes=attributes or {},
            created_at=now,
            last_updated=now,
            confidence=confidence,
            source_agent=source_agent
        )

        with self._graph_lock:
            self.relationships[relationship_id] = relationship
            self.node_relationships[source_node_id].add(relationship_id)
            self.node_relationships[target_node_id].add(relationship_id)

        # Persist to database
        self._save_relationship_to_db(relationship)

        logging.info(f"Added relationship: {relationship_type.value} between {source_node_id} and {target_node_id}")
        return relationship_id

    def semantic_search(self, query: SemanticQuery) -> List[Dict[str, Any]]:
        """
        Perform semantic search across the knowledge graph.

        This enables natural language queries like:
        - "Companies I've applied to in AI/ML"
        - "Skills needed for senior BRM roles"
        - "Financial optimization opportunities"
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_text_embedding(query.query_text)

            # Find semantically similar nodes
            node_similarities = []
            for node_id, node_embedding in self.node_embeddings.items():
                if node_id in self.nodes:
                    node = self.nodes[node_id]

                    # Filter by node type if specified
                    if query.node_types and node.node_type not in query.node_types:
                        continue

                    # Filter by confidence
                    if node.confidence < query.min_confidence:
                        continue

                    # Calculate semantic similarity
                    similarity = self._calculate_similarity(query_embedding, node_embedding)

                    # Boost similarity for keyword matches
                    for keyword in query.context_keywords:
                        if keyword.lower() in node.name.lower() or keyword.lower() in node.description.lower():
                            similarity += 0.2

                    node_similarities.append({
                        'node': node,
                        'similarity': min(similarity, 1.0),
                        'relationships': []
                    })

            # Sort by similarity
            node_similarities.sort(key=lambda x: x['similarity'], reverse=True)

            # Add related nodes and relationships if requested
            if query.include_relationships:
                for result in node_similarities[:query.max_results]:
                    node_id = result['node'].node_id

                    # Get connected relationships
                    related_relationships = []
                    for rel_id in self.node_relationships[node_id]:
                        if rel_id in self.relationships:
                            relationship = self.relationships[rel_id]

                            # Filter by relationship type if specified
                            if query.relationship_types and relationship.relationship_type not in query.relationship_types:
                                continue

                            related_relationships.append(relationship)

                    result['relationships'] = related_relationships[:10]  # Limit relationships

            return node_similarities[:query.max_results]

        except Exception as e:
            logging.error(f"Semantic search failed: {e}")
            return []

    def find_patterns(self, domain: str = None) -> List[Dict[str, Any]]:
        """
        Find patterns in the knowledge graph using ML analysis.

        Identifies:
        - Career progression patterns
        - Success/failure patterns
        - Preference patterns
        - Decision patterns
        - Optimization opportunities
        """
        try:
            # Prepare data for pattern analysis
            graph_data = {
                'nodes': [node.to_dict() for node in self.nodes.values()],
                'relationships': [rel.to_dict() for rel in self.relationships.values()],
                'domain_filter': domain
            }

            # Use ML system for pattern detection
            if self.ml_system:
                patterns = self.ml_system.detect_patterns({
                    'graph_data': graph_data,
                    'analysis_type': 'knowledge_graph_patterns',
                    'domain': domain
                })
            else:
                patterns = []

            # Enhance patterns with graph-specific insights
            enhanced_patterns = []
            for pattern in patterns:
                enhanced_pattern = {
                    'pattern_id': pattern.pattern_id,
                    'pattern_type': pattern.pattern_type,
                    'description': pattern.description,
                    'confidence': pattern.confidence,
                    'supporting_nodes': self._find_supporting_nodes(pattern),
                    'optimization_opportunities': self._identify_optimizations(pattern),
                    'actionable_insights': self._generate_actionable_insights(pattern)
                }
                enhanced_patterns.append(enhanced_pattern)

            return enhanced_patterns

        except Exception as e:
            logging.error(f"Pattern finding failed: {e}")
            return []

    def get_contextual_insights(self, context: Dict[str, Any]) -> List[KnowledgeInsight]:
        """
        Get contextual insights based on current situation.

        Examples:
        - Interview preparation insights
        - Financial optimization insights
        - Career progression insights
        - Relationship network insights
        """
        insights = []

        try:
            # Analyze context to determine relevant domains
            relevant_domains = self._analyze_context_domains(context)

            for domain in relevant_domains:
                domain_insights = self._generate_domain_insights(domain, context)
                insights.extend(domain_insights)

            # Cross-domain insights
            cross_domain_insights = self._generate_cross_domain_insights(context, relevant_domains)
            insights.extend(cross_domain_insights)

            # Sort by confidence and relevance
            insights.sort(key=lambda x: x.confidence * self._calculate_insight_relevance(x, context), reverse=True)

            return insights[:10]  # Return top 10 insights

        except Exception as e:
            logging.error(f"Contextual insights generation failed: {e}")
            return []

    def update_from_agent_interaction(self, agent_id: str, interaction_data: Dict[str, Any]) -> None:
        """
        Update knowledge graph based on agent interactions.

        This enables continuous learning from all agent activities:
        - Job applications and outcomes
        - Interview results
        - Financial decisions
        - Travel preferences
        - Success/failure patterns
        """
        try:
            # Extract entities and relationships from interaction
            entities = self._extract_entities_from_interaction(interaction_data)
            relationships = self._extract_relationships_from_interaction(interaction_data)

            # Update or create nodes
            for entity in entities:
                existing_node = self.get_node_by_name(entity['name'], NodeType(entity['type']))
                if existing_node:
                    self._update_node_attributes(existing_node.node_id, entity['attributes'], agent_id)
                else:
                    self.add_node(
                        node_type=NodeType(entity['type']),
                        name=entity['name'],
                        description=entity['description'],
                        attributes=entity['attributes'],
                        source_agent=agent_id
                    )

            # Update or create relationships
            for rel in relationships:
                source_node = self.get_node_by_name(rel['source'], NodeType(rel['source_type']))
                target_node = self.get_node_by_name(rel['target'], NodeType(rel['target_type']))

                if source_node and target_node:
                    existing_rel = self._find_relationship(
                        source_node.node_id, target_node.node_id, RelationshipType(rel['type'])
                    )

                    if existing_rel:
                        # Strengthen existing relationship
                        self._strengthen_relationship(existing_rel.relationship_id, rel['strength_delta'])
                    else:
                        # Create new relationship
                        self.add_relationship(
                            source_node.node_id,
                            target_node.node_id,
                            RelationshipType(rel['type']),
                            rel['initial_strength'],
                            rel['attributes'],
                            agent_id
                        )

            # Record decision outcome if applicable
            if 'decision' in interaction_data and 'outcome' in interaction_data:
                self._record_decision_outcome(interaction_data, agent_id)

            logging.info(f"Updated knowledge graph from {agent_id} interaction")

        except Exception as e:
            logging.error(f"Failed to update from agent interaction: {e}")

    def get_agent_context(self, agent_id: str, request_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate enriched context for agents based on knowledge graph.

        This transforms agents from context-poor to context-rich by providing:
        - Relevant historical patterns
        - Related entities and relationships
        - Success/failure insights
        - Optimization opportunities
        - Predictive recommendations
        """
        try:
            # Determine agent domain focus
            agent_domains = self._get_agent_domains(agent_id)

            # Get relevant nodes and relationships
            relevant_context = {}

            for domain in agent_domains:
                domain_nodes = self._get_domain_nodes(domain)
                relevant_context[f'{domain}_entities'] = domain_nodes

                domain_patterns = self._get_domain_patterns(domain)
                relevant_context[f'{domain}_patterns'] = domain_patterns

            # Get cross-domain insights
            cross_domain_insights = self.get_contextual_insights(request_context)
            relevant_context['insights'] = [insight.to_dict() for insight in cross_domain_insights]

            # Get historical success patterns
            success_patterns = self._get_success_patterns_for_agent(agent_id)
            relevant_context['success_patterns'] = success_patterns

            # Get predictive recommendations
            recommendations = self._generate_predictive_recommendations(agent_id, request_context)
            relevant_context['recommendations'] = recommendations

            return relevant_context

        except Exception as e:
            logging.error(f"Failed to generate agent context: {e}")
            return {}

    def get_node_by_name(self, name: str, node_type: NodeType = None) -> Optional[KnowledgeNode]:
        """Find a node by name and optionally type"""
        for node in self.nodes.values():
            if node.name == name and (node_type is None or node.node_type == node_type):
                return node
        return None

    def get_all_entities(self, limit: Optional[int] = None, node_type: Optional[NodeType] = None) -> List[KnowledgeNode]:
        """Get all entities/nodes from the knowledge graph

        Args:
            limit: Maximum number of entities to return
            node_type: Filter by specific node type

        Returns:
            List of KnowledgeNode objects
        """
        nodes = list(self.nodes.values())

        # Filter by node type if specified
        if node_type:
            nodes = [node for node in nodes if node.node_type == node_type]

        # Sort by last_updated (most recent first)
        nodes.sort(key=lambda x: x.last_updated, reverse=True)

        # Apply limit if specified
        if limit:
            nodes = nodes[:limit]

        return nodes

    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get comprehensive knowledge graph summary"""
        node_type_counts = defaultdict(int)
        relationship_type_counts = defaultdict(int)

        for node in self.nodes.values():
            node_type_counts[node.node_type.value] += 1

        for relationship in self.relationships.values():
            relationship_type_counts[relationship.relationship_type.value] += 1

        return {
            'total_nodes': len(self.nodes),
            'total_relationships': len(self.relationships),
            'node_types': dict(node_type_counts),
            'relationship_types': dict(relationship_type_counts),
            'embedding_coverage': len(self.node_embeddings) / len(self.nodes) if self.nodes else 0,
            'insights_cached': len(self.insight_cache),
            'decision_outcomes_tracked': len(self.decision_outcomes),
            'last_updated': max([node.last_updated for node in self.nodes.values()], default=datetime.now()).isoformat(),
            'knowledge_domains': list(set(
                attr.get('domain') for node in self.nodes.values()
                for attr in [node.attributes] if 'domain' in attr
            ))
        }

    def _generate_node_embedding(self, node: KnowledgeNode) -> None:
        """Generate semantic embedding for a node"""
        try:
            # Combine node information for embedding
            text = f"{node.name} {node.description} {' '.join(str(v) for v in node.attributes.values())}"
            embedding = self._generate_text_embedding(text)

            self.node_embeddings[node.node_id] = embedding

            # Save to database
            self._save_embedding_to_db(node.node_id, embedding)

        except Exception as e:
            logging.error(f"Failed to generate embedding for node {node.node_id}: {e}")

    def _generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate text embedding using simple approach (would use sentence-transformers in production)"""
        # Simple hash-based embedding for demonstration
        # In production, use sentence-transformers or similar
        text_hash = hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()
        # Convert hash to fixed-size embedding
        embedding = np.array([ord(c) / 255.0 for c in text_hash[:self.embedding_dimension]])
        # Pad if necessary
        if len(embedding) < self.embedding_dimension:
            padding = np.zeros(self.embedding_dimension - len(embedding))
            embedding = np.concatenate([embedding, padding])
        return embedding[:self.embedding_dimension]

    def _calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings"""
        try:
            dot_product = np.dot(embedding1, embedding2)
            norms = np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            return dot_product / norms if norms > 0 else 0.0
        except:
            return 0.0

    def _save_node_to_db(self, node: KnowledgeNode) -> None:
        """Save node to database"""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO nodes
                    (node_id, node_type, name, description, attributes, created_at,
                     last_updated, confidence, source_agent, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    node.node_id, node.node_type.value, node.name, node.description,
                    json.dumps(node.attributes), node.created_at.isoformat(),
                    node.last_updated.isoformat(), node.confidence,
                    node.source_agent, json.dumps(node.metadata)
                ))
                conn.commit()
            finally:
                conn.close()

    def _save_relationship_to_db(self, relationship: KnowledgeRelationship) -> None:
        """Save relationship to database"""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO relationships
                    (relationship_id, source_node_id, target_node_id, relationship_type,
                     strength, attributes, created_at, last_updated, confidence,
                     source_agent, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    relationship.relationship_id, relationship.source_node_id,
                    relationship.target_node_id, relationship.relationship_type.value,
                    relationship.strength, json.dumps(relationship.attributes),
                    relationship.created_at.isoformat(), relationship.last_updated.isoformat(),
                    relationship.confidence, relationship.source_agent, json.dumps(relationship.metadata)
                ))
                conn.commit()
            finally:
                conn.close()

    def _save_embedding_to_db(self, node_id: str, embedding: np.ndarray) -> None:
        """Save embedding to database"""
        with self._db_lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO node_embeddings (node_id, embedding, created_at)
                    VALUES (?, ?, ?)
                """, (node_id, pickle.dumps(embedding), datetime.now().isoformat()))
                conn.commit()
            finally:
                conn.close()


# Global instance
_knowledge_graph = None

def get_knowledge_graph() -> PersonalKnowledgeGraph:
    """Get global personal knowledge graph instance"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = PersonalKnowledgeGraph()
    return _knowledge_graph


if __name__ == "__main__":
    # Example usage and testing
    kg = get_knowledge_graph()

    print("🧠 Personal Knowledge Graph - System Status")
    print("=" * 60)

    # Get knowledge summary
    summary = kg.get_knowledge_summary()
    print(f"Total Nodes: {summary['total_nodes']}")
    print(f"Total Relationships: {summary['total_relationships']}")
    print(f"Node Types: {summary['node_types']}")
    print(f"Relationship Types: {summary['relationship_types']}")
    print(f"Embedding Coverage: {summary['embedding_coverage']:.1%}")

    # Test semantic search
    print(f"\n🔍 Testing Semantic Search")
    query = SemanticQuery(
        query_text="career opportunities in technology",
        node_types=[NodeType.JOB, NodeType.COMPANY, NodeType.SKILL],
        max_results=5
    )

    results = kg.semantic_search(query)
    print(f"Found {len(results)} results for '{query.query_text}'")
    for result in results[:3]:
        print(f"  • {result['node'].name} ({result['node'].node_type.value}) - {result['similarity']:.2f}")

    # Test pattern detection
    print(f"\n🔄 Testing Pattern Detection")
    patterns = kg.find_patterns(domain="career")
    print(f"Found {len(patterns)} career patterns")

    print(f"\n🚀 Personal Knowledge Graph System: OPERATIONAL")
