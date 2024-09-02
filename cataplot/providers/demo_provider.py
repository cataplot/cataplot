"""
This module contains the DemoAdapter class.  It implements the BaseAdapter
interface and provides simulated data for plotting.
"""
from dataclasses import dataclass

from .base import BaseAdapter


from dataclasses import dataclass

@dataclass
class ServerMetric:
    """
    Data class for server metrics.
    """
    name: str
    description: str
    units: str

@dataclass
class ServerHost:
    """
    Data class for server hosts.
    """
    name: str
    description: str

# List of ServerMetric instances
SERVER_METRICS = [
    ServerMetric('CPU Usage', 'Overall CPU usage and per core usage', 'Percentage'),
    ServerMetric('Memory Usage', 'Total, used, and free memory including swap usage', 'Bytes'),
    ServerMetric('Disk I/O', 'Disk read/write operations per second, latency, and queue length', 'IOPS/Latency'),
    ServerMetric('Network I/O', 'Network bandwidth usage, packets sent/received, and errors', 'Mbps/Packets'),
    ServerMetric('Disk Space Utilization', 'Disk space usage per partition and overall', 'Bytes'),
    ServerMetric('Process Count', 'Number of running and blocked processes', 'Count'),
    ServerMetric('System Load Average', 'Short, medium, and long-term system load', 'Load Average'),
    ServerMetric('Context Switches', 'Rate of context switching between processes', 'Switches per second'),
    ServerMetric('Interrupts per Second', 'Hardware and software interrupts per second', 'Interrupts per second'),
    ServerMetric('CPU Temperature', 'Temperature of the CPU, especially for physical servers', 'Celsius'),
    ServerMetric('Application Response Time', 'Average, P95, and P99 latencies for applications', 'Milliseconds'),
    ServerMetric('Request Rate', 'Number of requests per second handled by the application', 'Requests per second'),
    ServerMetric('Error Rate', 'HTTP 4xx/5xx errors or application-specific errors', 'Errors per second'),
    ServerMetric('Throughput', 'Number of successful transactions per second', 'Transactions per second'),
    ServerMetric('Database Query Performance', 'Execution time, query throughput, and errors for database queries', 'Milliseconds/Queries per second'),
    ServerMetric('Cache Hit/Miss Ratio', 'Ratio of cache hits to misses', 'Ratio'),
    ServerMetric('Session Count', 'Number of active sessions and average session duration', 'Count/Seconds'),
    ServerMetric('Packet Loss', 'Percentage of packets lost in network transmission', 'Percentage'),
    ServerMetric('Network Latency', 'Round-trip time and ping response time', 'Milliseconds'),
    ServerMetric('Connection Count', 'Number of active, failed, and dropped connections', 'Count'),
    ServerMetric('Bandwidth Utilization', 'Upstream and downstream bandwidth utilization', 'Mbps'),
    ServerMetric('DNS Resolution Time', 'Time taken for DNS lookups', 'Milliseconds'),
    ServerMetric('Node Availability', 'Uptime and downtime of each node in the cluster', 'Percentage'),
    ServerMetric('Cluster Load Balancing Efficiency', 'Distribution of requests across nodes', 'Percentage'),
    ServerMetric('Replication Lag', 'Lag time in database replication', 'Milliseconds'),
    ServerMetric('Failover Events', 'Number and duration of failover events', 'Count/Seconds'),
    ServerMetric('Node Resource Utilization', 'CPU, memory, and disk usage per node', 'Percentage/Bytes'),
    ServerMetric('Unauthorized Access Attempts', 'Number of unauthorized access attempts', 'Count'),
    ServerMetric('SSL/TLS Certificate Expiry', 'Days remaining until SSL/TLS certificate expiry', 'Days'),
    ServerMetric('Firewall Activity', 'Number of blocked and allowed requests by the firewall', 'Count'),
    ServerMetric('Service Latency', 'Latency of individual microservices', 'Milliseconds'),
    ServerMetric('Application Deployment Time', 'Time taken to deploy application updates', 'Seconds'),
    ServerMetric('Backup/Restore Performance', 'Time taken to backup and restore data', 'Seconds'),
    ServerMetric('Log File Size', 'Rate of log file growth', 'Bytes/Second'),
]

SERVER_HOSTS = [
    ServerHost('web-01', 'Web server for the main website'),
    ServerHost('web-02', 'Backup web server for the main website'),
    ServerHost('db-01', 'Primary database server'),
    ServerHost('db-02', 'Backup database server'),
    ServerHost('app-01', 'Application server for the main application'),
    ServerHost('app-02', 'Backup application server'),
    ServerHost('cache-01', 'Cache server for the main website'),
    ServerHost('cache-02', 'Backup cache server'),
    ServerHost('lb-01', 'Load balancer for the main website'),
    ServerHost('lb-02', 'Backup load balancer'),
    ServerHost('monitoring-01', 'Monitoring server for the server cluster'),
    ServerHost('monitoring-02', 'Backup monitoring server'),
    ServerHost('logging-01', 'Logging server for the server cluster'),
    ServerHost('logging-02', 'Backup logging server'),
    ServerHost('backup-01', 'Backup server for the server cluster'),
    ServerHost('backup-02', 'Secondary backup server'),
    ServerHost('security-01', 'Security server for the server cluster'),
    ServerHost('security-02', 'Backup security server'),
    ServerHost('dev-01', 'Development server for the server cluster'),
    ServerHost('dev-02', 'Backup development server'),
]


class DemoAdapter(BaseAdapter):
    """
    Adapter that provides simulated data for plotting.
    """
    def __init__(self):
        super().__init__()

    def listdir(self, path: str = '/') -> list[tuple[str, str, str, str]]:
        """
        Returns a list of (name, type, description, units) items in the
        specified path.

            - name: The name of the item
            - type: The type of the item (e.g. "item" or "dir")
            - description: A description of the item
            - units: The units of the item (e.g. "m/s" or "C")
        
        For items that are "dir" type, listdir() can be called with the item's
        name to list the items in that directory.  The units field is not
        required for "dir" type items.
        """
        if path == '/':
            return [
                ('server_performance', 'dir',
                 'Various metrics related to the performance of a server cluster'),
                ('harvester_telemetry', 'dir',
                 'Telemetry data from a fleet of agricultural harvester robots'),
            ]
        if path == '/server_performance':
            return [
                ('By Host', 'dir', 'Server load metrics by host'),
                ('By Metric', 'dir', 'Server load metrics by metric'),
            ]
        if path == '/server_performance/By Metric':
            return [
                (metric.name, 'dir', metric.description, metric.units)
                for metric in SERVER_METRICS
            ]
        if path.startswith('/server_performance/By Metric/'):
            return [
                (host.name, 'item', host.description)
                for host in SERVER_HOSTS
            ]
        if path.startswith('/server_performance/By Host/'):
            return [
                (metric.name, 'item', metric.description, metric.units)
                for metric in SERVER_METRICS
            ]

        if path == '/harvester_telemetry':
            return [
                ('TBD', 'dir', 'Telemetry data from a fleet of agricultural harvester robots'),
            ]
        return []
