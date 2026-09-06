# Ground Station Data

This directory contains the ground based PM2.5 monitoring data used
for the hyperlocal PM2.5 reconstruction project, Zephyr!

## Source

The station datasets were obtained from the Pune Hourly Air Quality
Reports collection maintained by OpenCity, with the underlying source
identified as the Central Pollution Control Board (CPCB) air quality
data repository.

Source:
https://data.opencity.in/dataset/pune-hourly-air-quality-reports

Underlying CPCB source:
https://airquality.cpcb.gov.in/ccr/#/caaqm-dashboard-all/caaqm-landing/caaqm-data-repository

## Raw Data

The `raw/` directory contains station CSV files preserved in their
downloaded form.

Raw files are not modified.

## Processing

Processed datasets and derived statistics will be generated separately
from the raw files. No missing-value imputation or other transformation
will be applied to the raw files.
