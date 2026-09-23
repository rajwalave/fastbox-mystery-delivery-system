"""FastBox Mystery Delivery System.

Reads a delivery scenario from JSON, assigns each package to the nearest agent,
simulates deliveries, and writes a JSON performance report.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any



def euclidean_distance(point_a: list[float] | tuple[float, float], point_b: list[float] | tuple[float, float]) -> float:
    """Return the Euclidean distance between two 2-D points."""
    if len(point_a) != 2 or len(point_b) != 2:
        raise ValueError("Locations must contain exactly two coordinates.")
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])



def _normalise_locations(raw: Any, item_name: str) -> dict[str, tuple[float, float]]:
    """Support both dictionary and list-of-objects location formats."""
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = []
        for item in raw:
            if not isinstance(item, dict) or "id" not in item or "location" not in item:
                raise ValueError(f"Each {item_name} must contain 'id' and 'location'.")
            items.append((item["id"], item["location"]))
    else:
        raise ValueError(f"'{item_name}' must be a JSON object or list.")

    locations: dict[str, tuple[float, float]] = {}
    for identifier, location in items:
        if not isinstance(identifier, str):
            raise ValueError(f"{item_name} IDs must be strings.")
        if not isinstance(location, (list, tuple)) or len(location) != 2:
            raise ValueError(f"Location for {identifier} must contain two coordinates.")
        try:
            locations[identifier] = (float(location[0]), float(location[1]))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Location for {identifier} contains non-numeric coordinates.") from exc
    return locations



def _normalise_packages(raw: Any) -> list[dict[str, Any]]:
    """Validate and normalise package records."""
    if not isinstance(raw, list):
        raise ValueError("'packages' must be a JSON array.")

    packages: list[dict[str, Any]] = []
    for package in raw:
        if not isinstance(package, dict):
            raise ValueError("Each package must be a JSON object.")

        warehouse_id = package.get("warehouse_id", package.get("warehouse"))
        package_id = package.get("id")
        destination = package.get("destination")

        if not package_id or not warehouse_id:
            raise ValueError("Each package requires 'id' and a warehouse/warehouse_id.")
        if not isinstance(destination, (list, tuple)) or len(destination) != 2:
            raise ValueError(f"Destination for package {package_id} must contain two coordinates.")

        try:
            destination_tuple = (float(destination[0]), float(destination[1]))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Destination for package {package_id} contains non-numeric coordinates.") from exc

        packages.append(
            {
                "id": str(package_id),
                "warehouse_id": str(warehouse_id),
                "destination": destination_tuple,
            }
        )
    return packages



def load_data(input_path: str | Path) -> tuple[dict[str, tuple[float, float]], dict[str, tuple[float, float]], list[dict[str, Any]]]:
    """Load and validate warehouses, agents, and packages from a JSON file."""
    path = Path(input_path)
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Input file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("The root JSON value must be an object.")

    warehouses = _normalise_locations(data.get("warehouses"), "warehouses")
    agents = _normalise_locations(data.get("agents"), "agents")
    packages = _normalise_packages(data.get("packages"))

    if not warehouses:
        raise ValueError("At least one warehouse is required.")
    if not agents:
        raise ValueError("At least one agent is required.")

    for package in packages:
        if package["warehouse_id"] not in warehouses:
            raise ValueError(
                f"Package {package['id']} references unknown warehouse "
                f"{package['warehouse_id']}."
            )

    return warehouses, agents, packages



def assign_packages(
    warehouses: dict[str, tuple[float, float]],
    agents: dict[str, tuple[float, float]],
    packages: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Assign every package to the nearest agent using agent-to-warehouse distance.

    The assignment uses the agents' starting locations, exactly as specified by
    the task. Ties are resolved by agent ID for deterministic output.
    """
    assignments = {agent_id: [] for agent_id in agents}

    for package in packages:
        warehouse = warehouses[package["warehouse_id"]]
        nearest_agent = min(
            agents,
            key=lambda agent_id: (
                euclidean_distance(agents[agent_id], warehouse),
                agent_id,
            ),
        )
        assignments[nearest_agent].append(package)

    return assignments



def simulate_deliveries(
    warehouses: dict[str, tuple[float, float]],
    agents: dict[str, tuple[float, float]],
    assignments: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    """Simulate each agent's assigned packages in input order.

    For every package the agent travels from their current location to the
    package warehouse, then from the warehouse to the destination. After
    delivery, the agent's current location becomes that destination.
    """
    results: dict[str, dict[str, Any]] = {}

    for agent_id, assigned_packages in assignments.items():
        current_location = agents[agent_id]
        total_distance = 0.0
        deliveries = []

        for package in assigned_packages:
            warehouse_location = warehouses[package["warehouse_id"]]
            destination = package["destination"]

            pickup_distance = euclidean_distance(current_location, warehouse_location)
            delivery_distance = euclidean_distance(warehouse_location, destination)
            package_distance = pickup_distance + delivery_distance
            total_distance += package_distance

            deliveries.append(
                {
                    "package_id": package["id"],
                    "warehouse_id": package["warehouse_id"],
                    "pickup_distance": round(pickup_distance, 2),
                    "delivery_distance": round(delivery_distance, 2),
                    "total_distance": round(package_distance, 2),
                }
            )

            current_location = destination

        package_count = len(assigned_packages)
        efficiency = total_distance / package_count if package_count else 0.0

        results[agent_id] = {
            "packages_delivered": package_count,
            "total_distance": round(total_distance, 2),
            "efficiency": round(efficiency, 2),
            "deliveries": deliveries,
        }

    return results



def build_report(
    warehouses: dict[str, tuple[float, float]],
    agents: dict[str, tuple[float, float]],
    packages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the final report from an input scenario."""
    assignments = assign_packages(warehouses, agents, packages)
    simulation = simulate_deliveries(warehouses, agents, assignments)

    # Agents with no deliveries are excluded from best-agent selection because
    # an efficiency of zero would otherwise incorrectly make them the winner.
    active_agents = [agent_id for agent_id, data in simulation.items() if data["packages_delivered"] > 0]
    best_agent = min(
        active_agents,
        key=lambda agent_id: (simulation[agent_id]["efficiency"], agent_id),
    ) if active_agents else None

    report: dict[str, Any] = {}
    for agent_id, data in simulation.items():
        report[agent_id] = {
            "packages_delivered": data["packages_delivered"],
            "total_distance": data["total_distance"],
            "efficiency": data["efficiency"],
            "deliveries": data["deliveries"],
        }
    report["best_agent"] = best_agent
    report["summary"] = {
        "total_packages": len(packages),
        "packages_delivered": sum(data["packages_delivered"] for data in simulation.values()),
        "all_packages_delivered": sum(data["packages_delivered"] for data in simulation.values()) == len(packages),
    }
    return report



def save_report(report: dict[str, Any], output_path: str | Path) -> None:
    """Save the report as formatted JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)
        file.write("\n")



def save_top_performer_csv(report: dict[str, Any], output_path: str | Path) -> None:
    """Export the top-performing agent and key metrics to CSV."""
    best_agent = report.get("best_agent")
    if best_agent is None:
        return

    best_data = report[best_agent]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["agent_id", "packages_delivered", "total_distance", "efficiency"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "agent_id": best_agent,
                "packages_delivered": best_data["packages_delivered"],
                "total_distance": best_data["total_distance"],
                "efficiency": best_data["efficiency"],
            }
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="FastBox Mystery Delivery System")
    parser.add_argument("input", nargs="?", default="base_case.json", help="Path to input JSON")
    parser.add_argument("-o", "--output", default="report.json", help="Path for generated report JSON")
    parser.add_argument("--top-performer-csv", help="Optional CSV path for the top performer")
    args = parser.parse_args()

    warehouses, agents, packages = load_data(args.input)
    report = build_report(warehouses, agents, packages)
    save_report(report, args.output)
    if args.top_performer_csv:
        save_top_performer_csv(report, args.top_performer_csv)

    print(f"Processed {len(packages)} packages across {len(agents)} agents.")
    print(f"Best agent: {report['best_agent']}")
    print(f"Report saved to: {args.output}")


if __name__ == "__main__":
    main()
