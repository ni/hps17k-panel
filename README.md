# HPS17K Panel

This application supports v1.0.0 and v1.0.1 of the HPS-17000 API.  It provides a standalone HMI to control and validate the HPS-17000 and provide diagnostic feedback.  It was developed with LabVIEW 2023 64-bit.

- 1024x768 touch panel friendly interface
- TDMS Logging + File Viewer

### Chart

- View Measurement Stream (UDP) and gRPC (TCP) data
- Pause the live chart to zoom in and analyze waveforms
- Save the chart data to Excel for viewing later

![image](https://github.com/user-attachments/assets/6940d4d5-9274-4b74-92e5-5d75070026b5)

### Config

- Configure Single or Multi Cycler Network settings
- Search for HPS17K units on the local network
- Configure panel-specific settings for graph, logging, and profile execution

![image](https://github.com/user-attachments/assets/f98d9d36-74d9-41f8-88ad-8f0d2a0589c9)

### Control

- Manually control setpoints and toggle energization and output
- Configure cycler modes and ranges
  * High Voltage (1500V - 240A)
  * High Current (750V - 480A)
  * Internal Recirculation
  * Constant Current
  * Constant Voltage

![image](https://github.com/user-attachments/assets/6adebcfb-9788-40e5-8a06-d6bb240847e2)

Setpoint slew rates are configurable from the control tab; this is an example trace at 5V/sec voltage setpoint slew rate
![image](https://github.com/user-attachments/assets/9ef24501-0234-4a7e-a4c9-2907263a00f7)

### EIS

Configure EIS profiles to be executed on the cycler.  After execution is complete, generate corresponding nyquist and bode plots to analyze impedance data.

![image](https://github.com/user-attachments/assets/af02c34d-addf-4634-bd90-bbd8897e761d)


### Diagnostics

Diagnose issues with the HPS17K and view additional information from the cycler.

- Launch the Volta Monitor script to view additional HPS17K information
- Launch the FC Sys Inspect script to view PMSIC device health information
- Get the XC Report from the HPS17K for a comprehensive report of system health
- Launch the TDMS File Viewer to view saved log files for machines without DIAdem available

![image](https://github.com/user-attachments/assets/1f0528a9-4ee1-4598-985b-cc7304b9f135)


### Self-Test

Run the test server and self-test scripts on the HPS17K.

- Run the self test with or without the capacitor voltage reforming procedure

![image](https://github.com/user-attachments/assets/4ecb04e3-e0db-4ab0-b3ac-600ee7c66853)


### System

View system hardware limits, temperatures, and thermal limits of the system (read-only).

![image](https://github.com/user-attachments/assets/8f452172-f104-4589-b4ec-e32312333cb1)

