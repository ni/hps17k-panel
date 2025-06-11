'''
TODO: author docs?
TODO: high level usage documentation for this module
'''

from spme_wrapper import SpmePybammWrapper
from ecm_wrapper import EcmPybammWrapper

def create_spme():
    """
    Create and return a new SPMe simulation object.

    Returns:
        SpmePybammWrapper: A new SPMe simulation object.
    """
    return SpmePybammWrapper()

def create_ecm():
    """
    Create and return a new ECM simulation object.

    Returns:
        EcmPybammWrapper: A new ECM simulation object.
    """
    return EcmPybammWrapper()

def spme_load_profile(obj, chemistry="Chen2020"):
    """
    Load SPMe profile.

    Args:
        obj (SpmePybammWrapper): The SPMe simulation object.
        chemistry (str): The PyBaMM parameter set to use (default: "Chen2020").

    Returns:
        bool: True if successful, False otherwise.
    """
    return obj.load_profile(chemistry=chemistry)

def ecm_load_profile(obj, **kwargs):
    """
    Load ECM profile.

    Args:
        obj (EcmPybammWrapper): The ECM simulation object.
        **kwargs: The following keyword arguments are accepted:
            num_rc_pairs (int): Number of RC pairs (default: 1).
            R0 (float): Series resistance in Ohms (default: 0.0015).
            R1 (float): First RC pair resistance in Ohms (default: 0.001).
            C1 (float): First RC pair capacitance in Farads (default: 2500.0).
            R2 (float): Second RC pair resistance in Ohms (default: 0.0008, used if num_rc_pairs==2).
            C2 (float): Second RC pair capacitance in Farads (default: 40000.0, used if num_rc_pairs==2).
            nominal_capacity_Ah (float): Nominal cell capacity in Ah (default: 5.0).
            upper_voltage_cutoff (float): Upper voltage cutoff in V (default: 4.2).
            lower_voltage_cutoff (float): Lower voltage cutoff in V (default: 3.0).
            ocv_min (float): OCV at 0% SoC in V (default: 3.3).
            ocv_max (float): OCV at 100% SoC in V (default: 4.2).
            ecm_soc_data (np.ndarray or list): Optional custom SoC array for OCV curve.
            ecm_ocv_data (np.ndarray or list): Optional custom OCV array for OCV curve.

    Returns:
        bool: True if successful, False otherwise.
    """
    return obj.load_profile(**kwargs)

def step_simulation(obj, current_A, time_step_s):
    """
    Step simulation and return new voltage.

    Args:
        obj: The simulation object (SPMe or ECM).
        current_A (float): Current in Amperes (positive for discharge).
        time_step_s (float): Time step in seconds.

    Returns:
        float: New terminal/battery voltage after the step.
    """
    return obj.step_simulation(current_A, time_step_s)

def get_voltage(obj):
    """
    Get current voltage.

    Args:
        obj: The simulation object.

    Returns:
        float: Current terminal/battery voltage.
    """
    return obj.get_current_voltage()

def get_soc(obj):
    """
    Get current state of charge.

    Args:
        obj: The simulation object.

    Returns:
        float: Current state of charge (%).
    """
    return obj.get_current_soc()

def get_ocv_curve(obj):
    """
    Get OCV vs SoC curve as JSON string.

    Args:
        obj: The simulation object.

    Returns:
        str: JSON string of [[SoC %, OCV], ...] pairs.
    """
    return obj.get_ocv_soc_curve()

def reset_simulation(obj):
    """
    Reset the simulation state.

    Args:
        obj: The simulation object.

    Returns:
        bool: Always True.
    """
    obj.reset_simulation()
    return True

'''

TODO: add documentation for the main function, indicate it only runs from python directly (not LabVIEW)

'''
if __name__ == '__main__':
    print("--- TESTING SPME MODEL ---")
    spme_sim = create_spme()
    success = spme_load_profile(spme_sim)
    print(f"Profile load successful: {success}")
    print("-" * 20)

    if success:
        ocv_data_json = get_ocv_curve(spme_sim)
        print(f"Generated OCV Curve for SPMe: {ocv_data_json}")
        print("-" * 20)

        print("--- Starting a simulated discharge pulse (SPMe) ---")
        discharge_current = 5.0
        time_step_s = 60

        print(f"Initial State -> Voltage: {get_voltage(spme_sim):.4f}V, SoC: {get_soc(spme_sim):.2f}%")

        for i in range(5):
            new_voltage = step_simulation(spme_sim, discharge_current, time_step_s)
            if new_voltage == -1.0:
                print("Simulation failed. Aborting.")
                break
            current_soc = get_soc(spme_sim)
            print(f"Step {i+1} -> Voltage: {new_voltage:.4f}V, Current SoC: {current_soc:.2f}%")

    print("\n" + "="*50 + "\n")

    print("--- TESTING ECM MODEL ---")
    ecm_sim = create_ecm()
    success = ecm_load_profile(ecm_sim)
    print(f"Profile load successful: {success}")
    print("-" * 20)

    if success:
        ocv_data_json = get_ocv_curve(ecm_sim)
        print(f"Generated OCV Curve for ECM: {ocv_data_json}")
        print("-" * 20)

        print("--- Starting a simulated discharge pulse (ECM) ---")
        discharge_current = 5.0
        time_step_s = 60

        print(f"Initial State -> Voltage: {get_voltage(ecm_sim):.4f}V, SoC: {get_soc(ecm_sim):.2f}%")

        for i in range(5):
            new_voltage = step_simulation(ecm_sim, discharge_current, time_step_s)
            if new_voltage == -1.0:
                print("Simulation failed. Aborting.")
                break
            current_soc = get_soc(ecm_sim)
            print(f"Step {i+1} -> Voltage: {new_voltage:.4f}V, Current SoC: {current_soc:.2f}%")
