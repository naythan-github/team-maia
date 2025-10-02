#!/usr/bin/env python3
"""
System Health Monitor
====================

Basic health monitoring system for production services.
"""

import asyncio
import psutil
from typing import Dict, Any

class SystemHealthMonitor:
    """System health monitoring for production deployment"""
    
    def __init__(self, user_id: str = "naythan"):
        self.user_id = user_id
        
    async def run_all_health_checks(self) -> Dict[str, Any]:
        """Run basic health checks"""
        
        # Basic system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Count critical/warning issues
        critical_checks = 0
        warning_checks = 0
        
        if cpu_percent > 80:
            critical_checks += 1
        elif cpu_percent > 60:
            warning_checks += 1
            
        if memory.percent > 80:
            critical_checks += 1
        elif memory.percent > 60:
            warning_checks += 1
        
        # Determine overall health
        if critical_checks > 0:
            overall_health = "critical"
        elif warning_checks > 0:
            overall_health = "warning"
        else:
            overall_health = "healthy"
        
        return {
            "overall_health": overall_health,
            "critical_checks": critical_checks,
            "warning_checks": warning_checks,
            "healthy_checks": 3 - critical_checks - warning_checks,
            "total_checks": 3,
            "system_metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": round((disk.used / disk.total) * 100, 2)
            }
        }

async def main():
    """Test health monitoring"""
    monitor = SystemHealthMonitor()
    results = await monitor.run_all_health_checks()
    
    print("🏥 System Health Check")
    print("=" * 25)
    print(f"Overall Health: {results['overall_health'].upper()}")
    print(f"CPU Usage: {results['system_metrics']['cpu_percent']:.1f}%")
    print(f"Memory Usage: {results['system_metrics']['memory_percent']:.1f}%") 
    print(f"Disk Usage: {results['system_metrics']['disk_percent']:.1f}%")
    print(f"Critical Issues: {results['critical_checks']}")
    print(f"Warnings: {results['warning_checks']}")

if __name__ == "__main__":
    asyncio.run(main())