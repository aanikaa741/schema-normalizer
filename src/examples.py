"""
examples.py
Three worked example schemas covering different normalization scenarios:

  Example 1 — ORDER_ITEMS: composite key, has partial dependencies (2NF violation)
  Example 2 — EMPLOYEE:   single key, has transitive dependencies (3NF violation)
  Example 3 — ENROLLMENT: composite key, has both partial and transitive dependencies

"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from normalizer import Relation, FunctionalDependency
from tracer import trace_normalization


# ── Example 1: ORDER_ITEMS ────────────────────────────────────────────────────
# Classic e-commerce order table. Composite key: (OrderID, ProductID)
# Partial dependency: ProductID → ProductName, ProductPrice
#   (product info depends on ProductID alone, not the full composite key)

def example_order_items():
    fds = [
        FunctionalDependency({"OrderID", "ProductID"}, {"Quantity"}),
        FunctionalDependency({"ProductID"}, {"ProductName", "ProductPrice"}),
        FunctionalDependency({"OrderID"},   {"CustomerID", "OrderDate"}),
    ]
    relation = Relation(
        name        = "ORDER_ITEMS",
        attributes  = {"OrderID", "ProductID", "Quantity",
                       "ProductName", "ProductPrice",
                       "CustomerID", "OrderDate"},
        primary_key = {"OrderID", "ProductID"},
        fds         = fds,
    )
    sample_data = [
        {"OrderID": 1, "ProductID": 101, "Quantity": 2,
         "ProductName": "Laptop",  "ProductPrice": 999.99,
         "CustomerID": "C01", "OrderDate": "2024-01-15"},
        {"OrderID": 1, "ProductID": 102, "Quantity": 1,
         "ProductName": "Mouse",   "ProductPrice": 29.99,
         "CustomerID": "C01", "OrderDate": "2024-01-15"},
        {"OrderID": 2, "ProductID": 101, "Quantity": 1,
         "ProductName": "Laptop",  "ProductPrice": 999.99,
         "CustomerID": "C02", "OrderDate": "2024-01-16"},
    ]
    trace_normalization(relation, sample_data)


# ── Example 2: EMPLOYEE ───────────────────────────────────────────────────────
# Employee table with a single primary key (EmployeeID).
# No partial dependencies (single key) but has a transitive dependency:
#   EmployeeID → DeptID → DeptName, DeptLocation
#   (department info depends on DeptID, not directly on EmployeeID)

def example_employee():
    fds = [
        FunctionalDependency({"EmployeeID"}, {"Name", "Salary", "DeptID"}),
        FunctionalDependency({"DeptID"},     {"DeptName", "DeptLocation"}),
    ]
    relation = Relation(
        name        = "EMPLOYEE",
        attributes  = {"EmployeeID", "Name", "Salary",
                       "DeptID", "DeptName", "DeptLocation"},
        primary_key = {"EmployeeID"},
        fds         = fds,
    )
    sample_data = [
        {"EmployeeID": "E01", "Name": "Alice",   "Salary": 90000,
         "DeptID": "D1", "DeptName": "Engineering", "DeptLocation": "Orlando"},
        {"EmployeeID": "E02", "Name": "Bob",     "Salary": 75000,
         "DeptID": "D1", "DeptName": "Engineering", "DeptLocation": "Orlando"},
        {"EmployeeID": "E03", "Name": "Carol",   "Salary": 85000,
         "DeptID": "D2", "DeptName": "Marketing",   "DeptLocation": "Tampa"},
    ]
    trace_normalization(relation, sample_data)


# ── Example 3: ENROLLMENT ─────────────────────────────────────────────────────
# University enrollment table. Composite key: (StudentID, CourseID)
# Partial dependency: CourseID → CourseName, InstructorID
# Transitive dependency: InstructorID → InstructorName, Office
# This example requires BOTH 2NF and 3NF decomposition steps.

def example_enrollment():
    fds = [
        FunctionalDependency({"StudentID", "CourseID"}, {"Grade"}),
        FunctionalDependency({"CourseID"},               {"CourseName", "InstructorID"}),
        FunctionalDependency({"InstructorID"},           {"InstructorName", "Office"}),
        FunctionalDependency({"StudentID"},              {"StudentName", "Major"}),
    ]
    relation = Relation(
        name        = "ENROLLMENT",
        attributes  = {"StudentID", "CourseID", "Grade",
                       "CourseName", "InstructorID",
                       "InstructorName", "Office",
                       "StudentName", "Major"},
        primary_key = {"StudentID", "CourseID"},
        fds         = fds,
    )
    sample_data = [
        {"StudentID": "S01", "CourseID": "COP3502", "Grade": "A",
         "CourseName": "CS I", "InstructorID": "I1",
         "InstructorName": "Dr. Smith", "Office": "HEC-101",
         "StudentName": "Alice", "Major": "CS"},
        {"StudentID": "S02", "CourseID": "COP3502", "Grade": "B",
         "CourseName": "CS I", "InstructorID": "I1",
         "InstructorName": "Dr. Smith", "Office": "HEC-101",
         "StudentName": "Bob",   "Major": "IT"},
        {"StudentID": "S01", "CourseID": "COT4210", "Grade": "A",
         "CourseName": "Discrete II", "InstructorID": "I2",
         "InstructorName": "Dr. Jones", "Office": "HEC-205",
         "StudentName": "Alice", "Major": "CS"},
    ]
    trace_normalization(relation, sample_data)


if __name__ == "__main__":
    print("\n" + "█" * 60)
    print("  EXAMPLE 1: ORDER_ITEMS  (2NF violation — partial dependency)")
    print("█" * 60)
    example_order_items()

    print("\n" + "█" * 60)
    print("  EXAMPLE 2: EMPLOYEE  (3NF violation — transitive dependency)")
    print("█" * 60)
    example_employee()

    print("\n" + "█" * 60)
    print("  EXAMPLE 3: ENROLLMENT  (both 2NF and 3NF violations)")
    print("█" * 60)
    example_enrollment()
