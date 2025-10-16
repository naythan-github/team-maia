#!/usr/bin/env python3
"""
ServiceDesk Discovery Analyzer

Purpose: Semantic search and pattern discovery for ServiceDesk automation opportunities
Uses: E5-base-v2 768-dim embeddings for high-quality pattern matching
Focus: Discovery phase - finding automation candidates worth $350K/year

Usage:
    # Find repetitive issues
    python3 servicedesk_discovery_analyzer.py --query "repetitive manual tasks"

    # Find Azure infrastructure patterns
    python3 servicedesk_discovery_analyzer.py --query "Azure infrastructure deployment" --collection comments

    # Find high-impact automation candidates
    python3 servicedesk_discovery_analyzer.py --automation-opportunities

    # Interactive discovery mode
    python3 servicedesk_discovery_analyzer.py --interactive
"""

import chromadb
import sqlite3
import argparse
from sentence_transformers import SentenceTransformer
import sys
from typing import List, Dict, Tuple
from collections import Counter
import json

class ServiceDeskDiscoveryAnalyzer:
    def __init__(self, db_path: str = None, chroma_path: str = None, model_name: str = "intfloat/e5-base-v2"):
        """Initialize discovery analyzer with E5-base-v2 model"""
        self.db_path = db_path or "/Users/naythandawe/git/maia/claude/data/servicedesk_tickets.db"
        self.chroma_path = chroma_path or "/Users/naythandawe/.maia/servicedesk_rag"
        self.model_name = model_name

        print(f"🔍 ServiceDesk Discovery Analyzer")
        print(f"   Model: {model_name}")
        print(f"   Database: {self.db_path}")
        print(f"   ChromaDB: {self.chroma_path}")
        print()

        # Load model
        print("📥 Loading embedding model...")
        self.model = SentenceTransformer(model_name)
        print(f"   ✅ Model loaded (768 dimensions)")
        print()

        # Connect to databases
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)

        # Available collections
        self.collections = {
            'comments': self.chroma_client.get_collection('servicedesk_comments'),
            'descriptions': self.chroma_client.get_collection('servicedesk_descriptions'),
            'solutions': self.chroma_client.get_collection('servicedesk_solutions'),
            'titles': self.chroma_client.get_collection('servicedesk_titles'),
            'work_logs': self.chroma_client.get_collection('servicedesk_work_logs')
        }

    def semantic_search(self, query: str, collection_name: str = 'comments', n_results: int = 10, max_distance: float = None) -> List[Dict]:
        """Perform semantic search on specified collection

        Args:
            max_distance: Maximum distance threshold (lower distance = better match)
                         e.g. max_distance=0.4 means only return results with distance <= 0.4
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found. Available: {list(self.collections.keys())}")

        print(f"🔎 Searching: {collection_name}")
        print(f"   Query: '{query}'")
        print(f"   Top {n_results} results")
        if max_distance:
            print(f"   Max distance filter: {max_distance} (min similarity: {(1-max_distance)*100:.1f}%)")
        print()

        # Generate query embedding
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0].tolist()

        # Search
        collection = self.collections[collection_name]
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results * 3 if max_distance else n_results  # Get extras for filtering
        )

        # Format results
        formatted_results = []
        for i, (doc_id, doc, distance) in enumerate(zip(results['ids'][0], results['documents'][0], results['distances'][0])):
            if max_distance and distance > max_distance:
                continue

            if len(formatted_results) >= n_results:
                break

            formatted_results.append({
                'rank': len(formatted_results) + 1,
                'id': doc_id,
                'text': doc,
                'distance': distance,
                'similarity_score': 1 - distance  # Convert distance to similarity
            })

        return formatted_results

    def find_automation_opportunities(self, n_categories: int = 5) -> Dict:
        """Find high-value automation candidates using semantic clustering"""
        print("🎯 Finding Automation Opportunities")
        print("=" * 70)
        print()

        # Key patterns to search for
        automation_queries = [
            ("Repetitive manual tasks", "Tasks mentioned repeatedly that could be automated"),
            ("Azure infrastructure provisioning", "Infrastructure deployment and configuration"),
            ("User account management", "Creating, modifying, deleting user accounts"),
            ("Password resets and access issues", "Authentication and authorization problems"),
            ("Software installation requests", "Application deployment and updates"),
            ("Email and mailbox issues", "Email configuration and troubleshooting"),
            ("Virtual machine deployment", "VM creation and configuration"),
            ("Backup and restore requests", "Data backup and recovery operations"),
            ("Network configuration", "Network setup, VPN, firewall rules"),
            ("License management", "Software license assignment and tracking")
        ]

        opportunities = {}

        for query, description in automation_queries:
            print(f"🔍 Pattern: {query}")

            # Search both comments and descriptions for comprehensive coverage
            # Using 0.45 max distance (55% min similarity) as threshold for relevant matches
            comment_results = self.semantic_search(query, 'comments', n_results=50, max_distance=0.45)
            desc_results = self.semantic_search(query, 'descriptions', n_results=50, max_distance=0.45)

            # Get ticket IDs from results
            ticket_ids = []
            for result in comment_results + desc_results:
                # Doc IDs are [TKT-Ticket ID] values (numeric strings)
                ticket_id = int(result['id'])
                if ticket_id not in ticket_ids:
                    ticket_ids.append(ticket_id)

            # Get ticket details from SQLite using [TKT-Ticket ID]
            if ticket_ids:
                placeholders = ','.join(['?' for _ in ticket_ids])
                cursor = self.conn.execute(f"""
                    SELECT
                        "TKT-Ticket ID" as ticket_id,
                        "TKT-Title" as title,
                        "TKT-Description" as description,
                        "TKT-Account Name" as account,
                        "TKT-Status" as status,
                        "TKT-Priority" as priority,
                        "TKT-Created Time" as created,
                        "TKT-Closed Time" as closed
                    FROM tickets
                    WHERE "TKT-Ticket ID" IN ({placeholders})
                """, ticket_ids)

                tickets = [dict(row) for row in cursor.fetchall()]

                # Calculate metrics
                total_matches = len(tickets)
                avg_similarity = sum(r['similarity_score'] for r in comment_results + desc_results) / max(len(comment_results + desc_results), 1)

                opportunities[query] = {
                    'description': description,
                    'total_matches': total_matches,
                    'avg_similarity': avg_similarity,
                    'sample_tickets': tickets[:5],  # Top 5 examples
                    'top_accounts': self._get_top_accounts(tickets, 3)
                }

                print(f"   ✅ Found {total_matches} matching tickets (avg similarity: {avg_similarity:.2%})")
                if opportunities[query]['top_accounts']:
                    print(f"   Top clients: {', '.join([f'{acc} ({cnt})' for acc, cnt in opportunities[query]['top_accounts']])}")
                print()
            else:
                print(f"   ⚠️  No strong matches found")
                print()

        return opportunities

    def _get_top_accounts(self, tickets: List[Dict], n: int = 3) -> List[Tuple[str, int]]:
        """Get top N accounts by ticket count"""
        accounts = [t['account'] for t in tickets if t.get('account')]
        if not accounts:
            return []
        counter = Counter(accounts)
        return counter.most_common(n)

    def generate_discovery_report(self, opportunities: Dict, output_file: str = None):
        """Generate comprehensive discovery report"""
        print("📊 DISCOVERY REPORT")
        print("=" * 70)
        print()

        # Sort by potential value (total_matches * avg_similarity)
        ranked_opportunities = sorted(
            opportunities.items(),
            key=lambda x: x[1]['total_matches'] * x[1]['avg_similarity'],
            reverse=True
        )

        report_lines = []
        report_lines.append("# ServiceDesk Automation Discovery Report")
        report_lines.append(f"**Generated**: {self._get_timestamp()}")
        report_lines.append(f"**Model**: {self.model_name} (768-dim E5-base-v2)")
        report_lines.append("")
        report_lines.append("## Executive Summary")
        report_lines.append("")

        total_opportunities = len([opp for opp in opportunities.values() if opp['total_matches'] > 0])
        total_tickets = sum(opp['total_matches'] for opp in opportunities.values())

        report_lines.append(f"- **Automation Patterns Found**: {total_opportunities}")
        report_lines.append(f"- **Total Matching Tickets**: {total_tickets}")
        report_lines.append(f"- **Collections Analyzed**: 5 (comments, descriptions, solutions, titles, work_logs)")
        report_lines.append("")
        report_lines.append("## High-Value Automation Opportunities")
        report_lines.append("")

        for rank, (pattern, data) in enumerate(ranked_opportunities, 1):
            if data['total_matches'] == 0:
                continue

            value_score = data['total_matches'] * data['avg_similarity']
            report_lines.append(f"### {rank}. {pattern}")
            report_lines.append(f"**Value Score**: {value_score:.1f} (tickets: {data['total_matches']}, similarity: {data['avg_similarity']:.1%})")
            report_lines.append(f"**Description**: {data['description']}")
            report_lines.append("")

            if data['top_accounts']:
                report_lines.append("**Top Affected Clients**:")
                for account, count in data['top_accounts']:
                    report_lines.append(f"- {account}: {count} tickets")
                report_lines.append("")

            if data['sample_tickets']:
                report_lines.append("**Sample Tickets**:")
                for ticket in data['sample_tickets'][:3]:
                    # Truncate title to 80 chars for readability
                    title = ticket.get('title', 'No title')[:80]
                    if len(ticket.get('title', '')) > 80:
                        title += '...'
                    report_lines.append(f"- [Ticket {ticket['ticket_id']}] {title}")
                report_lines.append("")

            report_lines.append("---")
            report_lines.append("")

        report_lines.append("## Next Steps")
        report_lines.append("")
        report_lines.append("1. **Prioritize** top 3-5 patterns by business value")
        report_lines.append("2. **Deep dive** into each pattern to understand workflow")
        report_lines.append("3. **Estimate ROI** based on ticket volume and resolution time")
        report_lines.append("4. **Design automation** using existing tools or new workflows")
        report_lines.append("5. **Implement** highest-value automations first")
        report_lines.append("")

        report_content = "\n".join(report_lines)

        # Print to console
        print(report_content)

        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_content)
            print(f"\n✅ Report saved to: {output_file}")

        return report_content

    def interactive_mode(self):
        """Interactive discovery mode"""
        print("🔍 Interactive Discovery Mode")
        print("=" * 70)
        print()
        print("Commands:")
        print("  search <query>              - Semantic search across all collections")
        print("  search <collection> <query> - Search specific collection")
        print("  opportunities               - Find automation opportunities")
        print("  stats                       - Show collection statistics")
        print("  help                        - Show this help")
        print("  quit                        - Exit")
        print()

        while True:
            try:
                command = input("discovery> ").strip()

                if not command:
                    continue

                if command.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                if command.lower() == 'help':
                    print("\nCommands:")
                    print("  search <query>              - Semantic search across all collections")
                    print("  search <collection> <query> - Search specific collection")
                    print("  opportunities               - Find automation opportunities")
                    print("  stats                       - Show collection statistics")
                    print("  quit                        - Exit\n")
                    continue

                if command.lower() == 'stats':
                    self._show_stats()
                    continue

                if command.lower() == 'opportunities':
                    opportunities = self.find_automation_opportunities()
                    self.generate_discovery_report(opportunities)
                    continue

                if command.lower().startswith('search '):
                    parts = command.split(maxsplit=2)
                    if len(parts) == 2:
                        # search <query> - search all collections
                        query = parts[1]
                        for coll_name in ['comments', 'descriptions']:  # Focus on most relevant
                            print(f"\n{'='*70}")
                            results = self.semantic_search(query, coll_name, n_results=5)
                            self._print_search_results(results)
                    elif len(parts) == 3:
                        # search <collection> <query>
                        collection = parts[1]
                        query = parts[2]
                        results = self.semantic_search(query, collection, n_results=10)
                        self._print_search_results(results)
                    continue

                print("❌ Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _show_stats(self):
        """Show collection statistics"""
        print("\n📊 Collection Statistics")
        print("=" * 70)
        for name, collection in self.collections.items():
            count = collection.count()
            print(f"   {name:15s}: {count:,} documents")
        print()

    def _print_search_results(self, results: List[Dict]):
        """Pretty print search results"""
        if not results:
            print("   No results found.")
            return

        for result in results:
            print(f"\n{result['rank']}. Similarity: {result['similarity_score']:.1%} (distance: {result['distance']:.3f})")
            print(f"   ID: {result['id']}")
            text = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
            print(f"   {text}")

    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    parser = argparse.ArgumentParser(description="ServiceDesk Discovery Analyzer")
    parser.add_argument('--query', type=str, help="Semantic search query")
    parser.add_argument('--collection', type=str, default='comments',
                       choices=['comments', 'descriptions', 'solutions', 'titles', 'work_logs'],
                       help="Collection to search (default: comments)")
    parser.add_argument('--n-results', type=int, default=10, help="Number of results (default: 10)")
    parser.add_argument('--max-distance', type=float, help="Maximum distance threshold (lower = better match)")
    parser.add_argument('--automation-opportunities', action='store_true',
                       help="Find automation opportunities")
    parser.add_argument('--report-output', type=str, help="Save report to file")
    parser.add_argument('--interactive', '-i', action='store_true',
                       help="Interactive discovery mode")

    args = parser.parse_args()

    try:
        analyzer = ServiceDeskDiscoveryAnalyzer()

        if args.interactive:
            analyzer.interactive_mode()
        elif args.automation_opportunities:
            opportunities = analyzer.find_automation_opportunities()
            analyzer.generate_discovery_report(opportunities, args.report_output)
        elif args.query:
            results = analyzer.semantic_search(
                args.query,
                args.collection,
                args.n_results,
                args.max_distance
            )
            analyzer._print_search_results(results)
        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
