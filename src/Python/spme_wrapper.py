import numpy as np
import json
import pybamm

from base_wrapper import BasePybammWrapper

'''
TODO: generate pydocs describing SPM-e model and its parameters in detail
'''
class SpmePybammWrapper(BasePybammWrapper):
    def __init__(self):
        super().__init__()
        self.model_type = "SPMe"
        self.voltage_var = "Terminal voltage [V]"
        self.output_vars = [
            "Terminal voltage [V]",
            "X-averaged cell state of charge",
            "X-averaged state of charge",
            "State of Charge",
            "SoC",
            "Cell state of charge"
        ]

    def load_profile(self, chemistry: str = "Chen2020", *args, **kwargs) -> bool:
        try:
            print("Loading SPMe model...")
            self.model = pybamm.lithium_ion.SPMe()
            print(f"Loading standard parameter set '{chemistry}'...")
            self.param = pybamm.ParameterValues(chemistry)
            self.param["Current function [A]"] = pybamm.InputParameter("Current [A]")
            self.reset_simulation()
            print(f"Successfully loaded and configured model 'SPMe'.")
            return True
        except Exception as e:
            print(f"Error loading SPMe profile or model: {e}")
            self.model, self.param = None, None
            return False

    def get_ocv_soc_curve(self) -> str:
        if self.param is None:
            return json.dumps({"error": "No profile loaded."})
        try:
            soc_points = np.linspace(0, 1, 101)
            c_n_max = self.param["Maximum concentration in negative electrode [mol.m-3]"]
            c_p_max = self.param["Maximum concentration in positive electrode [mol.m-3]"]
            c_n_min = 0.0
            c_p_min = 0.0
            x_n = soc_points
            x_p = 1 - soc_points
            U_p_func = self.param["Positive electrode OCP [V]"]
            U_n_func = self.param["Negative electrode OCP [V]"]
            U_p = U_p_func(x_p)
            U_n = U_n_func(x_n)
            ocv_points = U_p - U_n
            curve_data = [[round(s * 100, 2), round(v, 4)] for s, v in zip(soc_points, np.array(ocv_points).flatten())]
            self.ocv_soc_curve = curve_data
            return json.dumps(curve_data)
        except Exception as e:
            print("Available parameter keys:", list(self.param.keys()))
            return json.dumps({"error": f"Failed to get OCV curve. Details: {type(e).__name__}: {e}"})

    def _initial_solve(self, inputs):
        initial_soc = 0.999
        self.simulation.solve([0, 1e-6], initial_soc=initial_soc, inputs=inputs)