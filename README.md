# fungal_germination_identification
Functions that use data output from real-time imaging to identify germination and then derive hyphal growth rates of filamentous fungi. Designed using the oCelloScope imager (BioSense Solutions). 

## Overview




## Repository Structure

```text
├── Python/
│   ├── Functions_Python.py
│   └── Example A canadensis - Python.ipynb
│
├── R_Script/
│   ├── Functions_R_Script.R
│   └── Example A canadensis - R Script.Rmd
│
├── Example Data/
│   └── 6 excell files from A. canadensis in both MY70 and CY20 media triplicate wells (oCelloScope data that will not be included in a paper)
│
├── LICENSE/
│
└── README.md/
```

## Input Data
* Excell files from oCelloScope Segmentation+Object Track
  * Functions will work on other data formats as long as the imported data is similarly structured.
 
## Workflow
1. Run Segmentation + Object Track modules on video
2. Perform quality control and filtering to verify that no debris or sugar crystals have been misidentified
3. Export to Excel files.
4. Run Excel through a workflow similar to the examples to quantify isotropic swelling (isotropic_growth), germination timepoint (find_time_point), and hyphal growth rates (length_post_germination).

## Installation
### Python Dependencies
```bash
import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.formula.api as smf
import sys
import re
import requests
import os
import importlib.util
from pathlib import Path
```

### R Dependencies
```{r}
library(readxl)
library(dplyr)
library(tidyverse)
library(ggplot2)
library(ggpubr)
library(knitr)
library(kableExtra)
library(RColorBrewer)
library(segmented)
library(nortest)
library(car)
library(drc)

#IMPORTANT NOTE
#segmented package interferes with dplyr::select 
```
## Usage
### Python
```bash
import os

#clone repository on you working directory 
!git clone https://github.com/NFA-NRCWE/fungal_germination_identification/Python.git
sys.path.append("fungal_germination_identification")

#import functions as germ_functions
import Functions_Python as germ_function
```

### R
```{r}
download.file("https://raw.githubusercontent.com/NFA-NRCWE/fungal_germination_identification/main/R_Script/Functions_R_Script.R",  "Germination Functions.R", mode = "wb")

#run functions script to load fucntions into global environment
source("Germination Functions.R")
```
## Outputs

## Methods
### Isotropic Growth
Isotropic growth is determined using segmented linear regressions on conidia area over time. The breakpoint (or hinge point) is the moment when the initial linear regression stops being significantly correlated with the initial linear regression, which is inferred as the transition from isotropic growth to polarized growth. The isoropic_growth function returns plots of all conidia that increased in area at least 2.5X over the experimental window with segmented regressions and a summary dataframe containing Average_Swelling_change, Average_Breakpoint_Time, Average_Breakpoint_Area, and Average_First_Area.

### Gemination  Identification
The germination identification function (find_time_point) runs through individual conidia (identified by TrackId) to identify the image frame in which germination tube formation initiates. This function uses the Average_Swelling_change (multiplied by 1.25x to limit false positives) derived from the isotropic growth analysis, alongside a decrease in circularity below 0.94 to systematically identify germination. This function returns a data frame with the germination time point identified for every tracked conidia (selected_time_point), and derives the hypheal growth rate (linear_growth_rate and exponential_growth_rate). Ungerminated conidia metrics are returned as NA.

### Hyphal Growth
Image data is reformatted using the germination time point as the new relative time 0, and the total length of conidia is tracked over time. Both exponential and linear growth models are derived from the new relative data. The function length_post_germination returns a data frame with the relative_time and lengths of all germinated conidia with track_id as identifier, a dataframe with relative_time tracked alongside Median_Length, linear modal length predictions (lm_predicted), and exponential model length predictions (exm_predicted). This function also plots every germinated condias length over 24 hours alongside  the median length, linear model, and exponential model.

Growth rates are calculated from the change in hyphal length over time following germination. The specific implementation is described within the analysis scripts.
## Citation
Priest, K. (2026). fungal_germination_identification (Version 1.0) [Computer software]. GitHub. https://github.com/NFA-NRCWE/fungal_germination_identification

## License
Copyright (c) 2026 NFA - NRCWE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
