
<p align="center">
  <img src="images/ZephyrLOGO.svg" width="280" alt="Zephyr Logo"/>
</p>

<h1 align="center">Zephyr</h1>

<p align="center">
  <strong>Satellite Assisted Hyperlocal Air Quality Reconstruction</strong>
</p>

<p align="center">
  An environmental monitoring and research project combining ground level sensor data with satellite observations to investigate and reconstruct hyperlocal PM2.5 pollution patterns.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/ESP32-orange?style=flat-square" alt="ESP32"/>
  <img src="https://img.shields.io/badge/PMS5003-blue?style=flat-square" alt="PMS5003"/>
  <img src="https://img.shields.io/badge/AIR_QUALITY-2ea44f?style=flat-square" alt="Air Quality"/>
  <img src="https://img.shields.io/badge/SATELLITE_%2B_GROUND-purple?style=flat-square" alt="Satellite + Ground"/>
</p>

---


Can a sparse network of low cost ground sensors, fused with freely available satellite aerosol data, reconstruct accurate hyperlocal (street by street) air pollution levels — outperforming both "nearest official station" estimates and ground sensors alone? 

[<video src="https://githubusercontent.com" controls autoplay muted loop width="100%"></video>](https://github.com/user-attachments/assets/357be0b4-d9a9-4513-a550-b56602abb73d)

---

## Overview 

Zephyr collects ground level particulate matter and environmental readings to support research into estimating PM2.5 pollution in areas with sparse monitoring coverage. Zephyr aims to address the challenges of urban air pollution by making hyperlocal air quality insights more accessible and actionable. By combining ground level sensor measurements with satellite derived data, the project seeks to identify pollution patterns that conventional monitoring networks may overlook. 

<table>
  <tr>
    <td align="center">
      <img src="images/Zephyr_IRL_1.jpeg" width="400">
    </td>
    <td align="center">
      <img src="images/Zephyr_IRL_2.jpeg" width="400">
    </td>
  </tr>
</table>

---

## Research Workflow

> **Detailed Research Journal:** For the complete development history, experimental logs, methodology, and progress documentation, refer to the [Zephyr Research Journal](https://docs.google.com/document/d/1UNnaVMcwHacSM3fK-nPlUQ8PDllBp77jAxlY4db8Qwo/edit?tab=t.0).


Zephyr investigates **satellite assisted reconstruction of hyperlocal PM2.5 concentration fields** by integrating sparse ground level observations from CPCB Continuous Ambient Air Quality Monitoring Stations (CAAQMS) with satellite derived atmospheric data from Sentinel-5P.

The workflow encompasses geospatial preprocessing, spatiotemporal data alignment, ground-station coverage analysis, meteorological feature integration, and diffusion based reconstruction of urban pollution fields. Model evaluation focuses on spatial generalization and quantitative validation against suitable ground-level reference measurements, using metrics such as MAE, RMSE, and \(R^2\).

The objective is to investigate whether multi source data fusion can improve the spatial resolution of air quality estimates in areas underserved by conventional monitoring networks.

<table>
  <tr>
    <td align="center">
      <img src="images/Research_1.png" width="400">
    </td>
    <td align="center">
      <img src="images/Research_2.png" width="400">
    </td>
  </tr>
</table>

---

## PCB and Hardware

Zephyr integrates **embedded systems engineering and environmental sensing** into a portable air quality monitoring platform built around the ESP32. The system combines particulate matter, meteorological, gas sensing, and GPS modules for localized environmental data acquisition.

The custom PCB design process uses **KiCad based electronic design automation (EDA)**, incorporating schematic capture, component layout, power distribution, and design rule verification. Firmware driven sensor interfacing and microSD based CSV logging support field data collection for subsequent geospatial analysis.

### Core Components

- **ESP32:** Embedded processing and sensor interfacing.
- **PMS5003:** PM1.0, PM2.5, and PM10 measurements.
- **AHT20 + BMP180:** Temperature, humidity, and atmospheric pressure.
- **MQ135:** Analog gas sensor readings.
- **GPS + microSD:** Geospatial tagging and local data logging.
- **Battery and voltage regulation:** Portable power delivery.

<p align="center">
  <img src="images/PCB_ZOOMIN.png" width="700">
</p>

<p align="center">
  <img src="images/Zephyr_Schematic.png" width="700">
</p>



