import matplotlib.pyplot as plt
import json
import numpy as np
import pybamm

'''
TODO: add pydocs describing the base wrapper class and its methods
'''
class BasePybammWrapper:
    def __init__(self):
        self.model = None
        self.param = None
        self.simulation = None
        self.solution = None
        self.model_type = None
        self.ocv_soc_curve = None

    def load_profile(self, *args, **kwargs):
        raise NotImplementedError

    def get_ocv_soc_curve(self) -> str:
        raise NotImplementedError

    def get_current_voltage(self) -> float:
        if self.solution:
            return float(self.solution[self.voltage_var].entries[-1])
        if self.param is None:
            return 0.0
        try:
            curve_data_json = self.get_ocv_soc_curve()
            if "error" in curve_data_json:
                return 0.0
            curve_data = json.loads(curve_data_json)
            return float(curve_data[-1][1]) if curve_data else 0.0
        except Exception:
            return 0.0

    def get_current_soc(self) -> float:
        if self.solution is None or self.ocv_soc_curve is None:
            return 100.0
        try:
            voltage = float(self.solution[self.voltage_var].entries[-1])
            socs = np.array([point[0] for point in self.ocv_soc_curve])
            ocvs = np.array([point[1] for point in self.ocv_soc_curve])
            sort_idx = np.argsort(ocvs)
            ocvs_sorted = ocvs[sort_idx]
            socs_sorted = socs[sort_idx]
            voltage_clipped = np.clip(voltage, ocvs_sorted.min(), ocvs_sorted.max())
            soc = float(np.interp(voltage_clipped, ocvs_sorted, socs_sorted))
            return soc
        except Exception as e:
            print(f"Error interpolating SoC from OCV curve: {e}")
            return -1.0

    def reset_simulation(self):
        self.simulation = None
        self.solution = None
        print("Simulation state reset.")

    def step_simulation(self, current_A: float, time_step_s: float) -> float:
        if self.model is None or self.param is None:
            return -1.0
        try:
            inputs = {"Current [A]": current_A}
            if self.simulation is None:
                self.simulation = pybamm.Simulation(
                    self.model,
                    parameter_values=self.param,
                    output_variables=self.output_vars
                )
                self._initial_solve(inputs)
            self.simulation.step(dt=time_step_s, save=True, inputs=inputs)
            self.solution = self.simulation.solution
            return float(self.solution[self.voltage_var].entries[-1])
        except Exception as e:
            print(f"Error during simulation step: {e}")
            return -1.0

    def _initial_solve(self, inputs):
        # To be overridden if needed
        self.simulation.solve([0, 1e-6], inputs=inputs)

    def plot_results(self):
        """Plot voltage and SoC vs. time using matplotlib."""
        if self.solution is None:
            print("No simulation results to plot.")
            return

        t = self.solution["Time [s]"].entries
        voltage = self.solution[self.voltage_var].entries

        plt.figure(figsize=(10, 5))
        plt.subplot(2, 1, 1)
        plt.plot(t, voltage, label="Voltage")
        plt.ylabel("Voltage [V]")
        plt.title(f"{self.model_type} Simulation Results")
        plt.grid(True)
        plt.legend()

        # Try to plot SoC if available
        soc_var = None
        for candidate in [
            "X-averaged cell state of charge",
            "X-averaged state of charge",
            "State of Charge",
            "SoC",
            "Cell state of charge"
        ]:
            if candidate in self.solution._variables:
                soc_var = candidate
                break

        if soc_var:
            soc = self.solution[soc_var].entries
            plt.subplot(2, 1, 2)
            plt.plot(t, soc, label="SoC", color="orange")
            plt.ylabel("SoC")
            plt.xlabel("Time [s]")
            plt.grid(True)
            plt.legend()
        else:
            plt.subplot(2, 1, 2)
            plt.text(0.5, 0.5, "SoC not available", ha='center', va='center')
            plt.axis('off')

        plt.tight_layout()
        plt.show()
