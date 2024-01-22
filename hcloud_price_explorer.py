from prometheus_client import CollectorRegistry, Gauge, write_to_textfile
import requests

# Define your environments and their corresponding API keys
environments = [
    {"env": "nbg", "job_id": "hcloud_price_explorer", "hcloud_auth": "Bearer CHANGEME"},
    {"env": "fsn", "job_id": "hcloud_price_explorer", "hcloud_auth": "Bearer CHANGEME"},
    # Add more environments as needed
]

# Create a Prometheus registry
REGISTRY = CollectorRegistry()

# Define Prometheus metrics
monthly_price_metric = Gauge("hcloud_monthly_price", "Monthly price of Hetzner Cloud servers", ["env", "job_id", "name", "description", "dc"], registry=REGISTRY)

for environment in environments:
    env = environment["env"]
    job_id = environment["job_id"]
    hcloud_auth = environment["hcloud_auth"]

    headers = {"Authorization": f"{hcloud_auth}"}

    page = 1
    while True:
        response = requests.get(f"https://api.hetzner.cloud/v1/servers?per_page=50&page={page}", headers=headers)
        result = response.json()

        try:
            servers = result["servers"]
        except KeyError:
            break

        for server in servers:
            name = server["name"]
            description = server["server_type"]["description"]
            monthly_price = float(server["server_type"]["prices"][0]["price_monthly"]["gross"])
            monthly_price = round(monthly_price, 2)

            # Rename datacenter_name to dc
            dc = server.get("datacenter", {}).get("name", "")

            # Set Prometheus metric
            monthly_price_metric.labels(env=env, job_id=job_id, name=name, description=description, dc=dc).set(monthly_price)

        if result["meta"]["pagination"]["next_page"] is None:
            break
        else:
            page = result["meta"]["pagination"]["next_page"]

# Write metrics to a text file
write_to_textfile("/opt/node_exporter/hcloud_price.prom", REGISTRY)
