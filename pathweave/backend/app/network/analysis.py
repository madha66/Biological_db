"""Deterministic network construction without a heavy graph dependency."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, Iterable, List, Set, Tuple

from app.api.models import (
    DiseaseAssociation,
    DiseasePathway,
    IntegratedNetwork,
    NetworkCluster,
    NetworkEdge,
    NetworkNode,
    ProteinInteraction,
    RNAInteraction,
    LncRNAAssociation,
    SharedAssociation,
)


def _add_node(nodes: Dict[str, NetworkNode], identifier: str, node_type: str) -> None:
    nodes.setdefault(identifier, NetworkNode(id=identifier, label=identifier, node_type=node_type))


def build_integrated_network(
    inputs: List[str],
    input_types: Dict[str, str],
    associations: List[DiseaseAssociation],
    pathways: List[DiseasePathway],
    mirna_relationships: List[RNAInteraction],
    lncrna_relationships: List[LncRNAAssociation],
    protein_interactions: List[ProteinInteraction],
) -> IntegratedNetwork:
    nodes: Dict[str, NetworkNode] = {}
    edges: Dict[Tuple[str, str, str, str], NetworkEdge] = {}
    for item in inputs:
        node_type = input_types.get(item, "gene")
        _add_node(nodes, item, node_type)

    def add_edge(source: str, target: str, edge_type: str, source_db: str,
                 evidence: str | None = None, score: float | None = None) -> None:
        key = (source, target, edge_type, source_db)
        edges.setdefault(key, NetworkEdge(
            source=source, target=target, edge_type=edge_type,
            source_db=source_db, evidence=evidence, score=score,
        ))

    for association in associations:
        _add_node(nodes, association.input_name, input_types.get(association.input_name, "gene"))
        _add_node(nodes, association.disease_id, "disease")
        add_edge(association.input_name, association.disease_id, "associated_with", association.source_db,
                 association.evidence, association.score)
    for pathway in pathways:
        _add_node(nodes, pathway.pathway_id, "pathway")
        for gene in pathway.input_genes:
            _add_node(nodes, gene, input_types.get(gene, "gene"))
            add_edge(gene, pathway.pathway_id, "participates_in", pathway.source_db)
    for item in mirna_relationships:
        _add_node(nodes, item.rna, "miRNA")
        _add_node(nodes, item.target_gene, "gene")
        add_edge(item.rna, item.target_gene, "targets", item.source_db, item.evidence)
    for item in lncrna_relationships:
        _add_node(nodes, item.lncrna, "lncRNA")
        for target in item.target_genes:
            _add_node(nodes, target, "gene")
            add_edge(item.lncrna, target, "regulates", item.source_db, item.evidence)
    for item in protein_interactions:
        _add_node(nodes, item.source_gene, "protein")
        _add_node(nodes, item.target_gene, "protein")
        add_edge(item.source_gene, item.target_gene, "interacts_with", item.source_db,
                 score=item.score)
    return IntegratedNetwork(nodes=list(nodes.values()), edges=list(edges.values()))


def _components(network: IntegratedNetwork) -> List[List[str]]:
    adjacency: Dict[str, Set[str]] = defaultdict(set)
    for node in network.nodes:
        adjacency[node.id]
    for edge in network.edges:
        adjacency[edge.source].add(edge.target)
        adjacency[edge.target].add(edge.source)
    seen: Set[str] = set()
    groups: List[List[str]] = []
    for node_id in sorted(adjacency):
        if node_id in seen:
            continue
        stack = [node_id]
        seen.add(node_id)
        group: List[str] = []
        while stack:
            current = stack.pop()
            group.append(current)
            for neighbor in sorted(adjacency[current], reverse=True):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        groups.append(sorted(group))
    return groups


def cluster_network(
    network: IntegratedNetwork,
    associations: List[DiseaseAssociation],
    pathways: List[DiseasePathway],
) -> List[NetworkCluster]:
    node_types = {node.id: node.node_type for node in network.nodes}
    disease_by_gene: Dict[str, Set[str]] = defaultdict(set)
    for association in associations:
        disease_by_gene[association.input_name].add(association.disease_name)
    pathway_by_gene: Dict[str, Set[str]] = defaultdict(set)
    for pathway in pathways:
        for gene in pathway.input_genes:
            pathway_by_gene[gene].add(pathway.pathway_name)
    clusters: List[NetworkCluster] = []
    for index, members in enumerate(_components(network), start=1):
        types = Counter(node_types.get(member, "unknown") for member in members)
        genes = [member for member in members if node_types.get(member) in {"gene", "protein"}]
        diseases = sorted({value for member in members for value in disease_by_gene.get(member, set())})
        pathways_for_cluster = sorted({value for member in members for value in pathway_by_gene.get(member, set())})
        clusters.append(NetworkCluster(
            cluster_id=f"cluster-{index}",
            members=members,
            node_count=len(members),
            node_types=dict(types),
            major_genes=sorted(genes),
            associated_diseases=diseases,
            associated_pathways=pathways_for_cluster,
        ))
    return clusters


def shared_unique_associations(
    entity_to_associations: Dict[str, Iterable[str]],
) -> Tuple[List[SharedAssociation], Dict[str, List[str]]]:
    normalized = {key: set(values) for key, values in entity_to_associations.items()}
    support: Dict[str, List[str]] = defaultdict(list)
    for entity, values in normalized.items():
        for value in values:
            support[value].append(entity)
    shared = [
        SharedAssociation(
            association=value,
            supporting_inputs=sorted(entities),
            scope="all inputs" if len(entities) == len(normalized) else "input subset",
        )
        for value, entities in sorted(support.items())
        if len(entities) > 1
    ]
    unique = {
        entity: sorted(value for value in values if len(support[value]) == 1)
        for entity, values in normalized.items()
    }
    return shared, unique
