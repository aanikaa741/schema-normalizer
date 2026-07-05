"""
tracer.py
Prints a human-readable, step-by-step normalization trace:
  original schema → 1NF check → 2NF decomposition → 3NF decomposition

This is the "teaching tool" layer on top of the normalizer engine.
Each step explains WHY a violation exists and WHAT is done to fix it,
mirroring how a textbook or instructor would walk through the problem.
"""

from normalizer import (
    Relation, FunctionalDependency,
    check_1nf,
    find_partial_dependencies, decompose_to_2nf,
    find_transitive_dependencies, decompose_to_3nf,
)

DIVIDER = "─" * 60


def _attrs(s):
    return "{" + ", ".join(sorted(s)) + "}"


def _print_relation(rel, indent=2):
    pad = " " * indent
    print(f"{pad}Relation : {rel.name}")
    print(f"{pad}Attributes: {_attrs(rel.attributes)}")
    print(f"{pad}Primary key: {_attrs(rel.primary_key)}")
    if rel.fds:
        print(f"{pad}Functional dependencies:")
        for fd in rel.fds:
            print(f"{pad}  {fd}")


def trace_normalization(relation, sample_data=None):
    """
    Run and print the full normalization trace for a given relation.

    Args:
        relation:    a Relation object (the starting unnormalized schema)
        sample_data: optional list of dicts (row samples) for 1NF data check
    """
    print(f"\n{'═' * 60}")
    print(f"  NORMALIZATION TRACE: {relation.name}")
    print(f"{'═' * 60}")

    # ── Original schema ───────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  ORIGINAL SCHEMA")
    print(DIVIDER)
    _print_relation(relation)

    if sample_data:
        print("\n  Sample data:")
        headers = sorted(relation.attributes)
        header_line = "  " + "  |  ".join(f"{h:15}" for h in headers)
        print(header_line)
        print("  " + "-" * (len(header_line) - 2))
        for row in sample_data:
            print("  " + "  |  ".join(f"{str(row.get(h, '')):<15}" for h in headers))

    # ── 1NF ──────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  STEP 1 — Check 1NF (First Normal Form)")
    print(DIVIDER)
    print("  1NF requires:")
    print("    • A defined primary key")
    print("    • All attributes are atomic (no lists or sets inside a cell)")
    print("    • No duplicate rows")

    is_1nf, violations_1nf = check_1nf(relation, sample_data)

    if is_1nf:
        print(f"\n  ✓ {relation.name} is in 1NF — primary key is defined and attributes are atomic.")
    else:
        print(f"\n  ✗ {relation.name} violates 1NF:")
        for v in violations_1nf:
            print(f"    - {v}")
        print("\n  → Fix: define a primary key and ensure all values are atomic.")
        print("    (Halting trace — resolve 1NF before proceeding.)")
        return

    # ── 2NF ──────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  STEP 2 — Check 2NF (Second Normal Form)")
    print(DIVIDER)
    print("  2NF requires: in 1NF AND no partial dependencies.")
    print("  A partial dependency: a non-key attribute depends on only")
    print("  PART of a composite primary key (not the whole key).")

    if len(relation.primary_key) <= 1:
        print(f"\n  ✓ Primary key {_attrs(relation.primary_key)} is a single attribute.")
        print("    Single-attribute keys cannot have partial dependencies.")
        print(f"    {relation.name} is automatically in 2NF.")
        relations_after_2nf = [relation]
    else:
        partials = find_partial_dependencies(relation)

        if not partials:
            print(f"\n  ✓ No partial dependencies found — {relation.name} is in 2NF.")
            relations_after_2nf = [relation]
        else:
            print(f"\n  ✗ Partial dependencies detected:")
            for subset, deps in partials:
                print(f"    {_attrs(subset)} → {_attrs(deps)}")
                print(f"    Because {_attrs(deps)} depends on only part of the key "
                      f"{_attrs(relation.primary_key)}.")

            print(f"\n  → Decomposing {relation.name} to remove partial dependencies...")
            relations_after_2nf = decompose_to_2nf(relation)

            print(f"\n  Result — {len(relations_after_2nf)} relation(s) after 2NF decomposition:")
            for rel in relations_after_2nf:
                print()
                _print_relation(rel)

    # ── 3NF ──────────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  STEP 3 — Check 3NF (Third Normal Form)")
    print(DIVIDER)
    print("  3NF requires: in 2NF AND no transitive dependencies.")
    print("  A transitive dependency: key → X → Y, where X is not a key.")
    print("  This means Y depends on the key only indirectly, through X.")

    final_relations = []
    any_transitive  = False

    for rel in relations_after_2nf:
        transitives = find_transitive_dependencies(rel)

        if not transitives:
            print(f"\n  ✓ {rel.name}: no transitive dependencies — already in 3NF.")
            final_relations.append(rel)
        else:
            any_transitive = True
            print(f"\n  ✗ {rel.name}: transitive dependencies detected:")
            for det, dep in transitives:
                print(f"    {_attrs(det)} → {_attrs(dep)}")
                print(f"    Because {_attrs(dep)} depends on {_attrs(det)}, not directly")
                print(f"    on the primary key {_attrs(rel.primary_key)}.")

            print(f"\n  → Decomposing {rel.name} to remove transitive dependencies...")
            decomposed = decompose_to_3nf(rel)
            final_relations.extend(decomposed)

            print(f"\n  Result — {len(decomposed)} relation(s) after 3NF decomposition:")
            for r in decomposed:
                print()
                _print_relation(r)

    if not any_transitive:
        print("\n  All relations are already in 3NF.")

    # ── Final schema ──────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print("  FINAL NORMALIZED SCHEMA (3NF)")
    print(DIVIDER)
    print(f"  Original relation '{relation.name}' decomposed into "
          f"{len(final_relations)} relation(s):\n")
    for rel in final_relations:
        pk   = _attrs(rel.primary_key)
        rest = _attrs(rel.attributes - rel.primary_key)
        rest_str = f", non-key: {rest}" if rel.attributes - rel.primary_key else ""
        print(f"  • {rel.name}")
        print(f"    PK: {pk}{rest_str}")
    print()
    print("  Properties of the decomposition:")
    print("  ✓ Lossless join  — original data can be reconstructed by joining on shared keys")
    print("  ✓ No partial dependencies  — every non-key attribute depends on the whole key")
    print("  ✓ No transitive dependencies  — every non-key attribute depends directly on the key")
    print(f"\n{'═' * 60}\n")

    return final_relations
