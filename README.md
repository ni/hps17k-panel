# HPS-17000 Panel

This application supports v1.0.1 of the HPS-17000 API.  It provides a standalone HMI to control and validate the HPS-17000 and provide diagnostic feedback.  It was developed with LabVIEW 2023 64-bit.

- 1024x768 touch panel friendly interface
- Support Single or Multiple Cycler Topology
- TDMS Logging + File Viewer
- EIS Testing and Report Generation

## Chart

- View Measurement Stream (UDP / High Speed) and gRPC (TCP / Low Speed) data
- Pause the live chart to zoom in and analyze waveforms
- Save the chart data to Excel for viewing later

![image](https://github.com/user-attachments/assets/43ee1f2a-eb1e-4391-90ea-55660fe47c4e)

## Config

- Configure Single or Multi Cycler Network settings
- Search for HPS17K units on the local network
- Configure panel-specific settings for graph, logging, and profile execution

![image](https://github.com/user-attachments/assets/09c9a0c1-04c2-49cd-afab-a3d748701ee3)

## Control

- Manually control setpoints and toggle energization and output
- Configure cycler modes and ranges
  * High Voltage (1500V - 240A)
  * High Current (750V - 480A)
  * Internal Recirculation
  * Constant Current
  * Constant Voltage

![image](https://github.com/user-attachments/assets/6adebcfb-9788-40e5-8a06-d6bb240847e2)

## Diagnostics

Diagnose issues with the HPS17K and view additional information from the cycler.

- Launch the Volta Monitor script to view additional HPS17K information
- Launch the FC Sys Inspect script to view PMSIC device health information
- Get the XC Report from the HPS17K for a comprehensive report of system health
- Launch the TDMS File Viewer to view saved log files for machines without DIAdem/Excel installed

![image](https://github.com/user-attachments/assets/11128ab7-2bc8-4261-8951-5ff887b9f520)

## EIS

Configure EIS profiles to be executed on the cycler.  After execution is complete, generate corresponding nyquist and bode plots to analyze impedance data.

### EIS Profile View
![image](https://github.com/user-attachments/assets/d05879c5-c26c-4a53-a21b-3fa048be5b3f)

### EIS Running View
![image](https://github.com/user-attachments/assets/13dd1cdc-8c2b-4772-bbe2-6b0e7e434ba7)

### EIS Nyquist (Cole-Cole) Plot
![image](https://github.com/user-attachments/assets/88a369f2-d869-48fa-85cd-7e5e9e74992f)

### EIS Phase (Bode) Plot
![image](https://github.com/user-attachments/assets/23a8317d-dcc8-463d-a4f3-913915ed606f)

### EIS Phase (Magnitude) Plot
![image](https://github.com/user-attachments/assets/87d4ae65-3d8a-4d0a-a926-1e4ee4eeeaa4)

## Profile

Load CSV test profiles to be executed on the cycler with setpoint streams.  Test profiles are limited to 1500 steps in volta-sbrio-1.0.1 and 200 steps in volta-sbrio-1.0.0

![image](https://github.com/user-attachments/assets/10493260-29e7-463f-804b-af81bcac087f)

## Self-Test

Run the test server and self-test scripts on the HPS17K.

- Run the self test with or without the capacitor voltage reforming procedure (2 hour test)

![image](https://github.com/user-attachments/assets/8c2e001a-bb81-4f5e-9a39-ebbde35a4640)

## System

View system hardware limits, temperatures, and thermal limits of the system (read-only).

![image](https://github.com/user-attachments/assets/ab377b9c-0bce-495e-9e01-1eccf3d67521)


