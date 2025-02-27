# scripts/utils/thermal_conductivity.py
def slack_thermal_conductivity(element):
    """Estimate thermal conductivity using Slack's equation (MUY simplificado)."""
    try:
        debye_temp = element.debye_temperature
        resistivity = element.electrical_resistivity
        return 0.01 * resistivity * debye_temp**2
    except AttributeError:
        return None