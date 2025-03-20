# CFD-Miner

A Python implementation of Conditional Functional Dependency (CFD) mining algorithm for data quality analysis. This project focuses on discovering CFDs from datasets.

## Overview

Conditional Functional Dependencies (CFDs) are an extension of traditional functional dependencies that include pattern tableaux, allowing for data quality rules that hold on a subset of tuples. This implementation uses a tree-based approach to efficiently mine CFDs from data.

## Features

- Tree-based CFD mining algorithm
- Support for both constant and variable patterns
- Configurable support and confidence thresholds
- Optimized for large datasets
- Automatic enumeration column detection

## Installation
1. Python
2. Pandas

## Usage

The main function to use is `check_error_cfd(req_json)`, which accepts a JSON request containing:

```python
{
    "data_path": "path/to/input/data.csv",
    "output_path": "path/to/output/results"
}
```

### Parameters

- `data_path`: Path to the input CSV data file
- `output_path`: Path where results will be saved
- `enum_k`: Maximum number of distinct values for enumerated columns
- `support`: Minimum support threshold for rules
- `confidence`: Minimum confidence threshold for rules
- `tree_level`: Maximum number of predicates in rules

Note: While `data_path` and `output_path` are specified in the request, other parameters (`enum_k`, `support`, `confidence`, `tree_level`) are configured in the code.

## Algorithm Description

The CFD mining process follows these steps:

1. Load and parse input parameters
2. Identify enumeration columns based on `enum_k` parameter
3. Construct tuple patterns and constant patterns
4. Build a computation tree for each tuple pattern as root node (as Y in rules)
5. Traverse the tree using BFS:
   - Each node represents a potential rule
   - Calculate support and confidence for each node
   - If thresholds are met, save the rule and prune child nodes
6. For nodes meeting support but not confidence:
   - Add constant patterns and recalculate metrics
   - Save rules that meet thresholds after modification
7. Prune subtrees of nodes not meeting support threshold
8. Output discovered rules

## Data Format

The input data should be a CSV file with a header row. The algorithm automatically processes the data to identify potential CFDs based on the configured parameters.

## Example

For a hospital dataset, the miner might discover rules such as:
- t0.emergency_service=t1.emergency_service->t0.state=t1.state
- t0.state=t1.state^t0.owner='voluntary non-profit - church'^t1.owner='voluntary non-profit - church'->t0.emergency_service=t1.emergency_service
