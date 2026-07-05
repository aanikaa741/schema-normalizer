"""
test_normalizer.py
Unit tests for normalizer.py

Run with: python3 -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from normalizer import (
    Relation, FunctionalDependency,
    check_1nf,
    find_partial_dependencies, decompose_to_2nf,
    find_transitive_dependencies, decompose_to_3nf,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def make_employee():
    """EMPLOYEE with a transitive dependency: DeptID → DeptName, DeptLocation."""
    return Relation(
        name        = "EMPLOYEE",
        attributes  = {"EmployeeID", "Name", "Salary", "DeptID", "DeptName", "DeptLocation"},
        primary_key = {"EmployeeID"},
        fds         = [
            FunctionalDependency({"EmployeeID"}, {"Name", "Salary", "DeptID"}),
            FunctionalDependency({"DeptID"},     {"DeptName", "DeptLocation"}),
        ],
    )


def make_order_items():
    """ORDER_ITEMS with composite key and partial dependencies."""
    return Relation(
        name        = "ORDER_ITEMS",
        attributes  = {"OrderID", "ProductID", "Quantity",
                       "ProductName", "ProductPrice", "CustomerID", "OrderDate"},
        primary_key = {"OrderID", "ProductID"},
        fds         = [
            FunctionalDependency({"OrderID", "ProductID"}, {"Quantity"}),
            FunctionalDependency({"ProductID"}, {"ProductName", "ProductPrice"}),
            FunctionalDependency({"OrderID"},   {"CustomerID", "OrderDate"}),
        ],
    )


def make_clean_relation():
    """A relation already in 3NF — no violations."""
    return Relation(
        name        = "PRODUCT",
        attributes  = {"ProductID", "ProductName", "Price"},
        primary_key = {"ProductID"},
        fds         = [FunctionalDependency({"ProductID"}, {"ProductName", "Price"})],
    )


# ── 1NF tests ────────────────────────────────────────────────────────────────

def test_1nf_passes_with_primary_key():
    rel = make_clean_relation()
    is_1nf, violations = check_1nf(rel)
    assert is_1nf
    assert violations == []


def test_1nf_fails_without_primary_key():
    rel = Relation("BAD", {"A", "B"}, set(), [])
    is_1nf, violations = check_1nf(rel)
    assert not is_1nf
    assert any("primary key" in v.lower() for v in violations)


def test_1nf_detects_duplicate_pk_in_data():
    rel = make_clean_relation()
    data = [
        {"ProductID": 1, "ProductName": "A", "Price": 10},
        {"ProductID": 1, "ProductName": "B", "Price": 20},  # duplicate PK
    ]
    is_1nf, violations = check_1nf(rel, data)
    assert not is_1nf
    assert any("duplicate" in v.lower() for v in violations)


# ── 2NF tests ────────────────────────────────────────────────────────────────

def test_no_partial_deps_on_single_key():
    """Single-attribute primary key → no partial dependencies possible."""
    rel = make_employee()
    partials = find_partial_dependencies(rel)
    assert partials == []


def test_partial_deps_detected_on_composite_key():
    rel = make_order_items()
    partials = find_partial_dependencies(rel)
    # should find at least one partial dependency
    assert len(partials) >= 1
    # all detected determinants should be proper subsets of the PK
    for subset, _ in partials:
        assert subset < rel.primary_key


def test_2nf_decomposition_removes_partial_deps():
    rel = make_order_items()
    decomposed = decompose_to_2nf(rel)
    # must produce more relations than the original
    assert len(decomposed) > 1
    # none of the resulting relations should have partial dependencies
    for r in decomposed:
        assert find_partial_dependencies(r) == [], \
            f"{r.name} still has partial dependencies after 2NF decomposition"


def test_2nf_decomposition_preserves_all_attributes():
    rel = make_order_items()
    decomposed = decompose_to_2nf(rel)
    all_attrs = set()
    for r in decomposed:
        all_attrs |= r.attributes
    assert rel.attributes == all_attrs, \
        "2NF decomposition lost or gained attributes"


def test_clean_relation_unchanged_by_2nf():
    rel = make_clean_relation()
    decomposed = decompose_to_2nf(rel)
    assert len(decomposed) == 1
    assert decomposed[0].name == rel.name


# ── 3NF tests ────────────────────────────────────────────────────────────────

def test_transitive_dep_detected():
    rel = make_employee()
    transitives = find_transitive_dependencies(rel)
    assert len(transitives) >= 1
    # the transitive dependency should be DeptID → {DeptName, DeptLocation}
    dets = [det for det, _ in transitives]
    assert frozenset({"DeptID"}) in dets


def test_no_transitive_deps_on_clean_relation():
    rel = make_clean_relation()
    transitives = find_transitive_dependencies(rel)
    assert transitives == []


def test_3nf_decomposition_removes_transitive_deps():
    rel = make_employee()
    decomposed = decompose_to_3nf(rel)
    assert len(decomposed) > 1
    for r in decomposed:
        assert find_transitive_dependencies(r) == [], \
            f"{r.name} still has transitive dependencies after 3NF decomposition"


def test_3nf_decomposition_preserves_all_attributes():
    rel = make_employee()
    decomposed = decompose_to_3nf(rel)
    all_attrs = set()
    for r in decomposed:
        all_attrs |= r.attributes
    assert rel.attributes == all_attrs, \
        "3NF decomposition lost or gained attributes"


def test_full_pipeline_enrollment():
    """
    End-to-end test: ENROLLMENT has both partial and transitive deps.
    After 2NF then 3NF decomposition, no violations should remain.
    """
    from examples import example_enrollment
    from normalizer import (find_partial_dependencies,
                            find_transitive_dependencies,
                            decompose_to_2nf, decompose_to_3nf)

    fds = [
        FunctionalDependency({"StudentID", "CourseID"}, {"Grade"}),
        FunctionalDependency({"CourseID"},               {"CourseName", "InstructorID"}),
        FunctionalDependency({"InstructorID"},           {"InstructorName", "Office"}),
        FunctionalDependency({"StudentID"},              {"StudentName", "Major"}),
    ]
    rel = Relation(
        name        = "ENROLLMENT",
        attributes  = {"StudentID", "CourseID", "Grade", "CourseName",
                       "InstructorID", "InstructorName", "Office",
                       "StudentName", "Major"},
        primary_key = {"StudentID", "CourseID"},
        fds         = fds,
    )

    after_2nf = decompose_to_2nf(rel)
    final = []
    for r in after_2nf:
        final.extend(decompose_to_3nf(r))

    for r in final:
        assert find_partial_dependencies(r) == [], \
            f"{r.name} still has partial deps"
        assert find_transitive_dependencies(r) == [], \
            f"{r.name} still has transitive deps"


if __name__ == "__main__":
    test_fns = [
        test_1nf_passes_with_primary_key,
        test_1nf_fails_without_primary_key,
        test_1nf_detects_duplicate_pk_in_data,
        test_no_partial_deps_on_single_key,
        test_partial_deps_detected_on_composite_key,
        test_2nf_decomposition_removes_partial_deps,
        test_2nf_decomposition_preserves_all_attributes,
        test_clean_relation_unchanged_by_2nf,
        test_transitive_dep_detected,
        test_no_transitive_deps_on_clean_relation,
        test_3nf_decomposition_removes_transitive_deps,
        test_3nf_decomposition_preserves_all_attributes,
        test_full_pipeline_enrollment,
    ]
    passed = 0
    for fn in test_fns:
        try:
            fn()
            print(f"PASS: {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {fn.__name__} -- {e}")
    print(f"\n{passed}/{len(test_fns)} tests passed")
