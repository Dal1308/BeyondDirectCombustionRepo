import numpy as np
import yaml
from enum import Enum
from pathlib import Path
from .refrigerant_properties import RefrigerantProperties

class ModelStatus(Enum):
    VALID = "valid"
    OUT_OF_ENVELOPE = "out_of_envelope"
    INVALID = "invalid"

class PhysicsEngine:
    """
    Core physics engine for the Thermodynamic Brayton Heat-Pump Architecture-Space Model v2.
    Shifts from parametric efficiencies to emergent energy flows based on 
    heat transfer and thermodynamic states.
    """
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = Path(__file__).resolve().parents[1] / "system_config.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.ref_props = RefrigerantProperties(self.config['refrigerant'])

    def _sink_reference_temperature(self):
        return self.config.get('sink', {}).get(
            't_reference_c',
            self.config.get('environment', {}).get('t_ambient', 10.0),
        )

    def calculate_brayton_energy_split(self, fuel_flow_kg_s):
        """
        Calculates the energy split of the Brayton cycle.
        Returns both useful mechanical work and waste heat (exhaust).
        """
        lhv = self.config['fuel']['lhv']  # J/kg
        eta_engine = self.config['fuel']['eta_engine']
        
        total_energy_in = fuel_flow_kg_s * lhv
        work_turbine = total_energy_in * eta_engine
        waste_heat_exhaust = total_energy_in - work_turbine
        
        return {
            'work_turbine': work_turbine,
            'waste_heat_exhaust': waste_heat_exhaust,
            'total_energy_in': total_energy_in
        }

    @staticmethod
    def _empty_ledger():
        return {
            'input_methane_lhv': 0.0,
            'brayton_work_output': 0.0,
            'brayton_exhaust_loss': 0.0,
            'hp_condenser_heat_gross': 0.0,
            'sink_heat_transfer': 0.0,
            'hp_useful_heat': 0.0,
            'hp_compressor_irreversibility': 0.0,
            'waste_heat_recovered': 0.0,
            'total_useful_heat_out': 0.0,
            'requested_useful_load': 0.0,
            'available_useful_heat': 0.0,
            'unmet_useful_load': 0.0,
            # Legacy compatibility aliases.
            'hp_condenser_heat': 0.0,
            'sink_heat_loss': 0.0,
            'imposed_useful_load': 0.0,
        }

    def _evaluate_heat_pump_at_sink(self, work_input_w, t_source_c, t_sink_target_c):
        """
        Evaluates the vapor compression cycle at a fixed sink temperature.
        Returns detailed energy flows for the audit ledger and a status.
        """
        t_crit = self.config['limits']['t_critical_r134a']

        q_cond = 0.0
        m_dot_ref = 0.0
        work_per_kg_actual = 0.0
        work_per_kg_is = 0.0
        h_cond_liq = 0.0

        status = ModelStatus.VALID
        status_msg = "Evaluated within envelope"
        t_sink = t_sink_target_c

        if t_sink >= t_crit:
            t_sink = t_crit - 1.0

        try:
            p_evap = self.ref_props.get_saturation_pressure(t_source_c)
            p_cond = self.ref_props.get_saturation_pressure(t_sink)

            h_evap_vap = self.ref_props.get_enthalpy_saturated_vapor(t_source_c)
            h_cond_liq = self.ref_props.get_enthalpy_saturated_liquid(t_sink)

            s_evap_vap = self.ref_props.get_entropy_saturated_vapor(t_source_c)
            h_isentropic_out = self.ref_props.get_enthalpy_from_pressure_and_entropy(p_cond, s_evap_vap)

            eta_iso = self.config['heat_pump']['eta_iso']
            work_per_kg_actual = (h_isentropic_out - h_evap_vap) / eta_iso
            work_per_kg_is = (h_isentropic_out - h_evap_vap)

            if work_per_kg_actual <= 0:
                work_per_kg_actual = 1e-3

            m_dot_ref = work_input_w / work_per_kg_actual
            h_comp_out = h_evap_vap + work_per_kg_actual
            q_cond = m_dot_ref * (h_comp_out - h_cond_liq)
        except (ValueError, RuntimeError) as e:
            return {
                't_sink': t_sink,
                'q_cond': q_cond,
                'm_dot_ref': m_dot_ref,
                'cop': 0,
                'compressor_loss': 0,
                'expansion_loss': 0,
                'status': ModelStatus.INVALID,
                'status_msg': f"CoolProp Error: {str(e)}",
            }

        # Calculate internal losses for the ledger
        compressor_loss = m_dot_ref * (work_per_kg_actual - work_per_kg_is)
        expansion_loss = m_dot_ref * (h_cond_liq - h_cond_liq) # Simplified: isenthalpic

        if t_sink > t_crit - 5.0:
            status = ModelStatus.OUT_OF_ENVELOPE
            status_msg = f"Converged near critical point ({t_sink:.1f}C)"
        elif q_cond / work_input_w > 30.0 if work_input_w > 0 else False:
            status = ModelStatus.OUT_OF_ENVELOPE
            status_msg = f"Non-physical COP detected ({q_cond / work_input_w:.1f})"

        return {
            't_sink': t_sink,
            'q_cond': q_cond,
            'm_dot_ref': m_dot_ref,
            'cop': q_cond / work_input_w if work_input_w > 0 else 0,
            'compressor_loss': compressor_loss,
            'expansion_loss': expansion_loss,
            'status': status,
            'status_msg': status_msg
        }

    def solve_heat_pump_predictive(self, work_input_w, t_source_c):
        """
        Solves the vapor compression cycle to find emergent sink temperature from
        the useful sink-transfer closure: Q_cond = UA * (T_sink - T_ref).
        """
        t_ref = self._sink_reference_temperature()
        t_sink = t_ref + 30.0
        tol = self.config['limits']['convergence_tol']
        max_iter = self.config['limits']['max_iterations']
        t_crit = self.config['limits']['t_critical_r134a']
        damping = 0.5

        q_cond = 0.0
        status = ModelStatus.VALID
        status_msg = "Converged within envelope"

        for i in range(max_iter):
            if t_sink >= t_crit:
                t_sink = t_crit - 1.0

            hp_eval = self._evaluate_heat_pump_at_sink(work_input_w, t_source_c, t_sink)
            if hp_eval['status'] == ModelStatus.INVALID:
                return hp_eval

            q_cond = hp_eval['q_cond']
            ua = self.config['heat_pump']['ua_condenser']
            t_sink_actual = t_ref + (q_cond / ua)
            t_sink_actual = max(t_sink_actual, t_source_c + 2.0)

            if abs(t_sink_actual - t_sink) < tol:
                status = hp_eval['status']
                status_msg = hp_eval['status_msg']
                hp_eval['t_sink'] = t_sink
                hp_eval['status'] = status
                hp_eval['status_msg'] = status_msg
                return hp_eval

            if t_sink_actual > t_crit + 10.0:
                status = ModelStatus.OUT_OF_ENVELOPE
                status_msg = f"Sink temperature pushed way beyond critical point ({t_sink_actual:.1f}C)"
                hp_eval['status'] = status
                hp_eval['status_msg'] = status_msg
                hp_eval['t_sink'] = t_sink_actual
                return hp_eval

            t_sink = t_sink + damping * (t_sink_actual - t_sink)

        hp_eval = self._evaluate_heat_pump_at_sink(work_input_w, t_source_c, t_sink)
        hp_eval['status'] = ModelStatus.INVALID
        hp_eval['status_msg'] = "Failed to converge within max iterations"
        return hp_eval

    def perform_energy_audit(self, fuel_flow_kg_s, t_source_c, q_useful_load_w=0.0, mode="predictive"):
        """
        Performs a full energy audit of the system.
        Tracks every Joule from methane input to final heat delivery.
        """
        # --- Input Guards ---
        if fuel_flow_kg_s <= 0:
            return {
                'ledger': self._empty_ledger(),
                'metrics': {'eta_effective': 0.0, 't_sink': 0.0, 'cop_hp': 0.0},
                'status': ModelStatus.INVALID,
                'status_msg': "Fuel flow must be positive"
            }
        
        t_crit = self.config['limits']['t_critical_r134a']
        if t_source_c >= t_crit - 5.0:
            return {
                'ledger': self._empty_ledger(),
                'metrics': {'eta_effective': 0.0, 't_sink': 0.0, 'cop_hp': 0.0},
                'status': ModelStatus.OUT_OF_ENVELOPE,
                'status_msg': f"Source temperature too high (near critical point {t_crit}C)"
            }
        if mode not in {"predictive", "feasibility"}:
            return {
                'ledger': self._empty_ledger(),
                'metrics': {'eta_effective': 0.0, 't_sink': 0.0, 'cop_hp': 0.0},
                'status': ModelStatus.INVALID,
                'status_msg': f"Unknown mode '{mode}'"
            }
        if mode == "predictive" and q_useful_load_w not in (0, 0.0):
            return {
                'ledger': self._empty_ledger(),
                'metrics': {'eta_effective': 0.0, 't_sink': 0.0, 'cop_hp': 0.0},
                'status': ModelStatus.INVALID,
                'status_msg': "q_useful_load_w is only supported in feasibility mode"
            }
        if mode == "feasibility" and q_useful_load_w < 0:
            return {
                'ledger': self._empty_ledger(),
                'metrics': {'eta_effective': 0.0, 't_sink': 0.0, 'cop_hp': 0.0},
                'status': ModelStatus.INVALID,
                'status_msg': "Requested useful load must be non-negative"
            }

        # 1. Brayton Cycle Energy Split
        brayton = self.calculate_brayton_energy_split(fuel_flow_kg_s)
        work_turbine = brayton['work_turbine']
        waste_heat_exhaust = brayton['waste_heat_exhaust']
        total_energy_in = brayton['total_energy_in']

        # 2. Heat Pump Cycle Energy Flow
        if mode == "predictive":
            hp_results = self.solve_heat_pump_predictive(work_turbine, t_source_c)
        else:
            ua = self.config['heat_pump']['ua_condenser']
            t_ref = self._sink_reference_temperature()
            required_sink_temp = max(t_ref + (q_useful_load_w / ua), t_source_c + 2.0)
            if required_sink_temp >= t_crit - 5.0:
                hp_results = {
                    't_sink': required_sink_temp,
                    'q_cond': 0.0,
                    'm_dot_ref': 0.0,
                    'cop': 0.0,
                    'compressor_loss': 0.0,
                    'expansion_loss': 0.0,
                    'status': ModelStatus.OUT_OF_ENVELOPE,
                    'status_msg': f"Required sink temperature outside envelope ({required_sink_temp:.1f}C)",
                }
            else:
                hp_results = self._evaluate_heat_pump_at_sink(work_turbine, t_source_c, required_sink_temp)

        q_cond_gross = hp_results['q_cond']
        comp_loss = hp_results['compressor_loss']
        hp_status = hp_results['status']
        hp_msg = hp_results['status_msg']

        # 3. Heat Recovery: Recover heat from the Brayton exhaust stream
        eff_rec = self.config['heat_pump']['recovery_effectiveness']
        q_recovery = waste_heat_exhaust * eff_rec

        if mode == "predictive":
            q_sink_transfer = q_cond_gross
            q_cond_useful = q_cond_gross
            requested_useful_load = 0.0
            available_useful_heat = q_cond_gross
            unmet_useful_load = 0.0
        else:
            requested_useful_load = q_useful_load_w
            available_useful_heat = max(q_cond_gross, 0.0)
            q_cond_useful = min(available_useful_heat, requested_useful_load)
            unmet_useful_load = max(requested_useful_load - available_useful_heat, 0.0)
            q_sink_transfer = q_cond_useful
            if hp_status == ModelStatus.VALID and unmet_useful_load > 1e-6:
                hp_status = ModelStatus.OUT_OF_ENVELOPE
                hp_msg = (
                    f"Requested useful load not met "
                    f"({available_useful_heat:.1f} W available vs {requested_useful_load:.1f} W requested)"
                )

        q_total_out = q_cond_useful + q_recovery

        # Effective System Efficiency: Includes ambient heat harvested by the HP
        eta_effective = q_total_out / total_energy_in

        ledger = {
            'input_methane_lhv': total_energy_in,
            'brayton_work_output': work_turbine,
            'brayton_exhaust_loss': waste_heat_exhaust,
            'hp_condenser_heat_gross': q_cond_gross,
            'sink_heat_transfer': q_sink_transfer,
            'hp_useful_heat': q_cond_useful,
            'hp_compressor_irreversibility': comp_loss,
            'waste_heat_recovered': q_recovery,
            'total_useful_heat_out': q_total_out,
            'requested_useful_load': requested_useful_load,
            'available_useful_heat': available_useful_heat,
            'unmet_useful_load': unmet_useful_load,
            # Legacy compatibility aliases.
            'hp_condenser_heat': q_cond_gross,
            'sink_heat_loss': 0.0,
            'imposed_useful_load': requested_useful_load,
        }

        return {
            'ledger': ledger,
            'metrics': {
                'eta_effective': eta_effective,
                't_sink': hp_results['t_sink'],
                'cop_hp': hp_results['cop']
            },
            'status': hp_status,
            'status_msg': hp_msg
        }

    def calculate_total_efficiency(self, fuel_flow_kg_s, t_source_c, q_useful_load_w=0.0):
        """Legacy wrapper for backward compatibility."""
        audit = self.perform_energy_audit(fuel_flow_kg_s, t_source_c, q_useful_load_w)
        return {
            'eta_conv': audit['metrics']['eta_effective'],
            't_sink': audit['metrics']['t_sink'],
            'q_cond': audit['ledger']['hp_condenser_heat_gross'],
            'q_cond_useful': audit['ledger']['hp_useful_heat'],
            'work_turbine': audit['ledger']['brayton_work_output'],
            'status': audit['status'].value if audit['status'] else None,
            'status_msg': audit.get('status_msg', 'N/A')
        }

if __name__ == "__main__":
    # Test the engine with config file
    engine = PhysicsEngine()
    res = engine.calculate_total_efficiency(fuel_flow_kg_s=1e-3, t_source_c=15.0)
    print(f"Results: {res}")
