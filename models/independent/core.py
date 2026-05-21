"""
models/independent/core.py

Pure thermodynamic benchmark physics — zero matplotlib / plotting dependencies.
Safe to import in notebooks, tests, or any non-plotting context.

This module is the independent layer's sole purpose: explore the design space
of the reversible benchmark from SI Note 1. It computes Q_H,max across fuels
and temperatures, providing the theoretical ceiling against which implementations
(Aspen, Brayton heat-pump architecture-space model) are compared.

Exports:
    MethaneProperties - frozen dataclass for fuel reaction thermodynamics
    carnot_efficiency() — η_Carnot for a reversible engine
    thermodynamic_limit() — Q_H,max from entropy-balance (SI Note 1)
"""

from __future__ import annotations

from dataclasses import dataclass


# ── Fuel property database ─────────────────────────────────────────────────

@dataclass(frozen=True)
class MethaneProperties:
    """Standard enthalpy and entropy for methane combustion.

    ΔH°_rxn = -890.7 kJ/mol (exothermic)
    ΔS°_rxn = -243 J/(mol·K) (gas moles decrease: 2 → 1)
    """
    delta_h_kj_per_mol: float = -890.7
    delta_s_kj_per_mol_k: float = -0.243
    co2_mol_per_mol_fuel: float = 1.0

    def delta_g_magnitude(self, temperature_k: float) -> float:
        """|ΔG°| = |ΔH° − T·ΔS°| at the given temperature."""
        return abs(self.delta_h_kj_per_mol - temperature_k * self.delta_s_kj_per_mol_k)


@dataclass(frozen=True)
class SyngasProperties:
    """Thermodynamics for syngas combustion:
    CO(g) + 2 H₂(g) + 1.5 O₂(g) → CO₂(g) + 2 H₂O(l).

    This corresponds to a CO:H₂ ratio of 1:2 (coal-gasification syngas).
    Product water is liquid, matching the methane convention.

    Data sources (NIST WebBook / CODATA, 298 K):
        ΔfH°(CO,g)  = -110.53 kJ/mol,  S°(CO,g)  = 197.66 J/mol·K
        ΔfH°(CO₂,g) = -393.51 kJ/mol, S°(CO₂,g) = 213.79 J/mol·K
        ΔfH°(H₂O,l) = -285.83 kJ/mol, S°(H₂O,l) = 69.95 J/mol·K
        S°(H₂,g)    = 130.68 J/mol·K
        S°(O₂,g)    = 205.15 J/mol·K

    Derived:
        ΔH°_rxn = -854.6 kJ/mol ≈ -855.0 kJ/mol (legacy rounded)
        ΔS°_rxn = -413.1 J/(mol·K) = -0.413 kJ/(mol·K) (legacy rounded)
    """
    delta_h_kj_per_mol: float = -855.0
    delta_s_kj_per_mol_k: float = -0.413
    co2_mol_per_mol_fuel: float = 1.0

    def delta_g_magnitude(self, temperature_k: float) -> float:
        return abs(self.delta_h_kj_per_mol - temperature_k * self.delta_s_kj_per_mol_k)


@dataclass(frozen=True)
class CarbonProperties:
    """Thermodynamics for solid carbon (graphite) oxidation: C(s) + O₂(g) → CO₂(g).

    Data sources (NIST WebBook / CODATA, 298 K):
        ΔfH°(CO₂,g) = -393.51 kJ/mol  [Cox, Wagman et al. 1984]
        S°(graphite)  = 5.60 J/mol·K  [NIST WebBook, avg of 10 values]
        S°(O₂,g)      = 205.15 J/mol·K [Cox, Wagman et al. 1984]
        S°(CO₂,g)     = 213.79 J/mol·K [Cox, Wagman et al. 1984]

    Derived:
        ΔH°_rxn = -393.5 kJ/mol
        ΔS°_rxn = +3.0 J/(mol·K)  (positive — 1 mol gas → 2 mol gas)
    """
    delta_h_kj_per_mol: float = -393.5
    delta_s_kj_per_mol_k: float = 0.0030
    co2_mol_per_mol_fuel: float = 1.0

    def delta_g_magnitude(self, temperature_k: float) -> float:
        return abs(self.delta_h_kj_per_mol - temperature_k * self.delta_s_kj_per_mol_k)


@dataclass(frozen=True)
class HydrogenProperties:
    """
    Thermodynamics for hydrogen combustion: H2(g) + 1/2 O2(g) -> H2O(g).

    Data sources (NIST WebBook / CODATA, 298 K):
        S°(H2,g) = 130.68 J/mol.K
        S°(O2,g) = 205.147 J/mol.K
        S°(H2O,g) = 188.834 J/mol.K
        ΔfH°(H2O,g) = -241.826 kJ/mol

    Derived:
        ΔH°_rxn = -241.826 kJ/mol
        ΔS°_rxn = -44.420 J/mol.K
    """
    delta_h_kj_per_mol: float = -241.826
    delta_s_kj_per_mol_k: float = -0.04442
    co2_mol_per_mol_fuel: float = 0.0

    def delta_g_magnitude(self, temperature_k: float) -> float:
        return abs(self.delta_h_kj_per_mol - temperature_k * self.delta_s_kj_per_mol_k)


@dataclass(frozen=True)
class AmmoniaProperties:
    """
    Thermodynamics for ammonia combustion: NH3(g) + 3/4 O2(g) -> 1/2 N2(g) + 3/2 H2O(g).

    Data sources (NIST WebBook / CODATA, 298 K):
        ΔfH°(NH3,g) = -45.94 kJ/mol, S°(NH3,g) = 192.77 J/mol.K
        S°(N2,g) = 191.609 J/mol.K
        S°(O2,g) = 205.147 J/mol.K
        S°(H2O,g) = 188.834 J/mol.K
        ΔfH°(H2O,g) = -241.826 kJ/mol

    Derived:
        ΔH°_rxn = -316.799 kJ/mol
        ΔS°_rxn = +32.425 J/mol.K (positive — net gas mole increase)
    """
    delta_h_kj_per_mol: float = -316.799
    delta_s_kj_per_mol_k: float = 0.032425
    co2_mol_per_mol_fuel: float = 0.0

    def delta_g_magnitude(self, temperature_k: float) -> float:
        return abs(self.delta_h_kj_per_mol - temperature_k * self.delta_s_kj_per_mol_k)


def get_fuel(name: str):
    """Return a fuel properties instance (methane/syngas/carbon/hydrogen/ammonia)."""
    fuels = {"methane": MethaneProperties,
             "syngas": SyngasProperties,
             "carbon": CarbonProperties,
             "hydrogen": HydrogenProperties,
             "ammonia": AmmoniaProperties}
    return fuels[name]()


# ── Core thermodynamic functions ────────────────────────────────────────────

def carnot_efficiency(t_cold_k: float, t_hot_k: float) -> float:
    """Carnot efficiency for a reversible engine between two reservoirs."""
    if t_hot_k <= t_cold_k:
        raise ValueError("t_hot_k must be greater than t_cold_k")
    return 1.0 - (t_cold_k / t_hot_k)


def carnot_heating_cop(t_cold_k: float, t_hot_k: float) -> float:
    """Carnot COP for a reversible heat pump between two reservoirs."""
    if t_hot_k <= t_cold_k:
        raise ValueError("t_hot_k must be greater than t_cold_k")
    return t_hot_k / (t_hot_k - t_cold_k)


def thermodynamic_limit(
    props,  # MethaneProperties or similar — duck-typed for delta_h, delta_s
    t_cold_k: float,
    t_hot_k: float,
) -> dict[str, float]:
    """
    Reversible upper bound for heat delivery from a chemical fuel.

    Derived from First+Second Law entropy balance (SI Note 1):

        Q_H^{max} = [ΔH°/T_C − ΔS°] / [1/T_H − 1/T_C]

    Which is algebraically equivalent to:

        Q_H^{max} = |ΔG°(T_C)| / η_Carnot

    where ΔG° is evaluated at the cold-reservoir temperature T_C.

    This is the thermodynamic ceiling — no real system can exceed it.
    """
    eta_carnot = carnot_efficiency(t_cold_k, t_hot_k)
    delta_g_mag = props.delta_g_magnitude(t_cold_k)
    q_h_max     = delta_g_mag / eta_carnot

    return {
        "q_h_max_kj_per_mol":  q_h_max,
        "eta_carnot":          eta_carnot,
        "cop_carnot":          carnot_heating_cop(t_cold_k, t_hot_k),
        "delta_g_magnitude":   delta_g_mag,
    }


def heating_multiplier(props, t_cold_k: float, t_hot_k: float) -> float:
    """
    Dimensionless: Q_H,max / |ΔH°| — how many times the fuel enthalpy
    can be delivered as heat when work potential is fully exploited.

    This is the quantity plotted in Fig. A (benchmark surface).
    """
    limit = thermodynamic_limit(props, t_cold_k, t_hot_k)
    # props.delta_h_kj_per_mol is signed (negative for combustion);
    # use abs() to get the magnitude for the denominator.
    return limit["q_h_max_kj_per_mol"] / abs(props.delta_h_kj_per_mol)



