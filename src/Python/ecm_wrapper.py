import numpy as np
import json
import pybamm

from base_wrapper import BasePybammWrapper

'''
TODO: generate pydocs describing SPM-e model and its parameters in detail
'''
class EcmPybammWrapper(BasePybammWrapper):
    def __init__(self):
        super().__init__()
        self.model_type = "ECM"
        self.voltage_var = "Battery voltage [V]"
        self.output_vars = [
            "Battery voltage [V]",
            "Current [A]",
            "Open-circuit voltage [V]",
        ]
        self.ecm_soc_data = None
        self.ecm_ocv_data = None

    def load_profile(
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
        ocv_min: float = 3.3,
        ocv_max: float = 4.2,
        ecm_soc_data: np.ndarray = None,
        ecm_ocv_data: np.ndarray = None,
        *args, **kwargs
    ) -> bool:
        try:
            print("Loading ECM (Thevenin) model...")

            # Use user-provided OCV curve if given, else generate linear
            if ecm_soc_data is not None and ecm_ocv_data is not None:
                self.ecm_soc_data = np.array(ecm_soc_data)
                self.ecm_ocv_data = np.array(ecm_ocv_data)
            else:
                self.ecm_soc_data = np.linspace(0, 1, 11)
                self.ecm_ocv_data = np.linspace(ocv_min, ocv_max, 11)

            ecm_ocv_interpolant = pybamm.Interpolant(
                self.ecm_soc_data, self.ecm_ocv_data, pybamm.Variable("SoC")
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
            self.reset_simulation()
            print(f"Successfully loaded and configured model 'ECM'.")
            return True
        except Exception as e:
            print(f"Error loading ECM profile or model: {e}")
            self.model, self.param = None, None
            return False

    def get_ocv_soc_curve(self) -> str:
        if self.param is None:
            return json.dumps({"error": "No profile loaded."})
        try:
            soc_points = np.linspace(0, 1, 101)
            ocv_points = np.interp(soc_points, self.ecm_soc_data, self.ecm_ocv_data)
            curve_data = [[round(s * 100, 2), round(v, 4)] for s, v in zip(soc_points, np.array(ocv_points).flatten())]
            self.ocv_soc_curve = curve_data
            return json.dumps(curve_data)
        except Exception as e:
            print("Available parameter keys:", list(self.param.keys()))
            return json.dumps({"error": f"Failed to get OCV curve. Details: {type(e).__name__}: {e}"})