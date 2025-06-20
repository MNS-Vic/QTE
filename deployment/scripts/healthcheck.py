#!/usr/bin/env python3
"""
QTE Production Health Check Script
Comprehensive health monitoring for production deployment.
"""

import os
import sys
import time
import json
import psutil
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class HealthCheckResult:
    """Health check result data structure."""
    name: str
    status: str  # "healthy", "unhealthy", "warning"
    message: str
    duration_ms: float
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Comprehensive health checker for QTE production environment."""
    
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.admin_url = "http://localhost:8081"
        self.metrics_url = "http://localhost:9090"
        self.timeout = 10.0
        self.results: List[HealthCheckResult] = []
        
    def check_application_health(self) -> HealthCheckResult:
        """Check main application health."""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                return HealthCheckResult(
                    name="application",
                    status="healthy",
                    message="Application is responding normally",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    details=data
                )
            else:
                return HealthCheckResult(
                    name="application",
                    status="unhealthy",
                    message=f"Application returned status {response.status_code}",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except requests.exceptions.RequestException as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="application",
                status="unhealthy",
                message=f"Application not responding: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def check_database_health(self) -> HealthCheckResult:
        """Check database connectivity."""
        start_time = time.time()
        
        try:
            # Check PostgreSQL
            result = subprocess.run(
                ["pg_isready", "-h", "postgres", "-p", "5432", "-U", "qte"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result.returncode == 0:
                return HealthCheckResult(
                    name="database",
                    status="healthy",
                    message="Database is accepting connections",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                )
            else:
                return HealthCheckResult(
                    name="database",
                    status="unhealthy",
                    message=f"Database connection failed: {result.stderr}",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="database",
                status="unhealthy",
                message="Database health check timed out",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="database",
                status="unhealthy",
                message=f"Database health check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def check_redis_health(self) -> HealthCheckResult:
        """Check Redis connectivity."""
        start_time = time.time()
        
        try:
            result = subprocess.run(
                ["redis-cli", "-h", "redis", "-p", "6379", "ping"],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result.returncode == 0 and "PONG" in result.stdout:
                return HealthCheckResult(
                    name="redis",
                    status="healthy",
                    message="Redis is responding to ping",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                )
            else:
                return HealthCheckResult(
                    name="redis",
                    status="unhealthy",
                    message=f"Redis ping failed: {result.stderr}",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except subprocess.TimeoutExpired:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="redis",
                status="unhealthy",
                message="Redis health check timed out",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="redis",
                status="unhealthy",
                message=f"Redis health check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def check_system_resources(self) -> HealthCheckResult:
        """Check system resource usage."""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Define thresholds
            cpu_threshold = 80
            memory_threshold = 85
            disk_threshold = 90
            
            status = "healthy"
            messages = []
            
            if cpu_percent > cpu_threshold:
                status = "warning"
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > memory_threshold:
                status = "warning"
                messages.append(f"High memory usage: {memory.percent:.1f}%")
            
            if disk.percent > disk_threshold:
                status = "unhealthy"
                messages.append(f"High disk usage: {disk.percent:.1f}%")
            
            message = "; ".join(messages) if messages else "System resources within normal limits"
            
            details = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            }
            
            return HealthCheckResult(
                name="system_resources",
                status=status,
                message=message,
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat(),
                details=details
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="system_resources",
                status="unhealthy",
                message=f"System resource check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def check_metrics_endpoint(self) -> HealthCheckResult:
        """Check metrics endpoint availability."""
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.metrics_url}/metrics",
                timeout=self.timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                # Count metrics
                metrics_count = len([line for line in response.text.split('\n') 
                                   if line and not line.startswith('#')])
                
                return HealthCheckResult(
                    name="metrics",
                    status="healthy",
                    message=f"Metrics endpoint available with {metrics_count} metrics",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    details={"metrics_count": metrics_count}
                )
            else:
                return HealthCheckResult(
                    name="metrics",
                    status="unhealthy",
                    message=f"Metrics endpoint returned status {response.status_code}",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except requests.exceptions.RequestException as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="metrics",
                status="unhealthy",
                message=f"Metrics endpoint not responding: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def check_log_files(self) -> HealthCheckResult:
        """Check log file accessibility and recent activity."""
        start_time = time.time()
        
        try:
            log_dir = "/app/logs"
            
            if not os.path.exists(log_dir):
                return HealthCheckResult(
                    name="logs",
                    status="unhealthy",
                    message="Log directory does not exist",
                    duration_ms=(time.time() - start_time) * 1000,
                    timestamp=datetime.utcnow().isoformat()
                )
            
            # Check for recent log activity
            recent_logs = []
            current_time = time.time()
            
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    if current_time - mtime < 300:  # Modified within 5 minutes
                        recent_logs.append(filename)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if recent_logs:
                return HealthCheckResult(
                    name="logs",
                    status="healthy",
                    message=f"Log files are being written: {', '.join(recent_logs)}",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat(),
                    details={"recent_logs": recent_logs}
                )
            else:
                return HealthCheckResult(
                    name="logs",
                    status="warning",
                    message="No recent log activity detected",
                    duration_ms=duration_ms,
                    timestamp=datetime.utcnow().isoformat()
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name="logs",
                status="unhealthy",
                message=f"Log file check failed: {str(e)}",
                duration_ms=duration_ms,
                timestamp=datetime.utcnow().isoformat()
            )
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks and return comprehensive results."""
        print("Running QTE health checks...")
        
        # Run all health checks
        checks = [
            self.check_application_health,
            self.check_database_health,
            self.check_redis_health,
            self.check_system_resources,
            self.check_metrics_endpoint,
            self.check_log_files
        ]
        
        self.results = []
        for check in checks:
            try:
                result = check()
                self.results.append(result)
                print(f"✓ {result.name}: {result.status} - {result.message}")
            except Exception as e:
                error_result = HealthCheckResult(
                    name=check.__name__,
                    status="unhealthy",
                    message=f"Health check failed: {str(e)}",
                    duration_ms=0,
                    timestamp=datetime.utcnow().isoformat()
                )
                self.results.append(error_result)
                print(f"✗ {check.__name__}: unhealthy - {str(e)}")
        
        # Determine overall health
        overall_status = "healthy"
        unhealthy_count = sum(1 for r in self.results if r.status == "unhealthy")
        warning_count = sum(1 for r in self.results if r.status == "warning")
        
        if unhealthy_count > 0:
            overall_status = "unhealthy"
        elif warning_count > 0:
            overall_status = "warning"
        
        # Prepare summary
        summary = {
            "overall_status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "total_checks": len(self.results),
            "healthy_checks": sum(1 for r in self.results if r.status == "healthy"),
            "warning_checks": warning_count,
            "unhealthy_checks": unhealthy_count,
            "checks": [
                {
                    "name": r.name,
                    "status": r.status,
                    "message": r.message,
                    "duration_ms": r.duration_ms,
                    "timestamp": r.timestamp,
                    "details": r.details
                }
                for r in self.results
            ]
        }
        
        return summary


def main():
    """Main health check execution."""
    checker = HealthChecker()
    results = checker.run_all_checks()
    
    # Print JSON results for programmatic consumption
    print("\n" + "="*60)
    print("HEALTH CHECK RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))
    
    # Exit with appropriate code
    if results["overall_status"] == "unhealthy":
        print(f"\n❌ Health check FAILED: {results['unhealthy_checks']} unhealthy checks")
        sys.exit(1)
    elif results["overall_status"] == "warning":
        print(f"\n⚠️  Health check WARNING: {results['warning_checks']} warning checks")
        sys.exit(0)
    else:
        print(f"\n✅ Health check PASSED: All {results['total_checks']} checks healthy")
        sys.exit(0)


if __name__ == "__main__":
    main()
