from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo


MAX_NJOBS = 8

FEED_FAVICONS: dict[str, str] = {
    "arxiv": "https://arxiv.org/favicon.ico",
    "aps": "https://cdn.journals.aps.org/development/journals/images/favicon.ico",
    "nature": "https://www.nature.com/uploads/product/npjcompumats/rss.png",
    "chemrxiv": "https://chemrxiv.org/favicon.ico",
}

# For RSS generation
TODAY_JST = datetime.now(ZoneInfo("Asia/Tokyo"))

# For arXiv fetch
_CATEGORIES = [
    "cond-mat.mtrl-sci",
    "physics.comp-ph",
]

# For APS Physical Review fetch
_APS_JOURNALS = ["prb", "prl", "prmaterials", "prx"]

# For Nature journal fetch
_NATURE_JOURNALS = ["npjcompumats"]

# For LLM-based paper filtering
_INTERESTS = """\
- Research discussing material properties from the perspective of symmetry
- Research computationally exploring crystal structures and phase diagrams
- Research on classification of crystal structures
- Research using computational chemistry to design/predict synthesizability and synthesis recipes across solid, liquid, and gas phases
- Open-source software in the computational materials science domain
\
"""

# Applied to every feed. Without these the model treated topical adjacency as a
# match and recommended over half of each day's papers: fabrication write-ups,
# lattice-model theory, and quantum-optics work all rode in on a shared keyword.
# The last bullet was added after standard periodic-DFT property runs (point
# defects in a single oxide, hydrogen energetics in one alloy) kept passing on the
# strength of being computational materials science.
_EXCLUSIONS = """\
- Papers whose contribution is sample growth, fabrication, device engineering, or \
measurement (transport, spectroscopy, microscopy, instrumentation), with no substantial \
computational or theoretical component.
- Abstract condensed-matter theory of model Hamiltonians: lattice models, flat bands, \
symmetry-protected topological phases, quantum criticality, entanglement measures. A \
symmetry analysis is still of interest when it explains a property of a specific real \
material rather than of a model.
- Photonics, metamaterials, quantum optics, quantum information, qubits, and cold atoms.
- Routine property evaluation of an already-known compound, where the novelty is the \
compound rather than the reasoning: defect and dopant formation energies, migration \
barriers, hydrogen or ion energetics, short-range order, adsorption energies, elastic, \
thermal, or transport coefficients. Such a paper is of interest only when its \
contribution is a symmetry argument, a structure or phase search, a classification, a \
synthesizability or synthesis-route assessment, or a released method, dataset, or code.
\
"""

# Crossref carries no ChemRxiv subject-area metadata, so this instruction makes
# the LLM stand in for the old "Theoretical and Computational Chemistry" filter.
# The explicit no/yes lists exist because a bare "computational AND matching the
# interests" rule let the computational half dominate: the feed filled up with
# molecular quantum-chemistry method papers that match no interest above.
_CHEMRXIV_EXTRA_CRITERIA = """\
The papers below are ChemRxiv preprints from every area of chemistry, and the large \
majority are irrelevant to the reader. Answer "yes" only when the paper is both \
(a) primarily theoretical, computational, or data-driven and (b) about crystalline \
solids, solid-state/inorganic materials, or the synthesis of such materials. \
Being computational is not on its own a reason to answer "yes", and neither is \
solid-state vocabulary in a paper whose subject is molecular: judge the contribution, \
not the material class of the reagents.

Also answer "no" for:
- Electronic-structure or quantum-chemistry method development demonstrated only on \
isolated molecules: perturbation-theory variants, basis sets, functionals benchmarked \
on molecular test sets, energy decomposition analysis, excited-state methods for dyes.
- Reaction mechanism or kinetics studies of molecular or homogeneous systems.
- Molecular dynamics of solutions, fluids, polymers, or biological matter with no \
crystalline or solid-state component.
- Drug discovery, cheminformatics, QSAR, and property-prediction models over molecular \
datasets, and general machine-learning methodology with no materials application.
- General theories of chemical bonding, atomic structure, or the periodic table: \
bond-order and bond-length relations, bond-energy or electronegativity scales, orbital \
models, and regularities in the element sequence.
- Catalysis whose contribution is the organic or molecular transformation it enables \
(C-H activation, cross-coupling, hydrogenation, polymerization), even when the catalyst \
itself is a solid, an electride, a zeolite, or a metal-organic framework.

Answer "yes" for papers such as:
- Crystal structure prediction, polymorph or cocrystal prediction, and classification or \
symmetry analysis of crystal structures.
- Periodic first-principles calculations whose contribution is a symmetry analysis, a \
structural or phase-stability result, or a new method, rather than one more compound's \
property table.
- Computational phase diagrams, thermodynamic stability, or synthesizability and synthesis \
routes of solid materials.
- Machine-learning interatomic potentials or datasets targeting inorganic or solid materials.
- Open-source software or databases for computational materials science.
"""


@dataclass
class Config:
    title: str = "article-rss-proxy"
    deploy_url: str = "https://lan496.github.io/article-rss-proxy/"
    categories: list[str] = field(default_factory=lambda: _CATEGORIES)
    interests: str = _INTERESTS
    exclusions: str = _EXCLUSIONS
    aps_journals: list[str] = field(default_factory=lambda: _APS_JOURNALS)
    nature_journals: list[str] = field(default_factory=lambda: _NATURE_JOURNALS)
    chemrxiv_extra_criteria: str = _CHEMRXIV_EXTRA_CRITERIA
