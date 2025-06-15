import pybamm
import numpy as np
import json
import matplotlib.pyplot as plt

class PybammWrapper:
    """
    Unified PyBaMM wrapper for battery simulation.
    Provides methods to load OCV/SOC curve from a model, load a custom curve, and configure ECM simulation.
    """
    def __init__(self):
        self.model = None
        self.param = None
        self.simulation = None
        self.solution = None
        self.model_type = None
        self.soc_data = None
        self.ocv_data = None
        self.voltage_var = "Battery voltage [V]"
        self.output_vars = [
            "Battery voltage [V]",
            "Current [A]",
            "Open-circuit voltage [V]",
        ]
        print("PybammWrapper initialized.")

    def __del__(self):
        """
        Destructor to clean up resources if needed.
        """
        self.simulation = None
        self.solution = None
        self.model = None
        self.param = None
        print("PybammWrapper destroyed.")

    def generate_ocv_soc_curve(self, chemistry="Chen2020", model_type="SPMe"):
        """
        Generate OCV/SOC curve from a PyBaMM model.
        Args:
            chemistry (str): Battery chemistry/model parameter set.
            model_type (str): Model to use ("SPMe", "DFN").
        Returns:
            soc (np.ndarray), ocv (np.ndarray)
        """
        if model_type.upper() == "DFN":
            model = pybamm.lithium_ion.DFN()
        else:
            model = pybamm.lithium_ion.SPMe()
        param = pybamm.ParameterValues(chemistry)
        U_p_func = param["Positive electrode OCP [V]"]
        U_n_func = param["Negative electrode OCP [V]"]
        soc = np.linspace(0, 1, 101)
        x_n = soc
        x_p = 1 - soc
        U_p = U_p_func(x_p)
        U_n = U_n_func(x_n)
        ocv = U_p - U_n
        return soc, ocv

    def load_model(self, chemistry="Chen2020", model_type="SPMe"):
        """
        Load OCV/SOC curve from a battery model (SPMe, DFN, etc).
        """
        soc, ocv = self.generate_ocv_soc_curve(chemistry=chemistry, model_type=model_type)
        self.soc_data = soc
        self.ocv_data = ocv
        return True

    def load_ocv_soc_curve(self, soc_data, ocv_data):
        """
        Load a custom OCV/SOC curve.
        """
        self.soc_data = np.array(soc_data)
        self.ocv_data = np.array(ocv_data)
        return True

    def load_simulation(
        self,
        num_rc_pairs: int = 1,
        R0: float = 0.0015,
        R1: float = 0.001,
        C1: float = 2500.0,
        R2: float = 0.0008,
        C2: float = 40000.0,
        nominal_capacity_Ah: float = 5.0,
        upper_voltage_cutoff: float = 4.2,
        lower_voltage_cutoff: float = 3.0,
    ):
        """
        Configure ECM simulation and return model, param.
        """
        try:
            ecm_ocv_interpolant = pybamm.Interpolant(
                np.array(self.soc_data), np.array(self.ocv_data), pybamm.Variable("SoC")
            )
            ecm_params_to_add = {
                "Open-circuit voltage [V]": ecm_ocv_interpolant,
                "R0 [Ohm]": R0,
                "Nominal cell capacity [A.h]": nominal_capacity_Ah,
                "Current function [A]": pybamm.InputParameter("Current [A]"),
                "Upper voltage cut-off [V]": upper_voltage_cutoff,
                "Lower voltage cut-off [V]": lower_voltage_cutoff,
                "R1 [Ohm]": R1,
                "C1 [F]": C1,
            }
            if num_rc_pairs == 2:
                ecm_params_to_add.update({
                    "R2 [Ohm]": R2,
                    "C2 [F]": C2,
                })
            self.model = pybamm.equivalent_circuit.Thevenin(
                options={"number of rc elements": num_rc_pairs}
            )
            self.param = self.model.default_parameter_values
            self.param.update(ecm_params_to_add, check_already_exists=False)
            # Find max SoC where OCV <= upper_voltage_cutoff
            socs = np.array(self.soc_data)
            ocvs = np.array(self.ocv_data)
            valid = np.where(ocvs <= upper_voltage_cutoff)[0]
            if len(valid) == 0:
                initial_soc = float(socs[np.argmin(np.abs(ocvs - upper_voltage_cutoff))])
            else:
                initial_soc = float(socs[valid[-1]])
            self.model.initial_conditions[pybamm.Variable("SoC")] = pybamm.Scalar(initial_soc)
            self.initial_soc = initial_soc  # Store for reference
            return True
        except Exception as e:
            print(f"Error configuring ECM simulation: {e}")
            return False

    def step_simulation(self, current_A, time_step_s):
        if self.model is None or self.param is None:
            return -1.0
        if self.simulation is None:
            self.simulation = pybamm.Simulation(
                self.model,
                parameter_values=self.param,
                output_variables=self.output_vars
            )
            # Set initial SoC to 1.0 (100%)
            self.simulation.solve([0, 1e-6], inputs={"Current [A]": current_A, "SoC": 1.0})
        self.simulation.step(dt=time_step_s, save=True, inputs={"Current [A]": current_A})
        self.solution = self.simulation.solution
        return float(self.solution[self.voltage_var].entries[-1])

    def get_voltage(self):
        if self.solution:
            return float(self.solution[self.voltage_var].entries[-1])
        return 0.0

    def get_soc(self):
        if self.solution is None or self.soc_data is None or self.ocv_data is None:
            return 100.0
        try:
            voltage = float(self.solution[self.voltage_var].entries[-1])
            socs = np.array(self.soc_data) * 100
            ocvs = np.array(self.ocv_data)
            sort_idx = np.argsort(ocvs)
            ocvs_sorted = ocvs[sort_idx]
            socs_sorted = socs[sort_idx]
            voltage_clipped = np.clip(voltage, ocvs_sorted.min(), ocvs_sorted.max())
            soc = float(np.interp(voltage_clipped, ocvs_sorted, socs_sorted))
            return soc
        except Exception as e:
            print(f"Error interpolating SoC from OCV curve: {e}")
            return -1.0

    def get_soc_ocv_curve(self):
        if self.soc_data is None or self.ocv_data is None:
            return '{"error": "No OCV/SOC curve loaded."}'
        soc_points = np.linspace(0, 1, 101)
        ocv_points = np.interp(soc_points, np.array(self.soc_data), np.array(self.ocv_data))
        curve_data = [[round(s * 100, 2), round(v, 4)] for s, v in zip(soc_points, np.array(ocv_points).flatten())]
        return json.dumps(curve_data)

    def reset_simulation(self):
        self.simulation = None
        self.solution = None
        return True
    
    def get_available_chemistries(self):
        """
        Query available chemistries from PyBaMM.
        Returns:
            list: List of available chemistry names.
        """
        chemistries = []
        try:
            chemistries = list(pybamm.parameter_sets)
        except Exception:
            pass
        return chemistries

    def get_available_models(self):
        """
        Query available model types from PyBaMM.
        Returns:
            list: List of available model type names.
        """
        models = []
        try:
            models = [
                attr for attr in dir(pybamm.lithium_ion)
                if not attr.startswith("_")
                and isinstance(getattr(pybamm.lithium_ion, attr), type)
            ]
        except Exception:
            pass
        return models
    

def create():
    """
    Factory function to create a PybammWrapper instance.
    Returns:
        PybammWrapper: A new instance of the wrapper.
    """
    return PybammWrapper()

def destroy(obj):
    """
    Destroys a PybammWrapper instance.
    Args:
        obj (PybammWrapper): The instance to destroy.
    """
    del obj

def load_model(
    obj, 
    chemistry="Chen2020", 
    model_type="SPMe"
):
    """
    Expose load_model for LabVIEW.
    """
    return obj.load_model(
        chemistry=chemistry, 
        model_type=model_type
    )

def load_soc_ocv_curve(obj, soc_data, ocv_data):
    """
    Expose load_soc_ocv_curve for LabVIEW.
    """
    return obj.load_soc_ocv_curve(soc_data, ocv_data)

def load_simulation(
    obj,
    num_rc_pairs=1,
    R0=0.0015,
    R1=0.001,
    C1=2500.0,
    R2=0.0008,
    C2=40000.0,
    nominal_capacity_Ah=5.0,
    upper_voltage_cutoff=4.2,
    lower_voltage_cutoff=3.0,
    **kwargs
):
    """
    Expose load_simulation for LabVIEW.
    """
    return obj.load_simulation(
        num_rc_pairs=num_rc_pairs,
        R0=R0,
        R1=R1,
        C1=C1,
        R2=R2,
        C2=C2,
        nominal_capacity_Ah=nominal_capacity_Ah,
        upper_voltage_cutoff=upper_voltage_cutoff,
        lower_voltage_cutoff=lower_voltage_cutoff,
        **kwargs
    )

def step_simulation(obj, current_A, time_step_s):
    """
    Expose step_simulation for LabVIEW.
    """
    return obj.step_simulation(current_A, time_step_s)

def get_voltage(obj):
    """
    Expose get_voltage for LabVIEW.
    """
    return obj.get_voltage()

def get_soc(obj):
    """
    Expose get_soc for LabVIEW.
    """
    return obj.get_soc()

def get_soc_ocv_curve(obj):
    """
    Expose get_soc_ocv_curve for LabVIEW.
    """
    return obj.get_soc_ocv_curve()

def reset_simulation(obj):
    """
    Expose reset_simulation for LabVIEW.
    """
    return obj.reset_simulation()

def run_simulation(obj, current_profile, time_step_s):
    """
    Expose run_simulation for LabVIEW.
    Args:
        obj (PybammWrapper): The simulation object.
        current_profile (list): List of current values (A).
        time_step_s (float): Time step for each current value (s).
    Returns:
        list: List of voltage values after each step.
    """
    return obj.run_simulation(current_profile, time_step_s)

def get_available_chemistries(obj):
    """
    Expose get_available_chemistries for LabVIEW or external use.
    If obj is provided, calls the method on the instance; otherwise, uses a temporary instance.
    """
    return PybammWrapper().get_available_chemistries()

def get_available_models(obj):
    """
    Expose get_available_models for LabVIEW or external use.
    If obj is provided, calls the method on the instance; otherwise, uses a temporary instance.
    """
    return PybammWrapper().get_available_models()

# Example usage from Python only
if __name__ == '__main__':
    print("--- TESTING UNIFIED PYBAMM WRAPPER ---")
    wrapper = PybammWrapper()
    print("Loading OCV/SOC curve from SPMe model...")
    success = wrapper.load_model(chemistry="Chen2020", model_type="SPMe")
    print(f"SOC/OCV curve load successful: {success}")
    print("-" * 20)

    print("Configuring ECM simulation...")
    sim_success = wrapper.load_simulation()
    print(f"Simulation config successful: {sim_success}")
    print("-" * 20)

    if success and sim_success:
        ocv_data_json = wrapper.get_soc_ocv_curve()
        print(f"Generated OCV Curve: {ocv_data_json}")
        print("-" * 20)

        print("--- Starting a simulated discharge pulse ---")
        discharge_current = 5.0
        time_step_s = 60

        print(f"Initial State -> Voltage: {wrapper.get_voltage():.4f}V, SoC: {wrapper.get_soc():.2f}%")

        for i in range(5):
            new_voltage = wrapper.step_simulation(discharge_current, time_step_s)
            if new_voltage == -1.0:
                print("Simulation failed. Aborting.")
                break
            current_soc = wrapper.get_soc()
            print(f"Step {i+1} -> Voltage: {new_voltage:.4f}V, Current SoC: {current_soc:.2f}%")

