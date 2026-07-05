"""
normalizer.py
Core normalization engine: detects violations and decomposes
a relational schema from 1NF through 3NF, printing step-by-step
reasoning at each stage.

THEORY:
-------
A relation schema R with functional dependencies (FDs) F is in:

  1NF  -- all attributes are atomic (no repeating groups or multi-valued
           attributes). We assume input tables are already atomic and
           check for duplicate rows and missing primary key instead.

  2NF  -- in 1NF AND no non-prime attribute is partially dependent on
           any candidate key. A partial dependency means a non-key
           attribute depends on only PART of a composite key.
           (If the key is a single attribute, 2NF is automatic.)

  3NF  -- in 2NF AND no non-prime attribute is transitively dependent
           on the primary key. A transitive dependency means:
           key → X → Y, where X is not a key/superkey.

Decomposition strategy used here is lossless and dependency-preserving
(we use the standard 3NF synthesis algorithm approach):
  - For each violating FD, split off a new relation containing the
    determinant + dependent attributes.
  - Keep the original relation with violating attributes removed.
"""


class FunctionalDependency:
    """Represents a single functional dependency: determinant → dependent."""

    def __init__(self, determinant, dependent):
        """
        Args:
            determinant: frozenset or set of attribute names (left-hand side)
            dependent:   frozenset or set of attribute names (right-hand side)
        """
        self.determinant = frozenset(determinant)
        self.dependent   = frozenset(dependent)

    def __repr__(self):
        lhs = ", ".join(sorted(self.determinant))
        rhs = ", ".join(sorted(self.dependent))
        return f"{{{lhs}}} → {{{rhs}}}"


class Relation:
    """Represents a relation schema: a name, a set of attributes, a primary key, and FDs."""

    def __init__(self, name, attributes, primary_key, fds):
        """
        Args:
            name:        string name of the relation
            attributes:  set of attribute name strings
            primary_key: set of attribute names that form the primary key
            fds:         list of FunctionalDependency objects
        """
        self.name        = name
        self.attributes  = set(attributes)
        self.primary_key = frozenset(primary_key)
        self.fds         = fds

    def non_key_attributes(self):
        return self.attributes - self.primary_key

    def __repr__(self):
        attrs  = ", ".join(sorted(self.attributes))
        pk     = ", ".join(sorted(self.primary_key))
        return f"{self.name}({attrs})  PK={{{pk}}}"


# ── 1NF check ────────────────────────────────────────────────────────────────

def check_1nf(relation, sample_data=None):
    """
    Check if a relation is in 1NF.
    For our purposes: every relation with a defined primary key and
    atomic attributes is assumed structurally 1NF-compliant.
    If sample_data (list of dicts) is provided, we also check for
    duplicate primary-key values (which would violate entity integrity).

    Returns (is_1nf: bool, violations: list of str)
    """
    violations = []

    if not relation.primary_key:
        violations.append("No primary key defined — 1NF requires a primary key.")

    if sample_data:
        seen_keys = set()
        for row in sample_data:
            key_val = tuple(row.get(k) for k in sorted(relation.primary_key))
            if key_val in seen_keys:
                violations.append(f"Duplicate primary key value {key_val} — violates 1NF.")
                break
            seen_keys.add(key_val)

    return len(violations) == 0, violations


# ── 2NF check and decomposition ───────────────────────────────────────────────

def find_partial_dependencies(relation):
    """
    Find all partial dependencies: non-key attributes that depend on
    a PROPER SUBSET of the primary key (only possible with composite keys).

    Returns list of (partial_key_subset: frozenset, dependent_attrs: frozenset)
    """
    if len(relation.primary_key) <= 1:
        return []  # single-attribute key → 2NF is automatic

    partials = []
    pk = relation.primary_key
    non_key = relation.non_key_attributes()

    # check every proper non-empty subset of the primary key
    pk_list = sorted(pk)
    n = len(pk_list)
    for mask in range(1, (1 << n) - 1):   # exclude empty set and full set
        subset = frozenset(pk_list[i] for i in range(n) if mask & (1 << i))

        # find which non-key attrs are determined by this subset
        determined = frozenset()
        for fd in relation.fds:
            if fd.determinant == subset and fd.dependent <= non_key:
                determined |= fd.dependent

        if determined:
            partials.append((subset, determined))

    return partials


def decompose_to_2nf(relation):
    """
    Decompose a relation into 2NF by removing partial dependencies.

    Returns list of Relation objects (the decomposed relations).
    """
    partials = find_partial_dependencies(relation)
    if not partials:
        return [relation]

    new_relations = []
    remaining_attrs = set(relation.attributes)
    remaining_fds   = list(relation.fds)

    for subset, dependent_attrs in partials:
        # new relation: partial key + its dependents
        new_name  = relation.name + "_" + "_".join(sorted(subset))
        new_attrs = subset | dependent_attrs
        new_fds   = [fd for fd in relation.fds
                     if fd.determinant == subset and fd.dependent <= dependent_attrs]
        new_rel   = Relation(new_name, new_attrs, subset, new_fds)
        new_relations.append(new_rel)

        # remove the migrated attributes from the original (keep key attrs)
        remaining_attrs -= dependent_attrs
        remaining_fds    = [fd for fd in remaining_fds
                            if not (fd.determinant == subset and fd.dependent <= dependent_attrs)]

    # the remainder: original key + what's left
    if remaining_attrs != relation.primary_key:
        remainder = Relation(
            relation.name,
            remaining_attrs,
            relation.primary_key,
            remaining_fds,
        )
        new_relations.append(remainder)

    return new_relations


# ── 3NF check and decomposition ───────────────────────────────────────────────

def find_transitive_dependencies(relation):
    """
    Find transitive dependencies: non-key attribute X determines
    another non-key attribute Y (key → X → Y, X is not a key).

    Returns list of (determinant: frozenset, dependent: frozenset)
    """
    non_key = relation.non_key_attributes()
    transitives = []

    for fd in relation.fds:
        # determinant must be a subset of non-key attrs (not the key itself)
        if (fd.determinant <= non_key
                and fd.determinant != relation.primary_key
                and fd.dependent <= non_key
                and fd.dependent.isdisjoint(fd.determinant)):
            transitives.append((fd.determinant, fd.dependent))

    return transitives


def decompose_to_3nf(relation):
    """
    Decompose a relation into 3NF by removing transitive dependencies.

    Returns list of Relation objects.
    """
    transitives = find_transitive_dependencies(relation)
    if not transitives:
        return [relation]

    new_relations = []
    remaining_attrs = set(relation.attributes)
    remaining_fds   = list(relation.fds)

    for determinant, dependent_attrs in transitives:
        new_name  = relation.name + "_" + "_".join(sorted(determinant))
        new_attrs = determinant | dependent_attrs
        new_fds   = [fd for fd in relation.fds
                     if fd.determinant == determinant and fd.dependent <= dependent_attrs]
        new_rel   = Relation(new_name, new_attrs, determinant, new_fds)
        new_relations.append(new_rel)

        remaining_attrs -= dependent_attrs
        remaining_fds    = [fd for fd in remaining_fds
                            if not (fd.determinant == determinant
                                    and fd.dependent <= dependent_attrs)]

    remainder = Relation(
        relation.name,
        remaining_attrs,
        relation.primary_key,
        remaining_fds,
    )
    new_relations.append(remainder)

    return new_relations
