import CoolProp.CoolProp as CP

class RefrigerantProperties:
    """
    Provides thermodynamic properties for a specified refrigerant using CoolProp.
    This ensures high-fidelity data suitable for scientific publication.
    """
    def __init__(self, fluid="R134a"):
        self.fluid = fluid

    def get_saturation_pressure(self, T_celsius):
        """Returns the saturation pressure [Pa] at a given temperature [C]."""
        T_kelvin = T_celsius + 273.15
        return CP.PropsSI('P', 'T', T_kelvin, 'Q', 0, self.fluid)

    def get_enthalpy_saturated_liquid(self, T_celsius):
        """Returns the enthalpy [J/kg] of saturated liquid at a given temperature [C]."""
        T_kelvin = T_celsius + 273.15
        return CP.PropsSI('H', 'T', T_kelvin, 'Q', 0, self.fluid)

    def get_enthalpy_saturated_vapor(self, T_celsius):
        """Returns the enthalpy [J/kg] of saturated vapor at a given temperature [C]."""
        T_kelvin = T_celsius + 273.15
        return CP.PropsSI('H', 'T', T_kelvin, 'Q', 1, self.fluid)

    def get_entropy_saturated_vapor(self, T_celsius):
        """Returns the entropy [J/kgK] of saturated vapor at a given temperature [C]."""
        T_kelvin = T_celsius + 273.15
        return CP.PropsSI('S', 'T', T_kelvin, 'Q', 1, self.fluid)

    def get_enthalpy_from_pressure_and_entropy(self, P_pa, s_val):
        """Returns the enthalpy [J/kg] for a given pressure [Pa] and entropy [J/kgK]."""
        return CP.PropsSI('H', 'P', P_pa, 'S', s_val, self.fluid)

    def get_enthalpy_superheated(self, P_pa, T_celsius):
        """Returns the enthalpy [J/kg] of superheated vapor at given pressure [Pa] and temperature [C]."""
        T_kelvin = T_celsius + 273.15
        return CP.PropsSI('H', 'P', P_pa, 'T', T_kelvin, self.fluid)

    def get_temperature_from_pressure(self, P_pa):
        """Returns the saturation temperature [C] for a given pressure [Pa]."""
        T_kelvin = CP.PropsSI('T', 'P', P_pa, 'Q', 0, self.fluid)
        return T_kelvin - 273.15

if __name__ == "__main__":
    # Sanity Check: Verify R134a properties against standard expectations
    # At ~25C, Psat should be around 6.6 bar (660,000 Pa)
    ref = RefrigerantProperties("R134a")
    test_t = 25.0
    p_sat = ref.get_saturation_pressure(test_t)
    h_liq = ref.get_enthalpy_saturated_liquid(test_t)
    h_vap = ref.get_enthalpy_saturated_vapor(test_t)

    print(f"--- R134a Sanity Check at {test_t}C ---")
    print(f"Saturation Pressure: {p_sat/1e5:.2f} bar")
    print(f"Saturated Liquid Enthalpy: {h_liq/1000:.2f} kJ/kg")
    print(f"Saturated Vapor Enthalpy: {h_vap/1000:.2f} kJ/kg")
    print(f"Latent Heat (h_fg): {(h_vap - h_liq)/1000:.2f} kJ/kg")
