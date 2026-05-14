import csv
import json
import argparse
import os
from datetime import datetime

# =========================================================
# CUSTOM EXCEPTIONS
# =========================================================

class DeploymentFailureError(Exception):
    pass


class MonitoringAgentError(Exception):
    pass


class InfrastructureAlertError(Exception):
    pass


# =========================================================
# SERVER CLASS
# =========================================================

class Server:

    def __init__(
        self,
        server_id,
        name,
        total_cpu,
        used_cpu,
        uptime,
        response_time,
        authorized=True
    ):

        self.server_id = server_id
        self.name = name
        self.total_cpu = total_cpu
        self.used_cpu = used_cpu
        self.uptime = uptime
        self.response_time = response_time
        self.authorized = authorized

    # CPU Formula
    def cpu_usage(self):

        if self.used_cpu < 0:
            raise ValueError(
                f"Negative CPU usage detected in {self.server_id}"
            )

        return (self.used_cpu / self.total_cpu) * 100

    def resource_optimization_score(self):

        usage = self.cpu_usage()

        if usage <= 70:
            return 100

        elif usage <= 85:
            return 80

        else:
            return 50


# =========================================================
# CONTAINER CLASS
# =========================================================

class Container:

    def __init__(
        self,
        container_id,
        name,
        status,
        logs_present
    ):

        self.container_id = container_id
        self.name = name
        self.status = status
        self.logs_present = logs_present

    def is_crashed(self):

        return self.status.upper() == "CRASHED"


# =========================================================
# DEPLOYMENT PIPELINE CLASS
# =========================================================

class DeploymentPipeline:

    VALID_STATUS = ["SUCCESS", "FAILED", "RUNNING"]

    def __init__(
        self,
        deployment_id,
        server_id,
        status
    ):

        self.deployment_id = deployment_id
        self.server_id = server_id
        self.status = status

    def validate_status(self):

        if self.status not in self.VALID_STATUS:

            raise DeploymentFailureError(
                f"Invalid deployment status: {self.status}"
            )


# =========================================================
# ALERT MANAGER
# =========================================================

class AlertManager:

    def __init__(self):

        self.alerts = []

    def create_alert(self, message):

        timestamp = datetime.now()

        alert_message = (
            f"[{timestamp}] ALERT: {message}"
        )

        self.alerts.append(alert_message)

        print(alert_message)

    def save_alerts(self):

        with open("alerts.json", "w") as file:

            json.dump(self.alerts, file, indent=4)


# =========================================================
# AUTO SCALER
# =========================================================

class AutoScaler:

    def scale_server(self, server):

        usage = server.cpu_usage()

        if usage > 85:

            print(
                f"Scaling UP resources for {server.name}"
            )

        elif usage < 30:

            print(
                f"Scaling DOWN resources for {server.name}"
            )

        else:

            print(
                f"No scaling required for {server.name}"
            )


# =========================================================
# MONITORING DASHBOARD
# =========================================================

class MonitoringDashboard:

    def __init__(self):

        self.servers = []
        self.containers = []
        self.deployments = []

        self.alert_manager = AlertManager()
        self.auto_scaler = AutoScaler()

    # =====================================================
    # LOAD SERVERS
    # =====================================================

    def load_servers(self, filename):

        seen_ids = set()

        with open(filename, "r") as file:

            data = json.load(file)

            for row in data:

                # Duplicate Server ID Check
                if row["server_id"] in seen_ids:

                    raise ValueError(
                        f"Duplicate Server ID: "
                        f"{row['server_id']}"
                    )

                seen_ids.add(row["server_id"])

                server = Server(
                    row["server_id"],
                    row["name"],
                    row["total_cpu"],
                    row["used_cpu"],
                    row["uptime"],
                    row["response_time"],
                    row["authorized"]
                )

                self.servers.append(server)

    # =====================================================
    # LOAD CONTAINERS
    # =====================================================

    def load_containers(self, filename):

        with open(filename, "r") as file:

            reader = csv.DictReader(file)

            for row in reader:

                # Missing Logs Validation
                if row["logs_present"] == "":

                    raise MonitoringAgentError(
                        f"Missing logs for container "
                        f"{row['container_id']}"
                    )

                container = Container(
                    row["container_id"],
                    row["name"],
                    row["status"],
                    row["logs_present"]
                )

                self.containers.append(container)

    # =====================================================
    # LOAD DEPLOYMENTS
    # =====================================================

    def load_deployments(self, filename):

        with open(filename, "r") as file:

            reader = csv.DictReader(file)

            for row in reader:

                deployment = DeploymentPipeline(
                    row["deployment_id"],
                    row["server_id"],
                    row["status"]
                )

                deployment.validate_status()

                self.deployments.append(deployment)

    # =====================================================
    # DETECT ANOMALIES
    # =====================================================

    def detect_anomalies(self):

        deployment_failures = {}

        # -------------------------------
        # SERVER CHECKS
        # -------------------------------

        for server in self.servers:

            usage = server.cpu_usage()

            # Server Downtime
            if server.uptime < 90:

                self.alert_manager.create_alert(
                    f"Server downtime detected: "
                    f"{server.name}"
                )

            # High CPU Usage
            if usage > 90:

                self.alert_manager.create_alert(
                    f"High CPU usage detected "
                    f"in {server.name}"
                )

            # Unauthorized Access
            if not server.authorized:

                self.alert_manager.create_alert(
                    f"Unauthorized access detected "
                    f"in {server.name}"
                )

            # Auto Scaling
            self.auto_scaler.scale_server(server)

        # -------------------------------
        # DEPLOYMENT FAILURES
        # -------------------------------

        for deployment in self.deployments:

            if deployment.status == "FAILED":

                deployment_failures.setdefault(
                    deployment.server_id,
                    0
                )

                deployment_failures[
                    deployment.server_id
                ] += 1

        for server_id, count in deployment_failures.items():

            if count >= 3:

                self.alert_manager.create_alert(
                    f"Repeated deployment failures "
                    f"in {server_id}"
                )

        # -------------------------------
        # CONTAINER CRASHES
        # -------------------------------

        for container in self.containers:

            if container.is_crashed():

                self.alert_manager.create_alert(
                    f"Container crash loop detected: "
                    f"{container.name}"
                )

    # =====================================================
    # DEPLOYMENT SUCCESS RATE
    # =====================================================

    def calculate_deployment_success_rate(
        self,
        server_id
    ):

        total = 0
        success = 0

        for deployment in self.deployments:

            if deployment.server_id == server_id:

                total += 1

                if deployment.status == "SUCCESS":

                    success += 1

        if total == 0:
            return 0

        return (success / total) * 100

    # =====================================================
    # SERVER RANKING
    # =====================================================

    def rank_servers(self):

        ranking = []

        for server in self.servers:

            deployment_score = (
                self.calculate_deployment_success_rate(
                    server.server_id
                )
            )

            optimization_score = (
                server.resource_optimization_score()
            )

            final_score = (
                (server.uptime * 0.4)
                +
                (deployment_score * 0.3)
                +
                (optimization_score * 0.2)
                +
                ((100 - server.response_time) * 0.1)
            )

            ranking.append(
                (
                    server.name,
                    round(final_score, 2)
                )
            )

        ranking.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return ranking

    # =====================================================
    # RECURSION
    # =====================================================

    def dependency_traversal(
        self,
        dependencies,
        node,
        visited=None
    ):

        if visited is None:

            visited = set()

        visited.add(node)

        print(node)

        for neighbor in dependencies.get(node, []):

            if neighbor not in visited:

                self.dependency_traversal(
                    dependencies,
                    neighbor,
                    visited
                )

    # =====================================================
    # REPORT GENERATION
    # =====================================================

    def generate_reports(self):

        # Create reports folder automatically
        os.makedirs("reports", exist_ok=True)

        # -----------------------------------------
        # DEPLOYMENT REPORT
        # -----------------------------------------

        with open(
            "reports/deployment_report.txt",
            "w"
        ) as file:

            file.write(
                "===== DEPLOYMENT REPORT =====\n\n"
            )

            for deployment in self.deployments:

                file.write(
                    f"{deployment.deployment_id} "
                    f"- {deployment.status}\n"
                )

        # -----------------------------------------
        # UPTIME REPORT
        # -----------------------------------------

        with open(
            "reports/uptime_report.txt",
            "w"
        ) as file:

            file.write(
                "===== SERVER UPTIME REPORT =====\n\n"
            )

            for server in self.servers:

                file.write(
                    f"{server.name} "
                    f"-> {server.uptime}% uptime\n"
                )

        # -----------------------------------------
        # FAILED CONTAINER REPORT
        # -----------------------------------------

        with open(
            "reports/failed_containers.txt",
            "w"
        ) as file:

            file.write(
                "===== FAILED CONTAINERS =====\n\n"
            )

            for container in self.containers:

                if container.is_crashed():

                    file.write(
                        f"{container.name}\n"
                    )

        # -----------------------------------------
        # RESOURCE REPORT
        # -----------------------------------------

        with open(
            "reports/resource_report.txt",
            "w"
        ) as file:

            file.write(
                "===== RESOURCE UTILIZATION =====\n\n"
            )

            for server in self.servers:

                file.write(
                    f"{server.name} "
                    f"-> CPU Usage: "
                    f"{round(server.cpu_usage(), 2)}%\n"
                )

        # -----------------------------------------
        # SECURITY REPORT
        # -----------------------------------------

        with open(
            "reports/security_report.txt",
            "w"
        ) as file:

            file.write(
                "===== SECURITY ALERT SUMMARY =====\n\n"
            )

            for server in self.servers:

                if not server.authorized:

                    file.write(
                        f"Unauthorized Access: "
                        f"{server.name}\n"
                    )

        print("\nReports Generated Successfully")

# =========================================================
# MAIN FUNCTION
# =========================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--environment",
        type=str,
        required=True,
        help="Enter environment name"
    )

    args = parser.parse_args()

    print(
        f"\nMonitoring Environment: "
        f"{args.environment}\n"
    )

    dashboard = MonitoringDashboard()

    # =====================================================
    # LOAD DATA FILES
    # =====================================================

    dashboard.load_servers("servers.json")

    dashboard.load_containers("containers.csv")

    dashboard.load_deployments("deployments.csv")

    # =====================================================
    # DETECT ANOMALIES
    # =====================================================

    dashboard.detect_anomalies()

    # =====================================================
    # SERVER RANKING
    # =====================================================

    print("\n===== SERVER RANKING =====\n")

    rankings = dashboard.rank_servers()

    for rank, server in enumerate(rankings, start=1):

        print(
            f"{rank}. "
            f"{server[0]} "
            f"-> Score: {server[1]}"
        )

    # =====================================================
    # RECURSION DEMO
    # =====================================================

    print("\n===== DEPENDENCY TRAVERSAL =====\n")

    dependencies = {

        "LoadBalancer": [
            "WebServer1",
            "WebServer2"
        ],

        "WebServer1": [
            "Database"
        ],

        "WebServer2": [
            "Cache"
        ],

        "Database": [],

        "Cache": []
    }

    dashboard.dependency_traversal(
        dependencies,
        "LoadBalancer"
    )

    # =====================================================
    # REPORTS
    # =====================================================

    dashboard.generate_reports()

    # =====================================================
    # SAVE ALERTS
    # =====================================================

    dashboard.alert_manager.save_alerts()

    print("\nAlerts saved to alerts.json")


# =========================================================
# PROGRAM START
# =========================================================

if __name__ == "__main__":

    main()