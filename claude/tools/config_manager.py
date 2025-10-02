#!/usr/bin/env python3
"""
Configuration Manager for Maia Dashboard Platform
Phase 2: Architecture Standardization - YAML Configuration Management

Validates and manages centralized dashboard configuration.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import requests

class DashboardConfigManager:
    """Centralized configuration management for dashboard services"""
    
    def __init__(self, config_path: str = "claude/tools/monitoring/config/dashboard_services.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration structure and content"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "summary": {}
        }
        
        # Check required sections
        required_sections = ["services", "global", "service_mesh", "hub"]
        for section in required_sections:
            if section not in self.config:
                validation_result["errors"].append(f"Missing required section: {section}")
                validation_result["valid"] = False
        
        # Validate services
        if "services" in self.config:
            services = self.config["services"]
            ports_used = []
            
            for service_name, service_config in services.items():
                # Check required service fields
                required_fields = ["port", "health_endpoint", "framework", "category"]
                for field in required_fields:
                    if field not in service_config:
                        validation_result["errors"].append(
                            f"Service {service_name} missing required field: {field}"
                        )
                        validation_result["valid"] = False
                
                # Check for port conflicts
                port = service_config.get("port")
                if port in ports_used:
                    validation_result["errors"].append(f"Port conflict: {port} used by multiple services")
                    validation_result["valid"] = False
                else:
                    ports_used.append(port)
        
        # Generate summary
        validation_result["summary"] = {
            "total_services": len(self.config.get("services", {})),
            "auto_start_services": len([s for s in self.config.get("services", {}).values() if s.get("auto_start", False)]),
            "ports_used": sorted(ports_used),
            "frameworks": list(set([s.get("framework") for s in self.config.get("services", {}).values()])),
            "categories": list(set([s.get("category") for s in self.config.get("services", {}).values()]))
        }
        
        return validation_result
    
    def health_check_all_services(self) -> Dict[str, Any]:
        """Check health of all configured services"""
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "service_mesh_enabled": self.config.get("service_mesh", {}).get("enabled", False),
            "services": {},
            "summary": {"healthy": 0, "unhealthy": 0, "unreachable": 0}
        }
        
        services = self.config.get("services", {})
        
        for service_name, service_config in services.items():
            port = service_config.get("port")
            health_endpoint = service_config.get("health_endpoint", "/health")
            
            try:
                url = f"http://127.0.0.1:{port}{health_endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    try:
                        health_data = response.json()
                        status = health_data.get("status", "unknown")
                        health_results["services"][service_name] = {
                            "status": status,
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                            "service_info": health_data
                        }
                        if status == "healthy":
                            health_results["summary"]["healthy"] += 1
                        else:
                            health_results["summary"]["unhealthy"] += 1
                    except json.JSONDecodeError:
                        health_results["services"][service_name] = {
                            "status": "unhealthy",
                            "error": "Invalid JSON response"
                        }
                        health_results["summary"]["unhealthy"] += 1
                else:
                    health_results["services"][service_name] = {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status_code}"
                    }
                    health_results["summary"]["unhealthy"] += 1
                    
            except requests.exceptions.RequestException as e:
                health_results["services"][service_name] = {
                    "status": "unreachable",
                    "error": str(e)
                }
                health_results["summary"]["unreachable"] += 1
        
        return health_results
    
    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific service"""
        return self.config.get("services", {}).get(service_name)
    
    def list_services_by_category(self, category: str) -> List[Dict[str, Any]]:
        """List all services in a specific category"""
        services = []
        for service_name, service_config in self.config.get("services", {}).items():
            if service_config.get("category") == category:
                services.append({
                    "name": service_name,
                    "config": service_config
                })
        return services
    
    def generate_nginx_config(self) -> str:
        """Generate nginx configuration from YAML config"""
        upstreams = []
        servers = []
        
        # Generate upstreams
        for service_name, service_config in self.config.get("services", {}).items():
            port = service_config.get("port")
            nginx_upstream = service_config.get("nginx_upstream", service_name)
            
            upstreams.append(f"""upstream {nginx_upstream} {{
    server 127.0.0.1:{port};
}}""")
        
        # Generate server blocks would go here
        nginx_config = f"""# Auto-generated nginx configuration
# Generated from: {self.config_path}
# Timestamp: {datetime.now().isoformat()}

{chr(10).join(upstreams)}

# Additional server configuration would be generated here
"""
        return nginx_config

def main():
    """Main CLI interface"""
    import sys
    
    config_manager = DashboardConfigManager()
    
    if len(sys.argv) < 2:
        print("Usage: python config_manager.py [validate|health|services|nginx]")
        return
    
    command = sys.argv[1]
    
    if command == "validate":
        result = config_manager.validate_config()
        print(json.dumps(result, indent=2))
    
    elif command == "health":
        result = config_manager.health_check_all_services()
        print(json.dumps(result, indent=2))
    
    elif command == "services":
        services = config_manager.config.get("services", {})
        for name, config in services.items():
            print(f"{name}: {config.get('framework')} on port {config.get('port')}")
    
    elif command == "nginx":
        nginx_config = config_manager.generate_nginx_config()
        print(nginx_config)
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()