#!/usr/bin/env python3
"""
LinkedIn MCP Server
==================

Model Context Protocol server for LinkedIn data processing and analysis.
Processes LinkedIn data exports to provide professional network intelligence.

Capabilities:
- LinkedIn data export processing
- Connection network analysis
- Career tracking and job intelligence
- Company insights from professional network
- Professional contact discovery
"""

import json
import csv
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add MCP library to path
try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
except ImportError:
    print("MCP library not found. Installing...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "mcp"])
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linkedin-mcp")

class LinkedInDataProcessor:
    """Processes LinkedIn data exports"""

    def __init__(self, data_dir: Optional[str] = None):
        """Initialize with LinkedIn data directory"""
        self.data_dir = data_dir or os.getenv("LINKEDIN_DATA_PATH", "~/Downloads/linkedin_data")
        self.data_dir = os.path.expanduser(self.data_dir)

        # Cache for processed data
        self._connections_cache = None
        self._profile_cache = None
        self._last_updated = None

    def find_linkedin_export(self) -> Optional[str]:
        """Find LinkedIn data export directory"""
        possible_paths = [
            self.data_dir,
            os.path.expanduser("~/Downloads/linkedin_data"),
            os.path.expanduser("~/Downloads/Basic_LinkedInDataExport*"),
            os.path.expanduser("~/Documents/linkedin_export"),
        ]

        for path_pattern in possible_paths:
            if '*' in path_pattern:
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    return matches[0]
            elif os.path.exists(path_pattern):
                return path_pattern

        return None

    def load_connections(self) -> List[Dict[str, Any]]:
        """Load connections from LinkedIn export"""
        export_path = self.find_linkedin_export()
        if not export_path:
            return []

        connections_file = os.path.join(export_path, "Connections.csv")
        if not os.path.exists(connections_file):
            logger.warning(f"Connections.csv not found in {export_path}")
            return []

        connections = []
        try:
            with open(connections_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean and structure connection data
                    connection = {
                        'first_name': row.get('First Name', '').strip(),
                        'last_name': row.get('Last Name', '').strip(),
                        'email': row.get('Email Address', '').strip(),
                        'company': row.get('Company', '').strip(),
                        'position': row.get('Position', '').strip(),
                        'connected_on': row.get('Connected On', '').strip(),
                        'full_name': f"{row.get('First Name', '').strip()} {row.get('Last Name', '').strip()}".strip()
                    }

                    # Add derived insights
                    connection['has_email'] = bool(connection['email'])
                    connection['connection_year'] = self._extract_year(connection['connected_on'])
                    connection['is_recent'] = self._is_recent_connection(connection['connected_on'])

                    connections.append(connection)

            self._connections_cache = connections
            self._last_updated = datetime.now()
            logger.info(f"Loaded {len(connections)} connections from LinkedIn export")

        except Exception as e:
            logger.error(f"Error loading connections: {e}")
            return []

        return connections

    def load_profile_data(self) -> Dict[str, Any]:
        """Load profile information from LinkedIn export"""
        export_path = self.find_linkedin_export()
        if not export_path:
            return {}

        profile_file = os.path.join(export_path, "Profile.csv")
        if not os.path.exists(profile_file):
            logger.warning(f"Profile.csv not found in {export_path}")
            return {}

        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                profile_data = next(reader, {})

            self._profile_cache = profile_data
            return profile_data

        except Exception as e:
            logger.error(f"Error loading profile: {e}")
            return {}

    def analyze_network(self) -> Dict[str, Any]:
        """Analyze professional network patterns"""
        connections = self.load_connections()
        if not connections:
            return {"error": "No connections data available"}

        # Company analysis
        companies = {}
        positions = {}
        connection_years = {}
        recent_connections = []

        for conn in connections:
            # Company clustering
            company = conn.get('company', 'Unknown')
            if company and company != 'Unknown':
                companies[company] = companies.get(company, 0) + 1

            # Position analysis
            position = conn.get('position', 'Unknown')
            if position and position != 'Unknown':
                positions[position] = positions.get(position, 0) + 1

            # Connection timeline
            year = conn.get('connection_year')
            if year:
                connection_years[year] = connection_years.get(year, 0) + 1

            # Recent connections (last 6 months)
            if conn.get('is_recent'):
                recent_connections.append(conn)

        # Sort and get top results
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:10]
        top_positions = sorted(positions.items(), key=lambda x: x[1], reverse=True)[:10]
        connection_timeline = sorted(connection_years.items(), key=lambda x: x[0], reverse=True)

        return {
            'total_connections': len(connections),
            'total_companies': len(companies),
            'total_unique_positions': len(positions),
            'connections_with_email': len([c for c in connections if c.get('has_email')]),
            'recent_connections_6m': len(recent_connections),
            'top_companies': top_companies,
            'top_positions': top_positions,
            'connection_timeline': connection_timeline[:5],
            'sample_recent_connections': recent_connections[:5]
        }

    def find_professionals_by_company(self, company_name: str) -> List[Dict[str, Any]]:
        """Find connections at specific company"""
        connections = self.load_connections()

        matches = []
        company_lower = company_name.lower()

        for conn in connections:
            if company_lower in conn.get('company', '').lower():
                matches.append(conn)

        return sorted(matches, key=lambda x: x.get('connected_on', ''), reverse=True)

    def track_career_changes(self) -> Dict[str, Any]:
        """Analyze career progression patterns in network"""
        connections = self.load_connections()

        # This is a simplified analysis - would need historical data for full tracking
        senior_roles = []
        leadership_keywords = ['director', 'manager', 'lead', 'head', 'chief', 'vp', 'senior', 'principal']

        for conn in connections:
            position = conn.get('position', '').lower()
            if any(keyword in position for keyword in leadership_keywords):
                senior_roles.append(conn)

        # Company transitions (simplified - would need historical data)
        company_counts = {}
        for conn in connections:
            company = conn.get('company')
            if company:
                company_counts[company] = company_counts.get(company, 0) + 1

        return {
            'total_senior_connections': len(senior_roles),
            'senior_percentage': (len(senior_roles) / len(connections)) * 100 if connections else 0,
            'top_senior_companies': sorted(
                [(comp, count) for comp, count in company_counts.items()
                 if any(conn['company'] == comp for conn in senior_roles)],
                key=lambda x: x[1], reverse=True
            )[:10],
            'sample_senior_roles': senior_roles[:10]
        }

    def get_export_status(self) -> Dict[str, Any]:
        """Check status of LinkedIn data export"""
        export_path = self.find_linkedin_export()

        if not export_path:
            return {
                'status': 'not_found',
                'message': 'LinkedIn data export not found',
                'search_paths': [
                    os.path.expanduser("~/Downloads/linkedin_data"),
                    os.path.expanduser("~/Downloads/Basic_LinkedInDataExport*"),
                    os.path.expanduser("~/Documents/linkedin_export")
                ]
            }

        # Check available files
        files = os.listdir(export_path) if os.path.exists(export_path) else []
        csv_files = [f for f in files if f.endswith('.csv')]

        return {
            'status': 'found',
            'export_path': export_path,
            'total_files': len(files),
            'csv_files': csv_files,
            'has_connections': 'Connections.csv' in files,
            'has_profile': 'Profile.csv' in files,
            'last_modified': self._get_last_modified(export_path) if export_path else None
        }

    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extract year from date string"""
        if not date_str:
            return None

        try:
            # LinkedIn typically uses format like "Oct 15, 2023"
            if ',' in date_str:
                year_part = date_str.split(',')[-1].strip()
                return int(year_part)
        except (ValueError, IndexError):
            pass

        return None

    def _is_recent_connection(self, date_str: str, months: int = 6) -> bool:
        """Check if connection is recent (within specified months)"""
        year = self._extract_year(date_str)
        if not year:
            return False

        current_year = datetime.now().year
        # Simplified - assumes current year connections are recent
        return year >= current_year

    def _get_last_modified(self, path: str) -> str:
        """Get last modified time of directory"""
        try:
            timestamp = os.path.getmtime(path)
            return datetime.fromtimestamp(timestamp).isoformat()
        except OSError:
            return "unknown"

class LinkedInMCPServer:
    """Main LinkedIn MCP Server"""

    def __init__(self):
        self.processor = LinkedInDataProcessor()
        self.server = Server("linkedin-professional")

    async def serve(self):
        """Start the MCP server"""

        # Define tools
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available LinkedIn tools"""
            return [
                Tool(
                    name="check_linkedin_export",
                    description="Check status of LinkedIn data export and available files",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="analyze_network",
                    description="Analyze professional network patterns, companies, and connections",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_recent": {
                                "type": "boolean",
                                "description": "Include recent connections analysis",
                                "default": True
                            }
                        },
                    },
                ),
                Tool(
                    name="find_professionals_by_company",
                    description="Find connections working at a specific company",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "company_name": {
                                "type": "string",
                                "description": "Name of the company to search for"
                            }
                        },
                        "required": ["company_name"]
                    },
                ),
                Tool(
                    name="track_career_changes",
                    description="Analyze career progression patterns in professional network",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                    },
                ),
                Tool(
                    name="get_connection_stats",
                    description="Get detailed statistics about LinkedIn connections",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "year": {
                                "type": "integer",
                                "description": "Filter connections by specific year",
                                "minimum": 2003,
                                "maximum": 2025
                            }
                        },
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls"""

            if name == "check_linkedin_export":
                result = self.processor.get_export_status()
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "analyze_network":
                result = self.processor.analyze_network()
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "find_professionals_by_company":
                company_name = arguments.get("company_name", "")
                if not company_name:
                    return [TextContent(type="text", text="Error: company_name is required")]

                result = self.processor.find_professionals_by_company(company_name)
                return [TextContent(type="text", text=json.dumps({
                    "company": company_name,
                    "total_connections": len(result),
                    "connections": result[:20]  # Limit results
                }, indent=2))]

            elif name == "track_career_changes":
                result = self.processor.track_career_changes()
                return [TextContent(type="text", text=json.dumps(result, indent=2))]

            elif name == "get_connection_stats":
                # Load connections and filter if needed
                connections = self.processor.load_connections()
                year_filter = arguments.get("year")

                if year_filter:
                    connections = [c for c in connections if c.get('connection_year') == year_filter]

                stats = {
                    "total_connections": len(connections),
                    "connections_with_email": len([c for c in connections if c.get('has_email')]),
                    "year_filter": year_filter,
                    "sample_connections": connections[:10]
                }

                return [TextContent(type="text", text=json.dumps(stats, indent=2))]

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        # Define resources
        @self.server.list_resources()
        async def handle_list_resources() -> list[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="linkedin://export-status",
                    name="LinkedIn Export Status",
                    description="Current status of LinkedIn data export",
                    mimeType="application/json",
                ),
                Resource(
                    uri="linkedin://network-overview",
                    name="Network Overview",
                    description="High-level overview of professional network",
                    mimeType="application/json",
                ),
                Resource(
                    uri="linkedin://connection-intelligence",
                    name="Connection Intelligence",
                    description="Intelligent analysis of professional connections",
                    mimeType="application/json",
                ),
            ]

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle resource reading"""

            if uri == "linkedin://export-status":
                result = self.processor.get_export_status()
                return json.dumps(result, indent=2)

            elif uri == "linkedin://network-overview":
                result = self.processor.analyze_network()
                return json.dumps(result, indent=2)

            elif uri == "linkedin://connection-intelligence":
                network_analysis = self.processor.analyze_network()
                career_analysis = self.processor.track_career_changes()

                combined = {
                    "network_analysis": network_analysis,
                    "career_analysis": career_analysis,
                    "generated_at": datetime.now().isoformat()
                }
                return json.dumps(combined, indent=2)

            else:
                raise ValueError(f"Unknown resource: {uri}")

        # Start server
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="linkedin-professional",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

async def main():
    """Main entry point"""
    server = LinkedInMCPServer()
    await server.serve()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
