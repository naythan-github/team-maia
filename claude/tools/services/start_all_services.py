#!/usr/bin/env python3
"""
Production Service Manager - Start All Services
===============================================

Starts all Maia production services in the correct order with health monitoring.
"""

import asyncio
import subprocess
import time
import json
import os
from pathlib import Path
import signal
import sys

class ProductionServiceManager:
    def __init__(self):
        self.services = {}
        self.service_order = [
            "intelligence_engine",
            "continuous_monitoring", 
            "background_learning",
            "alert_delivery",
            "health_monitor"
        ]
        
    def start_service(self, service_name):
        """Start a production service"""
        script_path = f"claude/tools/services/{service_name}_service.py"
        
        if not os.path.exists(script_path):
            print(f"❌ Service script not found: {script_path}")
            return False
        
        try:
            # Start service in background
            process = subprocess.Popen([
                "python3", script_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.services[service_name] = {
                "process": process,
                "pid": process.pid,
                "started_at": time.time()
            }
            
            print(f"✅ Started {service_name} (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start {service_name}: {e}")
            return False
    
    def stop_service(self, service_name):
        """Stop a production service"""
        if service_name in self.services:
            process = self.services[service_name]["process"]
            process.terminate()
            process.wait()
            del self.services[service_name]
            print(f"🛑 Stopped {service_name}")
    
    def start_all_services(self):
        """Start all services in correct order"""
        print("🚀 Starting Maia Production Services")
        print("=" * 40)
        
        for service_name in self.service_order:
            print(f"📦 Starting {service_name}...")
            success = self.start_service(service_name)
            if not success:
                print(f"❌ Failed to start {service_name}")
                return False
            
            # Wait between service starts
            time.sleep(2)
        
        print(f"\\n✅ All {len(self.service_order)} services started successfully!")
        return True
    
    def stop_all_services(self):
        """Stop all running services"""
        print("🛑 Stopping all services...")
        for service_name in list(self.services.keys()):
            self.stop_service(service_name)
        print("✅ All services stopped")
    
    def service_status(self):
        """Show status of all services"""
        print("📊 Service Status:")
        print("-" * 20)
        
        for service_name in self.service_order:
            if service_name in self.services:
                service = self.services[service_name]
                uptime = int(time.time() - service["started_at"])
                print(f"✅ {service_name}: Running (PID: {service['pid']}, Uptime: {uptime}s)")
            else:
                print(f"❌ {service_name}: Stopped")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\\n🛑 Received shutdown signal, stopping all services...")
        self.stop_all_services()
        sys.exit(0)

def main():
    manager = ProductionServiceManager()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "start":
            success = manager.start_all_services()
            if success:
                print("\\n📊 Service monitoring active. Press Ctrl+C to stop all services.")
                try:
                    while True:
                        time.sleep(30)
                        manager.service_status()
                except KeyboardInterrupt:
                    manager.stop_all_services()
        
        elif command == "stop":
            manager.stop_all_services()
        
        elif command == "status":
            manager.service_status()
            
        else:
            print("Usage: python3 start_all_services.py [start|stop|status]")
    else:
        print("Usage: python3 start_all_services.py [start|stop|status]")

if __name__ == "__main__":
    main()