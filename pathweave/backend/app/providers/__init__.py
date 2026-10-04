"""Pluggable RNA interaction providers for PathWeave."""
from __future__ import annotations

import csv
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from app.scoring.scorer import RNAInteraction

logger = logging.getLogger(__name__)


class InteractionProvider(ABC):
    """Abstract base for RNA interaction data sources."""

    @abstractmethod
    def get_interactions(
        self,
        seed_genes: List[str],
        rna_types: Optional[List[str]] = None,
    ) -> List[RNAInteraction]:
        """Return RNA interactions for the given seed genes."""
        ...

    @property
    @abstractmethod
    def name(self) -> str: ...


# ---------------------------------------------------------------------------
# CSV-backed provider (ships with PathWeave for demo mode)
# ---------------------------------------------------------------------------


class CSVInteractionProvider(InteractionProvider):
    """
    Loads interactions from a CSV file with columns:
    rna_id, rna_type, target_gene, evidence, source_db

    Plug-in: instantiate with any conforming CSV.
    Compatible with exports from miRTarBase, ENCORI/starBase, LncRNA2Target.
    """

    def __init__(self, csv_path: Path) -> None:
        self._path = csv_path
        self._interactions: Optional[List[RNAInteraction]] = None

    @property
    def name(self) -> str:
        return f"CSV:{self._path.stem}"

    def _load(self) -> List[RNAInteraction]:
        interactions = []
        with open(self._path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                interactions.append(
                    RNAInteraction(
                        rna_id=row["rna_id"].strip(),
                        rna_type=row["rna_type"].strip(),
                        target_gene=row["target_gene"].strip().upper(),
                        evidence=row["evidence"].strip(),
                        source_db=row["source_db"].strip(),
                    )
                )
        logger.info("Loaded %d interactions from %s", len(interactions), self._path)
        return interactions

    def get_interactions(
        self,
        seed_genes: List[str],
        rna_types: Optional[List[str]] = None,
    ) -> List[RNAInteraction]:
        if self._interactions is None:
            self._interactions = self._load()

        seed_upper = {g.upper() for g in seed_genes}
        result = []
        for ix in self._interactions:
            if rna_types and ix.rna_type not in rna_types:
                continue
            # Include interactions where the seed gene is the target
            # OR interactions from RNAs that target any seed gene (expand neighborhood)
            if ix.target_gene in seed_upper:
                result.append(ix)
        return result

    def get_all_interactions(
        self,
        rna_types: Optional[List[str]] = None,
    ) -> List[RNAInteraction]:
        """Return all interactions (used to build the full gene universe)."""
        if self._interactions is None:
            self._interactions = self._load()
        if rna_types:
            return [ix for ix in self._interactions if ix.rna_type in rna_types]
        return list(self._interactions)

    def expand_neighborhood(
        self,
        seed_genes: List[str],
        rna_types: Optional[List[str]] = None,
    ) -> List[RNAInteraction]:
        """
        Two-hop expansion:
        1. Find all RNAs that target any seed gene.
        2. Return ALL genes those RNAs target (the RNA neighborhood).
        """
        if self._interactions is None:
            self._interactions = self._load()

        seed_upper = {g.upper() for g in seed_genes}

        # Step 1: which RNAs touch the seed?
        seed_rnas: set[str] = set()
        for ix in self._interactions:
            if rna_types and ix.rna_type not in rna_types:
                continue
            if ix.target_gene in seed_upper:
                seed_rnas.add(ix.rna_id)

        # Step 2: all targets of those RNAs
        result = []
        for ix in self._interactions:
            if rna_types and ix.rna_type not in rna_types:
                continue
            if ix.rna_id in seed_rnas:
                result.append(ix)

        return result


# ---------------------------------------------------------------------------
# Future provider stubs (documented interface)
# ---------------------------------------------------------------------------
# To integrate miRTarBase:
#   class MiRTarBaseProvider(InteractionProvider): ...
#
# To integrate ENCORI/starBase:
#   class ENCORIProvider(InteractionProvider): ...
#
# To integrate LncRNA2Target:
#   class LncRNA2TargetProvider(InteractionProvider): ...
#
# Each must implement get_interactions() returning List[RNAInteraction].
# ---------------------------------------------------------------------------
