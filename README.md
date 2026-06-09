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
* Germination time estimates
* Hyphal growth rate calculations
* Summary tables

## Workflow

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
```segmented``` package interferres with ```dplyr::select```

```
## Usage
### Python
```bash
import os

#clone repository on you working directory 
!git clone https://github.com/NFA-NRCWE/fungal_germination_identification.git
sys.path.append("fungal_germination_identification")

#import functions as germ_functions
import Functions_Python as germ_function
```

### R
```{r}
download.file("https://raw.githubusercontent.com/NFA-NRCWE/fungal_germination_identification/main/Functions_R_Script.R",  "Germination Functions.R", mode = "wb")

#run functions script to load fucntions into global environment
source("Germination Functions.R")
```
## Outputs

## Methods

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
