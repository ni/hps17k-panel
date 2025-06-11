import pybamm
import numpy as np
import json

class PybammWrapper:
    """
    A stateful wrapper class to interface with the PyBaMM library, with robust,
    model-specific logic to correctly handle both full physics models (like SPMe)
    and equivalent circuit models (ECM).
    """
    def __init__(self):
        """Initializes the wrapper and all state variables."""
        self.model = None
        self.param = None
        self.simulation = None
        self.solution = None
        self.model_type = None
        # Store raw data for ECM model to ensure robust OCV lookup
        self.ecm_soc_data = None
        self.ecm_ocv_data = None
        self.ocv_soc_curve = None  # Will hold [[SoC, OCV], ...]
        print("PybammWrapper initialized. Please load a profile.")

    def load_profile(self, model_type: str, chemistry: str = "Chen2020", num_rc_pairs: int = 1) -> bool:
        """
        Initializes a model and its parameters using model-specific methods.
        """
        try:
            self.model_type = model_type
            if model_type == "SPMe":
                print("Loading SPMe model...")
                self.model = pybamm.lithium_ion.SPMe()
                print(f"Loading standard parameter set '{chemistry}'...")
                self.param = pybamm.ParameterValues(chemistry)
                # This is the standard way to make current a controllable input
                self.param["Current function [A]"] = pybamm.InputParameter("Current [A]")

            elif model_type == "ECM":
                print("Loading ECM (Thevenin) model...")

                self.ecm_soc_data = np.array([0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
                self.ecm_ocv_data = np.array([3.3, 3.5, 3.6, 3.65, 3.7, 3.75, 3.85, 3.95, 4.05, 4.1, 4.2])

                ecm_ocv_interpolant = pybamm.Interpolant(self.ecm_soc_data, self.ecm_ocv_data, pybamm.Variable("SoC"))
                ecm_params_to_add = {
                    "Open-circuit voltage [V]": ecm_ocv_interpolant,
                    "open-circuit potential": ecm_ocv_interpolant,
                    "R0 [Ohm]": 0.0015,
                    "Nominal cell capacity [A.h]": 5.0,
                    "Current function [A]": pybamm.InputParameter("Current [A]"),
                    "Upper voltage cut-off [V]": 4.2,
                    "Lower voltage cut-off [V]": 3.0,
                    "R1 [Ohm]": 0.001,      # <-- Correct key for RC resistance
                    "C1 [F]": 2500.0,       # <-- Correct key for RC capacitance
                }
                if num_rc_pairs == 2:
                    ecm_params_to_add.update({
                        "R2 [Ohm]": 0.0008,      # <-- Correct key for second RC resistance
                        "C2 [F]": 40000.0,       # <-- Correct key for second RC capacitance
                    })

                self.model = pybamm.equivalent_circuit.Thevenin(
                    options={"number of rc elements": num_rc_pairs}
                )
                self.param = self.model.default_parameter_values
                self.param.update(ecm_params_to_add,check_already_exists=False)

            else:
                raise ValueError(f"Model type '{model_type}' is not yet supported.")

            self.reset_simulation()
            print(f"Successfully loaded and configured model '{model_type}'.")
            return True
        except Exception as e:
            print(f"Error loading profile or model: {e}")
            self.model, self.param = None, None
            return False

    def get_ocv_soc_curve(self) -> str:
        """
        Extracts the OCV vs SOC curve using model-appropriate methods.
        """
        if self.param is None:
            return json.dumps({"error": "No profile loaded."})

        try:
            soc_points = np.linspace(0, 1, 101)

            if self.model_type == "ECM":
                ocv_points = np.interp(soc_points, self.ecm_soc_data, self.ecm_ocv_data)
            else:  # SPMe and other full physics models
                # Use concentrations to calculate stoichiometry
                c_n_max = self.param["Maximum concentration in negative electrode [mol.m-3]"]
                c_p_max = self.param["Maximum concentration in positive electrode [mol.m-3]"]
                c_n_init = self.param["Initial concentration in negative electrode [mol.m-3]"]
                c_p_init = self.param["Initial concentration in positive electrode [mol.m-3]"]

                c_n_min = 0.0
                c_p_min = 0.0

                x_n = soc_points  # For negative, stoichiometry is SoC if c_n_min=0, c_n_max=1
                x_p = 1 - soc_points  # For positive, stoichiometry is 1-SoC if c_p_min=0, c_p_max=1

                U_p_func = self.param["Positive electrode OCP [V]"]
                U_n_func = self.param["Negative electrode OCP [V]"]
                U_p = U_p_func(x_p)
                U_n = U_n_func(x_n)
                ocv_points = U_p - U_n

            curve_data = [[round(s * 100, 2), round(v, 4)] for s, v in zip(soc_points, np.array(ocv_points).flatten())]
            self.ocv_soc_curve = curve_data  # Store for interpolation
            return json.dumps(curve_data)
        except Exception as e:
            print("Available parameter keys:", list(self.param.keys()))
            return json.dumps({"error": f"Failed to get OCV curve. Details: {type(e).__name__}: {e}"})

    def get_current_voltage(self) -> float:
        """Returns the current Terminal Voltage (V) or initial OCV."""
        if self.solution:
            if self.model_type == "ECM":
                return float(self.solution["Battery voltage [V]"].entries[-1])
            else:
                return float(self.solution["Terminal voltage [V]"].entries[-1])
        if self.param is None: return 0.0

        try:
            curve_data_json = self.get_ocv_soc_curve()
            if "error" in curve_data_json: return 0.0
            curve_data = json.loads(curve_data_json)
            return float(curve_data[-1][1]) if curve_data else 0.0
        except Exception: return 0.0

    def get_current_soc(self) -> float:
        """Returns the current State of Charge (%) by interpolating from the OCV curve and terminal voltage."""
        if self.solution is None or self.ocv_soc_curve is None:
            return 100.0

        try:
            if self.model_type == "ECM":
                voltage = float(self.solution["Battery voltage [V]"].entries[-1])
            else:
                voltage = float(self.solution["Terminal voltage [V]"].entries[-1])
            socs = np.array([point[0] for point in self.ocv_soc_curve])
            ocvs = np.array([point[1] for point in self.ocv_soc_curve])

            # Sort by OCV (voltage) to ensure monotonicity for interpolation
            sort_idx = np.argsort(ocvs)
            ocvs_sorted = ocvs[sort_idx]
            socs_sorted = socs[sort_idx]

            # Clip voltage to OCV range to avoid always returning 0 or 100
            voltage_clipped = np.clip(voltage, ocvs_sorted.min(), ocvs_sorted.max())
            soc = float(np.interp(voltage_clipped, ocvs_sorted, socs_sorted))
            return soc
        except Exception as e:
            print(f"Error interpolating SoC from OCV curve: {e}")
            return -1.0

    def reset_simulation(self):
        """Resets the simulation state."""
        self.simulation = None
        self.solution = None
        print("Simulation state reset.")

    def step_simulation(self, current_A: float, time_step_s: float) -> float:
        """Steps the simulation forward."""
        if self.model is None or self.param is None: return -1.0

        try:
            inputs = {"Current [A]": current_A}

            if self.simulation is None:
                # To prevent termination events at t=0 for SPMe, slightly lower the initial SoC
                initial_soc = 0.999 if self.model_type == "SPMe" else 1.0
                # Specify output variables to ensure SoC is included
                if self.model_type == "ECM":
                    output_vars = [
                        "Battery voltage [V]",
                        "Current [A]",
                        "Open-circuit voltage [V]",
                    ]
                else:
                    output_vars = [
                        "Terminal voltage [V]",
                        "X-averaged cell state of charge",
                        "X-averaged state of charge",
                        "State of Charge",
                        "SoC",
                        "Cell state of charge"
                    ]
                self.simulation = pybamm.Simulation(
                    self.model,
                    parameter_values=self.param,
                    output_variables=output_vars
                )
                if self.model_type == "SPMe":
                    self.simulation.solve([0, 1e-6], initial_soc=initial_soc, inputs=inputs)
                else:
                    self.simulation.solve([0, 1e-6], inputs=inputs)

            self.simulation.step(dt=time_step_s, save=True, inputs=inputs)
            self.solution = self.simulation.solution

            if self.model_type == "ECM":
                return float(self.solution["Battery voltage [V]"].entries[-1])
            else:
                return float(self.solution["Terminal voltage [V]"].entries[-1])
        except Exception as e:
            print(f"Error during simulation step: {e}")
            return -1.0

# --- Example of how to use this class ---
if __name__ == '__main__':
    print("--- TESTING SPME MODEL ---")
    spme_sim = PybammWrapper()
    success = spme_sim.load_profile(model_type="SPMe")
    print(f"Profile load successful: {success}")
    print("-" * 20)
    
    if success:
        ocv_data_json = spme_sim.get_ocv_soc_curve()
        print(f"Generated OCV Curve for SPMe: {ocv_data_json}")
        print("-" * 20)
        
        print("--- Starting a simulated discharge pulse (SPMe) ---")
        discharge_current = 5.0 
        time_step_s = 60 
        
        print(f"Initial State -> Voltage: {spme_sim.get_current_voltage():.4f}V, SoC: {spme_sim.get_current_soc():.2f}%")
        
        for i in range(5):
            new_voltage = spme_sim.step_simulation(discharge_current, time_step_s)
            if new_voltage == -1.0: 
                print("Simulation failed. Aborting.")
                break
            current_soc = spme_sim.get_current_soc()
            print(f"Step {i+1} -> Voltage: {new_voltage:.4f}V, Current SoC: {current_soc:.2f}%")

    print("\n" + "="*50 + "\n")



    print("--- TESTING ECM MODEL ---")
    ecm_sim = PybammWrapper()
    success = ecm_sim.load_profile(model_type="ECM")
    print(f"Profile load successful: {success}")
    print("-" * 20)

    if success:
        ocv_data_json = ecm_sim.get_ocv_soc_curve()
        print(f"Generated OCV Curve for ECM: {ocv_data_json}")
        print("-" * 20)

        print("--- Starting a simulated discharge pulse (ECM) ---")
        discharge_current = 5.0
        time_step_s = 60
        
        print(f"Initial State -> Voltage: {ecm_sim.get_current_voltage():.4f}V, SoC: {ecm_sim.get_current_soc():.2f}%")
        
        for i in range(5):
            new_voltage = ecm_sim.step_simulation(discharge_current, time_step_s)
            if new_voltage == -1.0:
                print("Simulation failed. Aborting.")
                break
            current_soc = ecm_sim.get_current_soc()
            print(f"Step {i+1} -> Voltage: {new_voltage:.4f}V, Current SoC: {current_soc:.2f}%")
