# FastBox Mystery Delivery System

Python implementation for the Nexgensis Technologies Pvt. Ltd. Python Developer Assignment Round.

## Overview

This project simulates a warehouse/package delivery system:

1. Reads delivery data from JSON.
2. Assigns each package to the nearest available agent based on the agent's distance to the package's warehouse.
3. Calculates travel distance for each assigned package:
   - Agent -> Warehouse
   - Warehouse -> Package Destination
4. Calculates total distance and efficiency for each agent.
5. Identifies the agent with the lowest efficiency.
6. Produces a JSON report.
7. Can export a top-performer CSV report.
8. Includes automated tests and the 10 supplied assignment test cases with generated outputs.

## Project Structure

```text
FastBox-Mystery-Delivery-System/
├── README.md
├── delivery_system.py
├── test_delivery_system.py
├── base_case.json
├── report.json
├── top_performer.csv
├── requirements.txt
├── .gitignore
├── test_cases/
│   ├── test_case_1.json
│   ├── ...
│   └── test_case_10.json
└── test_outputs/
    ├── test_case_1_report.json
    ├── ...
    └── test_case_10_report.json
```

## Requirements

- Python 3.9+
- No third-party packages are required.

## Run the Program

Run the base case:

```bash
python delivery_system.py base_case.json
```

Generate a report for any supplied test case:

```bash
python delivery_system.py test_cases/test_case_1.json --output report.json
```

Generate a CSV summary as well:

```bash
python delivery_system.py test_cases/test_case_1.json --output report.json --csv top_performer.csv
```

## Run Tests

```bash
python -m unittest -v
```

The automated test suite covers distance calculation, input-format compatibility, nearest-agent assignment, deterministic tie handling, invalid JSON handling, and the supplied test cases.

## Engineering Assumptions

The assignment explicitly asks candidates to document assumptions where behavior is ambiguous. The following assumptions are used:

1. **Agent assignment**
   - Every package is assigned to the agent with the smallest Euclidean distance from that agent's current/base location to the package's warehouse.
   - Assignment is based on the warehouse distance only, as specified by the assignment logic.

2. **Delivery route**
   - For each package, the route distance is:
     `Agent -> Warehouse -> Package Destination`.
   - Packages assigned to the same agent are processed in the order in which they appear in the input JSON.
   - The agent returns to its base location after completing its assigned deliveries only for the purpose of calculating the complete route where applicable; no unnecessary extra travel is added when the assignment specification does not require it.

3. **Tie-breaking**
   - If two or more agents are at exactly the same nearest distance, the agent ID is used as a deterministic tie-breaker.
   - This makes results reproducible across runs.

4. **Efficiency**
   - Efficiency is calculated as:
     `Total Distance / Number of Packages Delivered`.
   - If an agent has delivered zero packages, efficiency is represented as `0.0` to avoid division by zero.

5. **Floating-point values**
   - Euclidean distances are calculated using `math.hypot`.
   - Reported distance and efficiency values are rounded to two decimal places for presentation.

6. **Input compatibility**
   - The implementation accepts both:
     - dictionary-style warehouse/agent collections, and
     - list-style collections with explicit `id` fields.
   - This is useful because the supplied assignment materials contain more than one JSON representation.

7. **Invalid input**
   - Invalid JSON and structurally invalid input raise clear errors rather than silently producing an incorrect report.

## Validation

All 10 supplied test-case input files are included in `test_cases/`.

The corresponding generated reports are included in `test_outputs/`, allowing the reviewer to inspect the input/output behavior directly.

## Output

A report contains:

- `agent_id`
- `packages_delivered`
- `total_distance`
- `efficiency`
- `best_agent`

The CSV export contains a compact agent-level summary.

## Notes

The implementation is intentionally data-driven and does not hard-code warehouse IDs, agent IDs, package IDs, or the number of records.
