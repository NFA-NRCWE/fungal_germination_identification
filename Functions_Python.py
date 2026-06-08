import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.formula.api as smf
import sys
import re

#Test data set
test_df = pd.DataFrame({
    "ScanArea": ["test data frame"] * 16,
    "TrackId": ["A","A","A","A",
                "B","B","B","B",
                "C","C","C","C",
                "D","D","D","D"],
    
    "sheet_name": [
        "Circularity", "Area (um2)", "TotalLength (um)", "LongestPath (um)",
        "Circularity", "Area (um2)", "TotalLength (um)", "LongestPath (um)",
        "Circularity", "Area (um2)", "TotalLength (um)", "LongestPath (um)",
        "Circularity", "Area (um2)", "TotalLength (um)", "LongestPath (um)"
    ],

    "Repetition_0": [0.99, 60, 20, 21, 0.97, 40, 30, 31, 0.99, 55, 20, 21, np.nan, np.nan, np.nan, np.nan],
    "Repetition_1": [0.98, 70, 25, 26, 0.96, 160, 35, 36, 0.94, 85, 35, 36, np.nan, np.nan, np.nan, np.nan],
    "Repetition_2": [0.94, 120, 30, 31, 0.95, 170, 40, 41, 0.90, 105, 45, 46, 0.96, 60, 30, 31],
    "Repetition_3": [0.93, 130, 35, 36, 0.94, 190, 50, 51, 0.89, 115, 55, 56, 0.92, 125, 45, 46],
    "Repetition_4": [0.93, 130, 45, 36, 0.94, 190, 50, 51, 0.89, 115, 55, 56, 0.92, 125, 45, 46],
})

def combine_excel_sheets(file_path):
    """
    #load and combine all sheets except 'Job Configuration' because it contains non relevant information
    
    Parameters
    ----------
    file_path : filepath to data output from oCelloScope Object Tracking Module (EXCELL ONLY)

    Returns
    -------
        pandas.DataFrame with all datasheets stacked together with a new column (sheet_name) to define the data type
    """   
    
        
    # Load Excel file
    xls = pd.ExcelFile(file_path)
    
    # Get all sheet names
    sheet_names = xls.sheet_names
    
    # Remove "Job Configuration" sheets (case-insensitive, this mattered on one excell)
    sheet_names = [
        s for s in sheet_names
        if "job configuration" not in s.lower()
    ]
    
    all_data = []
    
    # Loop over each sheet
    for sheet in sheet_names:
        sheet_data = pd.read_excel(file_path, sheet_name=sheet)
        
        # Only select relevant columns:
            # ScanArea, TrackId, and Time defining columns (containing "Repetition")
        repetition_cols = [col for col in sheet_data.columns if "Repetition" in col]

        #Change order of columns
        selected_cols = ["ScanArea", "TrackId"] + repetition_cols
        
        # Keep only columns that actually exist (avoids errors)
        selected_cols = [col for col in selected_cols if col in sheet_data.columns]
        
        sheet_data_filtered = sheet_data[selected_cols].copy()
        
        # Add sheet name column to later be able to differentiate data origin
        sheet_data_filtered["sheet_name"] = sheet
        
        # Reorder columns
        cols = ["ScanArea", "TrackId", "sheet_name"] + [
            col for col in sheet_data_filtered.columns
            if col not in ["ScanArea", "TrackId", "sheet_name"]
        ]
        sheet_data_filtered = sheet_data_filtered[cols]
        
        # Append to list
        all_data.append(sheet_data_filtered)
    
    # Combine all sheets into one pd.DataFrame
    combined_data = pd.concat(all_data, ignore_index=True)
    
    return combined_data

def rename_repetition_columns(df):
    """
    In the original data frame, "Repetition X" doesn't correspond to the actual time 
    For further analysis, Repetition X must correspond to time
    This function changes Repetition X to match my time since the experiment initiated:
        imaged every 4 hours for the first 20 hours and then imaged every 2 hours for the next 76 
    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe containing individual conidia data (MUST ALREADY BE CONVERTED BY combine_excel_sheets())

    Returns
    -------
        pandas.DataFrame with all Repetition columns transformed to match the hour of the experiment
    """ 

    #input checks
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    #confirm data type (sheet_name)
    required_sheets = {"Area (um2)"}
    present_sheets = set(df["sheet_name"].dropna().unique())

    missing_sheets = required_sheets - present_sheets
    if missing_sheets:
        raise ValueError(f"df is missing required sheet_name data types: {missing_sheets}")

    #Start time at 0 hours
    current_time = 0
    
    new_columns = []
    #Loop over all Repetition Columns
    for col_name in df.columns:
        #Check if column starts with "Repetition"
        if col_name.startswith("Repetition"):
            #new column name with the "current time"
            new_col_name = f"Repetition {current_time}"
            new_columns.append(new_col_name)

            #change the time: first 20 hours are 4 hours apart, the rest are 2 hours apart
            if current_time < 20:
                current_time += 4
            else:
                current_time += 2
        else:
            #dont transfomr TrackId or ScanArea
            new_columns.append(col_name)

    df.columns = new_columns
    return df

#determine the extent of istropic growth 
#imput must be include:
#oCelloScope data frame that is transformed to have data type to be saved under coulumn "sheet_name" and Repetition number corresponds to hour of experiment
#oCelloScope data must also have "TrackId" 
#species, media, and date must also be str. its important for final data sets

#return: isotropic_growth[1] or isotropic_growth[data] is a data frame
#return: isotropic_growth[2] or isotropic_growth[plot] is a plot showing segmenteted regression

def isotropic_growth(df, species, media, date):
    """
    determine the extent of isotropic growth before polarized growth

    df : pandas.DataFrame
        Input dataframe containing individual conidia data. 
        Repetition columns must match hour of the experiment
    species : str
        Species/isolate name.
    Media : str
        Growth condition testing.  (Ex: fungicide concentration, environmental conditions, temperature, water activity)
    date : str
        Experiment date. For keeping replicates separate when combining all data

    Returns
    -------
        isotropic_growth[1] or isotropic_growth["data"] pandas.DataFrame with isotropic growth metrics
        isotropic_growth[2] or isotropic_growth["plot"] is a plot showing segmenteted regression
    """    
    #input checks
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if not isinstance(species, str):
        raise TypeError("species must be a string")

    if not isinstance(media, str):
        raise TypeError("media must be a string")

    if not isinstance(date, str):
        raise TypeError("date must be a string")

    #column checks
    required_columns = {"TrackId", "sheet_name"}

    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        raise ValueError(f"df is missing required columns: {missing_cols}")

    #confirm data type (sheet_name)
    required_sheets = {"Area (um2)"}
    present_sheets = set(df["sheet_name"].dropna().unique())

    missing_sheets = required_sheets - present_sheets
    if missing_sheets:
        raise ValueError(f"df is missing required sheet_name data types: {missing_sheets}")


    
    # find repetition columns
    time_columns = [col for col in df.columns if "Repetition" in col]

    # pivot longer
    data_long = df.melt(
        id_vars=[col for col in df.columns if col not in time_columns],
        value_vars=time_columns,
        var_name="time",
        value_name="value"
    )

    data_long["time"] = (
        data_long["time"]
        .str.replace(r"[^0-9.]", "", regex=True)
        .astype(float)
    )

    # area data only
    area_data = data_long[data_long["sheet_name"] == "Area (um2)"].copy()
    
    #Label first and last ecorded areaa
    area_data["Original_Size"] = area_data.groupby("TrackId")["value"].transform("first")
    area_data["Max_Size"] = area_data.groupby("TrackId")["value"].transform("max")

    
    # remove ungerminated conidia by removing all conida that failed to grow larger than 2.5x origional
    area_data_filtered = area_data[
        area_data["Max_Size"] > 2.5 * area_data["Original_Size"]
    ].copy()
    
    #stall code if no area over no 2.5X (look at original video to confirm germination)
    if area_data_filtered.empty:
        raise ValueError("No conidia grew > 2.5x original size, likely no germination. Watch video to confirm")

    results = []
    model_rows = []

    # fit segmented regression per TrackId
    for track_id, d in area_data_filtered.groupby("TrackId"):
        d = d[["TrackId", "time", "value"]].dropna().sort_values("time").copy()
        
        #confirm there is enough time period points to make an accurate segmented regression
        if len(d) < 4:
            continue
        
        #confirm only looking at resoirded time points
        unique_times = np.sort(d["time"].unique())
        
        #list of potential breakpoints
        candidate_breaks = unique_times[1:-1]

        if len(candidate_breaks) == 0:
            continue
        
        #name initial  model values
        best_break = None
        best_model = None
        best_rss = np.inf

        x = d["time"].values
        y = d["value"].values

        for bp in candidate_breaks:
            hinge = np.maximum(0, x - bp)

            X = pd.DataFrame({
                "intercept": 1.0,
                "time": x,
                "hinge": hinge
            })

            fit = sm.OLS(y, X).fit()
            rss = np.sum(fit.resid ** 2)
            
            #only best fit metrics saved
            if rss < best_rss:
                best_rss = rss
                best_break = bp
                best_model = fit

        if best_model is None:
            continue

        #Predicted area at breakpoint using model deirved above
        bp_X = pd.DataFrame({
            "intercept": [1.0],
            "time": [best_break],
            "hinge": [0.0]
        })

        breakpoint_area = best_model.predict(bp_X)[0]
        
        #Pull inital area of conidia at first recorded time
        first_time = d["time"].min()
        first_area = d.loc[d["time"] == first_time, "value"].iloc[0]

        #append all conidia data
        results.append({
            "TrackId": track_id,
            "Breakpoint_Time": best_break,
            "Breakpoint_Area": breakpoint_area,
            "First_Area": first_area,
            "Swelling_change": breakpoint_area / first_area
        })

        pred_X = pd.DataFrame({
            "intercept": 1.0,
            "time": x,
            "hinge": np.maximum(0, x - best_break)
        })

        d["predicted"] = best_model.predict(pred_X)
        d["Breakpoint_Time"] = best_break
        model_rows.append(d)

    if not results:
        raise ValueError("No TrackId had enough valid data for segmented regression. look at video, likely no germination")

    breakpoint_values = pd.DataFrame(results)

    #model with hingepoint saved
    test_model_data = pd.concat(model_rows, ignore_index=True)

    # average of all conidia with experiemntal condition identification
    breakpoint_results = pd.DataFrame({
        "Species": [species],
        "Media": [media],
        "Date": [date],
        "Average_Breakpoint_Time": [breakpoint_values["Breakpoint_Time"].mean()],
        "Average_Breakpoint_Area": [breakpoint_values["Breakpoint_Area"].mean()],
        "Average_First_Area": [breakpoint_values["First_Area"].mean()],
        "Average_Swelling_change": [breakpoint_values["Swelling_change"].mean()]
    })

    # plot facet grid of every conidia with regression done
    g = sns.FacetGrid(
        test_model_data,
        col="TrackId",
        col_wrap=4,
        sharey=False,
        height=3
    )
    
    #add dot of time points
    g.map_dataframe(sns.scatterplot, x="time", y="value")

    #add line of line regression
    g.map_dataframe(sns.lineplot, x="time", y="predicted")

    for ax, track_id in zip(g.axes.flat, test_model_data["TrackId"].unique()):
        bp = breakpoint_values.loc[
            breakpoint_values["TrackId"] == track_id,
            "Breakpoint_Time"
        ].iloc[0]
        ax.axvline(bp, linestyle="--", color="black")

    g.set_axis_labels("Time (Hours)", "Area (μm²)")
    g.fig.suptitle(
        f"Segmented Regression with Breakpoints and Values - {species}",
        y=1.03
    )

    plt.tight_layout()

    return {
        "isotropic_data": breakpoint_results,
        "plot": g.fig
    }
  
def find_time_point(df, breakpoint_value, species, media, date):
    """
    Find the time point when germination tube formation begins based on a change in circularity and area
    
    df : pandas.DataFrame
        Input dataframe containing individual conidia data.
    breakpoint_value : float
        Extent of isotropic swelling before polarized growth (found using isotropic_growth())
    species : str
        Species/isolate name.
    Media : str
        Growth condition testing.  (Ex: fungicide concentration, environmental conditions, temperature, water activity )
    date : str
        Experiment date. For keeping replicates separate when combining all data

    Returns
    -------
    pandas.DataFrame
        Data frame with germination time (lag time) and other growth metrics.
    """     
    
    #input checks
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if not isinstance(breakpoint_value, (int, float, np.number)):
        raise TypeError("breakpoint_value must be a single numeric value (not a Series)"
                       "Try breakpoint_df.Swelling_change.iloc[0]")
        
    if not isinstance(species, str):
        raise TypeError("species must be a string")

    if not isinstance(media, str):
        raise TypeError("media must be a string")

    if not isinstance(date, str):
        raise TypeError("date must be a string")

    #column checks
    required_columns = {"TrackId", "ScanArea", "sheet_name"}

    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        raise ValueError(f"df is missing required columns: {missing_cols}")

    #confirm data type (sheet_name)
    required_sheets = {"Circularity", "Area (um2)", "TotalLength (um)"}
    present_sheets = set(df["sheet_name"].dropna().unique())

    missing_sheets = required_sheets - present_sheets
    if missing_sheets:
        raise ValueError(f"df is missing required sheet_name data types: {missing_sheets}")

    # Get time point columns containing "Repetition"
    time_cols = [col for col in df.columns if "Repetition" in col]
    
    #find Unique TrackIds
    track_ids = pd.unique(df["TrackId"])
    
    #create output lists that are as long as unique track number
    selected_time_points = [np.nan] * len(track_ids)
    last_time_points = [np.nan] * len(track_ids)
    selected_lengths = [np.nan] * len(track_ids)
    final_lengths = [np.nan] * len(track_ids)

    #confirmation window (to make sure next data points also meet germination criteria to limit false positives) 
    confirm_n = 3

    # Loop through each TrackId
    for i, track_id in enumerate(track_ids):
        track_data = df[df["TrackId"] == track_id]

        #create separate Circularity, Area, and TotalLength data
        circularity_data = track_data[track_data["sheet_name"] == "Circularity"]
        area_data = track_data[track_data["sheet_name"] == "Area (um2)"]
        length_data = track_data[track_data["sheet_name"] == "TotalLength (um)"]

        #skip na vlues
        if circularity_data.empty or area_data.empty or length_data.empty:
            continue

        #start on first row
        circularity_row = circularity_data[time_cols].iloc[0]
        area_row = area_data[time_cols].iloc[0]
        length_row = length_data[time_cols].iloc[0]

        #find first valid initial area: non-NA and between 10 and 75
        initial_area = np.nan
        for val in area_row:
            if pd.notna(val) and 10 <= val <= 75:
                initial_area = val
                break

        #find first valid initial circle: non-NA and < 0.92
        initial_circle = np.nan
        for val in circularity_row:
            if pd.notna(val) and val < 0.92:
                initial_circle = val
                break

        #find germination time point
        #check if there is valid initial area
        if pd.notna(initial_area):
            
            for j, col in enumerate(time_cols):
                current_circularity = circularity_row[col]
                current_area = area_row[col]
                #does current circularity and area data meet germination threshold , only looks at non na variables
                if pd.notna(current_circularity) and pd.notna(current_area):
                    if current_circularity < 0.94 and current_area >= (breakpoint_value * initial_area * 1.25):
                        L = len(time_cols)
                        confirmed = False
                        
                        #confirm that the next frames also satisfy the germination threshold, limit falso positives
                        #reject timepoints dont also reach threshold
                        if j + confirm_n < L:
                            confirmed = True
                            for k in range(j + 1, j + confirm_n + 1):
                                next_circ = circularity_row[time_cols[k]]
                                next_area = area_row[time_cols[k]]

                                if (
                                    pd.isna(next_circ)
                                    or pd.isna(next_area)
                                    or not (
                                        next_circ < 0.94
                                        and next_area >= (breakpoint_value * initial_area * 1.25)
                                    )
                                ):
                                    confirmed = False
                                    break
                        else:
                            #if there are less than three frames left, accept timepoint
                            confirmed = True
                            
                        #continue scanning that unique TrackId if timepoint rejected
                        if not confirmed:
                            continue
                            
                        #store timepoint germination threshold met and length at selected timepoint
                        selected_time_points[i] = col
                        selected_lengths[i] = length_row[col]
                        break

        # Find last non-NA length and corresponding time point
        final_length_found = np.nan
        for col in time_cols:
            if pd.notna(length_row[col]):
                final_length_found = length_row[col]
                last_time_points[i] = col
        
        #store final lengths
        final_lengths[i] = final_length_found

    #function to numeric time out of Repetition X: to later use for growth modeling
    def extract_numeric(value):
        if pd.isna(value):
            return np.nan
        nums = re.sub(r"[^0-9.]", "", str(value))
        return float(nums) if nums else np.nan

    #extract TrackId specific ScanArea
    scanarea_map = (
        df[["TrackId", "ScanArea"]]
        .drop_duplicates(subset=["TrackId"])
        .set_index("TrackId")["ScanArea"]
    )

    #create pd.dataframe that sores all unique TrackId germiantion metrics
    result = pd.DataFrame({
        "ScanArea": [scanarea_map.get(track_id, np.nan) for track_id in track_ids],
        "TrackId": track_ids,
        "selected_time_point": [extract_numeric(x) for x in selected_time_points],
        "selected_time_point_word": selected_time_points,
        "last_time_point": [extract_numeric(x) for x in last_time_points],
        "selected_length": selected_lengths,
        "final_length": final_lengths,
    }).drop_duplicates()

    #add experiemtnal identifiers to results data frame
    result["Species"] = species
    result["Media"] = media
    result["Date"] = date
    
    #calculate linear growth rate using fist and last lengths and time recorded germinated
    result["linear_growth_rate"] = (
        (result["final_length"] - result["selected_length"]) /
        (result["last_time_point"] - result["selected_time_point"])
    )
    #calculate exponential growth rate using fist and last lengths and time recorded germinated
    result["exponential_growth_rate"] = (
        (np.log(result["final_length"]) - np.log(result["selected_length"])) /
        (result["last_time_point"] - result["selected_time_point"])
    )

    # Reorder columns to read easier
    result = result[
        ["Species",
         "Media",
         "Date",
         "ScanArea",
         "TrackId",
         "selected_time_point",
         "selected_time_point_word",
         "last_time_point",
         "selected_length",
         "final_length",
         "linear_growth_rate",
         "exponential_growth_rate",
        ]
    ]
    return result

    
def length_post_germination(df, germination_results, species, media, date):
    """
    making a data frame/plot with the length of the individual spore and the relative time, given the point of germination found using the find_time_point function
    
    df : pandas.DataFrame
        Input data frame containing individual conidia data.
    germination_results : pandas.DataFrame
        data frame from find_time_point()
    species : str
        Species/isolate name.
    media : str
        Growth condition testing.  (Ex: fungicide concentration, environmental conditions, temperature, water activity )
    date : str
        Experiment date. For keeping replicates separate when combining all data

    Returns
    -------
        length_post_germination[1] or length_post_germination[”relative_time_df”] pandas.DataFrame length of each conidia, identified with TrackId, with time relative to germination tube formation 
        length_post_germination[2] or length_post_germination[”median_length_df”] pandas.DataFrame median length and relative time since germination also includes linear and exponential modeling data
        length_post_germination[3] or length_post_germination[”plot”] is a plot showing conidia length since germination, with median length and linear and exponential growth models
    """   
    #input checks
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    if not isinstance(germination_results, pd.DataFrame):
        raise TypeError("germination_results must be a pandas DataFrame")
        
    if not isinstance(species, str):
        raise TypeError("species must be a string")

    if not isinstance(media, str):
        raise TypeError("media must be a string")

    if not isinstance(date, str):
        raise TypeError("date must be a string")

    #column checks
    required_columns = {"TrackId", "ScanArea", "sheet_name"}

    missing_cols = required_columns - set(df.columns)
    if missing_cols:
        raise ValueError(f"df is missing required columns: {missing_cols}")

    #confirm data type (sheet_name)
    required_sheets = {"Circularity", "Area (um2)", "TotalLength (um)"}
    present_sheets = set(df["sheet_name"].dropna().unique())

    missing_sheets = required_sheets - present_sheets
    if missing_sheets:
        raise ValueError(f"df is missing required sheet_name data types: {missing_sheets}")

    species_name = species
    media_type = media
    date_of_experiment = date
    
    #get time columns
    time_cols = [col for col in df.columns if "Repetition" in col]

    #extract numeric time from time columns
    def extract_time(col):
        m = re.search(r"([0-9]+\.?[0-9]*)", str(col))
        return float(m.group(1)) if m else np.nan

    time_intervals = np.array([extract_time(col) for col in time_cols], dtype=float)

    #filter for TotalLength data and merge with germination results on TrackId
    df_germinated = (
        df[df["sheet_name"] == "TotalLength (um)"]
        .merge(germination_results, on="TrackId", how="inner")
        .copy()
    )

    #inital relative time list
    relative_time_data_list = []

    #loop through each germinated conidia row
    for _, row in df_germinated.iterrows():
        track_id = row["TrackId"]
         #germination time saved as column name not numeric
        germination_time_point = row["selected_time_point_word"]

        #extract TotalLength data
        sample_data = df[
            (df["TrackId"] == track_id) &
            (df["sheet_name"] == "TotalLength (um)")
        ]
        #skip if no germination
        if sample_data.empty:
            continue

        #take first matching row (first germianted conidia)
        sample_row = sample_data.iloc[0]

        #Convert length values to numeric
        length_values = pd.to_numeric(sample_row[time_cols], errors="coerce").to_numpy()

        #skip if no germination
        if np.all(np.isnan(length_values)):
            continue

        #find index of germination time point
        if germination_time_point not in time_cols:
            continue

        germination_index = time_cols.index(germination_time_point)

        if germination_index >= len(length_values):
            continue
        
        #align time to germiantion (germination = 0 hours)
        relative_times = time_intervals - time_intervals[germination_index]
         # Store in as individual TrackId data
        relative_time_data = pd.DataFrame({
            "track_id": track_id,
            "relative_time": relative_times,
            "length": length_values
        })
        
        relative_time_data_list.append(relative_time_data)

    #combine all samples, still identified and seperated by TrackId
    if relative_time_data_list:
        relative_time_data_combined = pd.concat(relative_time_data_list, ignore_index=True)
    else:
        relative_time_data_combined = pd.DataFrame(columns=["track_id", "relative_time", "length"])

    #remove missing lengths
    relative_time_data_combined = relative_time_data_combined.dropna(subset=["length"]).copy()

    #median length at each relative time
    if not relative_time_data_combined.empty:
        total_length_median = (
            relative_time_data_combined
            .groupby("relative_time", as_index=False)
            .agg(
                Median_Length=("length", "median"),
                n=("length", "count")
            )
        )
        #log median length
        total_length_median["log_Median_Length"] = np.log(total_length_median["Median_Length"])
        
        #add experiemnt identifiers
        total_length_median["Species"] = species_name
        total_length_median["Media"] = media_type
        total_length_median["Date"] = date_of_experiment
    else:
        total_length_median = pd.DataFrame(
            columns=[
                "relative_time", "Median_Length", "log_Median_Length",
                "n", "Species", "Media", "Date"
            ]
        )

    #growth models on 0 <= relative_time <= 24
    fit_subset = total_length_median[
        (total_length_median["relative_time"] >= 0) &
        (total_length_median["relative_time"] <= 24)
    ].copy()
    
    #initialize growth model columns
    total_length_median["lm_predicted"] = np.nan
    total_length_median["exm_predicted"] = np.nan

    
    if len(fit_subset) >= 2:
        # Linear model
        lm_model = smf.ols("Median_Length ~ relative_time", data=fit_subset).fit()
        total_length_median["lm_predicted"] = lm_model.predict(total_length_median)

        #exponential model
        exm_subset = fit_subset[fit_subset["Median_Length"] > 0].copy()
        if len(exm_subset) >= 2:
            exm_model = smf.ols("log_Median_Length ~ relative_time", data=exm_subset).fit()
            total_length_median["exm_predicted"] = np.exp(exm_model.predict(total_length_median))

    #set ylim to be 10 µm more than maximium measured condia (within first 24 hours)
    valid_window = relative_time_data_combined[
        (relative_time_data_combined["relative_time"] >= 0) &
        (relative_time_data_combined["relative_time"] <= 24)
    ]
    if not valid_window.empty:
        y_limit = valid_window["length"].max() + 10
    else:
        y_limit = None

    #Make plot of all conida growing with media length, linear, and exponenstial growth models
    fig, ax = plt.subplots(figsize=(10, 6))

    #individual conidia lines
    if not relative_time_data_combined.empty:
        for track_id, group in relative_time_data_combined.groupby("track_id"):
            group = group.sort_values("relative_time")
            ax.plot(
                group["relative_time"],
                group["length"],
                color="black",
                alpha=0.7,
                linewidth=1)
            ax.scatter(
                group["relative_time"],
                group["length"],
                color="black",
                s=15,
                alpha=0.7)

    #median lenth
    if not total_length_median.empty:
        ax.plot(
            total_length_median["relative_time"],
            total_length_median["Median_Length"],
            linewidth=2,
            label="Median Length")

    #linear growth model
    if "lm_predicted" in total_length_median.columns and total_length_median["lm_predicted"].notna().any():
        ax.plot(
            total_length_median["relative_time"],
            total_length_median["lm_predicted"],
            linewidth=2,
            label="Linear Growth Model")

    #exponential growth model
    if "exm_predicted" in total_length_median.columns and total_length_median["exm_predicted"].notna().any():
        ax.plot(
            total_length_median["relative_time"],
            total_length_median["exm_predicted"],
            linewidth=2,
            label="Exponential Growth Model")
        
    #set title to include experiments specific information
    ax.set_title(f"Length Over Time Post-Germination (Germination Time = 0) - {species} : {media}")
    
    ax.set_xlabel("Relative Time since Germination (Hours)")
    ax.set_ylabel("Length (µm)")
    
    #set xlim to be from 0 to 24 hours
    ax.set_xlim(0, 24)

    #set ylim to be 10 more than maximium measured condia (within first 24 hours)
    if y_limit is not None:
        ax.set_ylim(0, y_limit)
    ax.legend()
    ax.grid(True, alpha=0.3)

    return {
        "relative_time_df": relative_time_data_combined,
        "median_length_df": total_length_median,
        "plot": fig
    }
