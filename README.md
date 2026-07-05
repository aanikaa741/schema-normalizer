# Schema Normalizer: 1NF → 3NF Step Tracer

A Python tool that takes an unnormalized relational schema, detects functional dependency violations, and traces the decomposition from **1NF through 2NF to 3NF** — printing the reasoning at each step the way a textbook or instructor would.

## What it does

Given a relation schema and its functional dependencies, the tracer:

1. **Checks 1NF** — verifies a primary key exists and data is atomic
2. **Checks 2NF** — detects partial dependencies (non-key attributes depending on only part of a composite key) and decomposes to remove them
3. **Checks 3NF** — detects transitive dependencies (key → X → Y, where X is not a key) and decomposes to remove them
4. **Prints the final normalized schema** with all decomposed relations and a summary of the guarantees achieved

## Example output

Running the EMPLOYEE example (transitive dependency: `EmployeeID → DeptID → DeptName, DeptLocation`):

```
════════════════════════════════════════════════════════════
  NORMALIZATION TRACE: EMPLOYEE
════════════════════════════════════════════════════════════

  STEP 2 — Check 2NF
  ✓ Primary key {EmployeeID} is a single attribute.
    Single-attribute keys cannot have partial dependencies.
    EMPLOYEE is automatically in 2NF.

  STEP 3 — Check 3NF
  ✗ EMPLOYEE: transitive dependencies detected:
    {DeptID} → {DeptLocation, DeptName}
    Because {DeptLocation, DeptName} depends on {DeptID}, not directly
    on the primary key {EmployeeID}.

  → Decomposing EMPLOYEE...

  FINAL NORMALIZED SCHEMA (3NF)
  • EMPLOYEE_DeptID  — PK: {DeptID}, non-key: {DeptLocation, DeptName}
  • EMPLOYEE         — PK: {EmployeeID}, non-key: {DeptID, Name, Salary}
```

## Three worked examples

| Example | Schema | Violation |
|---|---|---|
| `ORDER_ITEMS` | E-commerce orders | Partial dependency (2NF) |
| `EMPLOYEE` | Staff + department info | Transitive dependency (3NF) |
| `ENROLLMENT` | University course enrollment | Both partial and transitive |

## Project structure

```
schema-normalizer/
├── src/
│   ├── normalizer.py   # core FD detection and decomposition engine
│   ├── tracer.py       # step-by-step trace printer
│   └── examples.py     # three worked example schemas
├── tests/
│   └── test_normalizer.py  # 13 unit tests
└── README.md
```

## Setup & usage

```bash
# no dependencies beyond Python 3 standard library
python3 src/examples.py          # run all three worked examples
python3 -m pytest tests/ -v      # run the test suite
```

To define your own schema:

```python
from normalizer import Relation, FunctionalDependency
from tracer import trace_normalization

fds = [
    FunctionalDependency({"StudentID", "CourseID"}, {"Grade"}),
    FunctionalDependency({"CourseID"}, {"CourseName"}),
]
rel = Relation(
    name        = "MY_RELATION",
    attributes  = {"StudentID", "CourseID", "Grade", "CourseName"},
    primary_key = {"StudentID", "CourseID"},
    fds         = fds,
)
trace_normalization(rel)
```

## Why it matters

Database normalization is one of the most error-prone topics in introductory database courses — students understand the definitions but consistently struggle to apply them to real schemas. This tool makes each step explicit and inspectable, showing not just *what* the final decomposition is but *why* each attribute moved.

## License
MIT
