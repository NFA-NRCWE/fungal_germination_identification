#install and load packages
packages <- c("readxl", "dplyr", "tidyverse", "ggplot2", "ggpubr", "knitr", "RColorBrewer", "segmented", "nortest", "car", "drc")

for (pkg in packages) {
  if (!require(pkg, character.only = TRUE)) {
    install.packages(pkg)
    library(pkg, character.only = TRUE)
  }
}

library(readxl)
library(dplyr)
library(tidyverse)
library(ggplot2)
library(ggpubr)
library(knitr)
library(RColorBrewer)
library(segmented)
library(nortest)
library(car)
library(drc)

##################################################################################
#' Function to load and combine all sheets except 'Job Configuration' because it contains non relevant information
#' @param file_path filepath to data output from oCelloScope Object Tracking Module (EXCELL ONLY)
#' @return Data Frame with all datasheets stacked together with a new column (sheet_name) to define the data type
combine_excel_sheets <- function(file_path) {
  
  #Get all sheet names from the Excel file
  sheet_names <- excel_sheets(file_path)
  
  #Remove "job configuration" sheet, added ignore case becuase I have seen it be different on different jobs
  sheet_names <- sheet_names[!grepl("Job configuration", sheet_names, ignore.case = TRUE)]
  
  all_data <- list()
  
  #Loop over each sheet
  for (sheet in sheet_names) {
    
    sheet_data <- read_excel(file_path, sheet = sheet)
    
    #dplyr::select is necessary because other packages loaded interfere
    sheet_data_filtered <- sheet_data %>%
      dplyr::select(ScanArea, TrackId, matches("Repetition"))
    
    #sheet name column will be data type
    sheet_data_filtered <- sheet_data_filtered %>%
      mutate(sheet_name = sheet)  # Add sheet name as a column
    
    #Reorder columns to make 'sheet_name' the first column
    sheet_data_filtered <- sheet_data_filtered %>%
      dplyr::select(ScanArea, TrackId, sheet_name, everything())
    
    #Append the filtered data to the list
    all_data[[sheet]] <- sheet_data_filtered
  }
  
  # Combine all the sheet data into one large data frame
  combined_data <- bind_rows(all_data)
  
  return(combined_data)
}

##################################################################################
#' In the original data frame, "Repetition X" doesn't correspond to the actual time 
#' For further analysis, Repetition X must correspond to time
#' This function changes Repetition X to match my time since the experiment initiated:
#' Imaged every 4 hours for the first 20 hours and then imaged every 2 hours for the next 76 

#' @param df Data frame containing individual conidia data (MUST ALREADY BE CONVERTED BY combine_excel_sheets())
#' @return Data frame with all Repetition columns transformed to match the hour of the experiment
rename_repetition_columns <- function(df) {
  #Start time at 0 hours
  current_time <- 0

  new_columns <- c()
  
  # loop over all Repetition Columns
  for (col_name in names(df)) {
    #Check if the column name starts with "Repetition"
    if (startsWith(col_name, "Repetition")) {
      #new column name with the current time
      new_col_name <- paste("Repetition", current_time)
      
      new_columns <- c(new_columns, new_col_name)
      
      #change the time: first 20 hours are 4 hours apart, the rest are 2 hours apart
      if (current_time < 20) {
        current_time <- current_time + 4
      } else {
        current_time <- current_time + 2
      }
    } else {
      #keep non Repetition names 
      new_columns <- c(new_columns, col_name)
    }
  }
  
  #Rename the columns in the data frame
  colnames(df) <- new_columns
  
  return(df)
}

####################################################################################
#' In the original data frame, "Repetition X" doesn't correspond to the actual time 
#' For further analysis, Repetition X must correspond to time
#' This function changes Repetition X to match my time since the experiment initiated:
#' Imaged every hour

#' @param df Data frame containing individual conidia data (MUST ALREADY BE CONVERTED BY combine_excel_sheets())
#' @return Data frame with all Repetition columns transformed to match the hour of the experiment
rename_repetition_columns2 <- function(df) {
  #Start time at 0 hours
  current_time <- 0
  
  new_columns <- c()
  
  # loop over all Repetition Columns
  for (col_name in names(df)) {
    #Check if the column name starts with "Repetition"
    if (startsWith(col_name, "Repetition")) {
      #new column name with the current time
      new_col_name <- paste("Repetition", current_time)
      
      new_columns <- c(new_columns, new_col_name)
      
      #change the time: first 20 hours are 1 hours apart, the rest are 1 hours apart
      if (current_time < 20) {
        current_time <- current_time + 1
      } else {
        current_time <- current_time + 1
      }
    } else {
      #keep non Repetition names 
      new_columns <- c(new_columns, col_name)
    }
  }
  
  #Rename the columns in the data frame
  colnames(df) <- new_columns
  
  return(df)
}

################################################################################
#' In the original data frame, "Repetition X" doesn't correspond to the actual time 
#' For further analysis, Repetition X must correspond to time
#' This function changes Repetition X to match my time since the experiment initiated:
#' Imaged every other hour

#' @param df Data frame containing individual conidia data (MUST ALREADY BE CONVERTED BY combine_excel_sheets())
#' @return Data frame with all Repetition columns transformed to match the hour of the experiment
rename_repetition_columns3 <- function(df) {
  #Start time at 0 hours
  current_time <- 0
  
  new_columns <- c()
  
  # Iterate over column names
  for (col_name in names(df)) {
    #Check if the column name starts with "Repetition"
    if (startsWith(col_name, "Repetition")) {
      #new column name with the current time
      new_col_name <- paste("Repetition", current_time)
      
      new_columns <- c(new_columns, new_col_name)
      
      #change the time: first 20 hours are 2 hours apart, the rest are 2 hours apart
      if (current_time < 20) {
        current_time <- current_time + 2
      } else {
        current_time <- current_time + 2
      }
    } else {
      #keep non Repetition names 
      new_columns <- c(new_columns, col_name)
    }
  }
  
  #Rename the columns in the data frame
  colnames(df) <- new_columns
  
  return(df)
}

################################################################################
#' determine the time and area in which the conidia transition from isotropic growth to polarized growth using a segmented linear regression

#' @param df Data frame containing individual conidia data id identified under TrackId (repetition columns must match hour of the experiment)
#' @param species Character Species/isolate name.
#' @param media Character Growth condition testing  (Ex: fungicide concentration, environmental conditions, temperature, water activity)
#' @param date Character Experiment date. For keeping replicates separate when combining all data

#' @return isotropic_growth[1] or isotropic_growth["isotropic_data"] Data Frame with isotropic growth metrics
#' @return isotropic_growth[2] or isotropic_growth["plot"] is a plot showing segmented regression
isotropic_growth <- function(df, species, media, date) {
  #convert Repetition columns to numaric time
  time_columns <- grep("Repetition", names(df), value = TRUE)
  numeric_times <- as.numeric(gsub("[^0-9.]", "", time_columns))
  
  #pivot table long with all Repetition
  data_long <- df %>%
    pivot_longer(
      cols = all_of(time_columns),
      names_to = "time",
      values_to = "value"
    ) %>%
    mutate(time = as.numeric(gsub("[^0-9.]", "", time)))
  
  #filter for only area data
  area_data <- data_long %>%
    filter(sheet_name == "Area (um2)")
  
  #remove all ungerminated conidia
  #filter for only conidia that grew to at least 2.5x over recorded time 
  area_data_filtered <- area_data %>%
    group_by(TrackId) %>%
    mutate(
      Original_Size = first(value),  
      Max_Size = max(value, na.rm = TRUE) 
    ) %>%
    ungroup()
  
  area_data_filtered <- area_data_filtered %>%
    filter(Max_Size > 2.5 * Original_Size)
  
  if (nrow(area_data_filtered) == 0 || all(is.na(area_data_filtered$value))) {
    return(list(
      isotropic_data = "no germination, check video",
      plot = NULL
    ))
  }
  
  #segmented regression to determine isotropic growth fold change before polarized growth
  fits <- area_data_filtered %>%
    group_by(TrackId) %>%
    nest() %>%
    mutate(
      lm_fit = map(data, \(d) lm(value ~ time, data = d)),
      seg_fit = map(data, \(d) segmented(
        lm(value ~ time, data = d),
        seg.Z = ~ time,
        psi = 10
      ))
    ) 
  
  #breakpoints = time the initial linear regression stopped being significantly correlated
  breakpoints <- fits %>%
    mutate(bp = map(seg_fit, \(m) as.data.frame(m$psi))) %>%
    dplyr::select(TrackId, bp) %>%
    unnest(bp)
  
  #area at breakpoints
  breakpoint_values <- fits %>%
    filter(!map_lgl(seg_fit, is.null)) %>%
    mutate(
      bp = map(seg_fit, \(m) as.data.frame(m$psi)),
      pred = map2(seg_fit, bp, \(m, bp_df) {
        predict(m, newdata = data.frame(time = bp_df$Est.))
      })
    ) %>%
    dplyr::select(TrackId, bp, pred) %>%
    unnest(c(bp, pred))   
  
  #regression visualization
  test_model_data <- fits %>%
    filter(!map_lgl(seg_fit, is.null)) %>%
    mutate(
      model_data = map2(seg_fit, data, \(m, d) {
        d %>%
          arrange(time) %>%
          mutate(predicted = predict(m, newdata = data.frame(time = as.numeric(time)))
          )
      })
    ) %>%
    dplyr::select(TrackId, model_data) %>%
    unnest(model_data)
  
  first_area <- area_data_filtered %>%
    filter(time == min(time, na.rm = TRUE)) %>%
    dplyr::select(TrackId, First_Area = value)
  
  breakpoint_results <- breakpoint_values %>%
    dplyr::select(TrackId,
                  Breakpoint_Time = Est.,
                  Breakpoint_Area = pred) %>%
    left_join(first_area, by = "TrackId") %>%
    mutate(Swelling_change = Breakpoint_Area / First_Area,
           Species = species,
           Media = media,
           Date = date) %>%
    group_by(Species, Media, Date) %>%
    reframe(Average_Breakpoint_Time = mean(Breakpoint_Time),
            Average_Breakpoint_Area = mean(Breakpoint_Area),
            Average_First_Area = mean(First_Area),
            Average_Swelling_change= mean(Swelling_change))
  
  result <-  breakpoint_results
  
  data_visual <-ggplot(test_model_data, aes(x = time, y = value, group = TrackId)) +
    geom_point(color = "#A8B6CC", size = 3, na.rm = TRUE) +
    geom_line(aes(y = predicted), color = "#F05039", linewidth = 1) +
    facet_wrap(~ TrackId, scales = "free_y") +
    geom_vline(data = breakpoint_values, aes(xintercept = Est.), linetype = "dashed", color = "black") +
    labs(
      title = bquote("Segmented Regression with Breakpoints and Values - " ~ italic(.(breakpoint_results$Species))),
      x = "Time (Hours)",
      y = expression(Area(μm^{2}))
    ) +
    theme_minimal()
  
  return(list(isotropic_data = result, plot = data_visual))
}


################################################################################
#' find the time point when germination tube formation begins based on a change in circularity and area. also calculates growthrates

#' @param df Data frame containing individual conidia data id identified under TrackId (repetition columns must match hour of the experiment)
#' @param breakpoint_value Numeric Swelling_change from isotropic_growth() function (Example: a_fumigatus_isotropic_growth$Swelling_change)
#' @param species Character Species/isolate name.
#' @param media Character Growth condition testing  (Ex: fungicide concentration, environmental conditions, temperature, water activity)
#' @param date Character Experiment date. For keeping replicates separate when combining all data

#' @return Data frame with germination metrics
find_time_point <- function(df, breakpoint_value, species, media, date) {
  
  # Get the time point columns (assumed to be all except SampleID and measure_type)
  time_cols <- grep("Repetition", colnames(df), value = TRUE)
  
  # Unique list of TrackIds
  track_ids <- df$TrackId
  
  # Initialize output variables
  selected_time_points <- rep(NA, length(track_ids))
  last_time_points <- rep(NA, length(track_ids))
  selected_lengths <- rep(NA, length(track_ids))
  final_lengths <- rep(NA, length(track_ids))

  confirm_n <- 3  
  
  
  # Loop through each SampleID
  for (i in seq_along(track_ids)) {
    track_data <- subset(df, TrackId == track_ids[i])  # Subset data for the current SampleID
    
    # Separate circularity, area, and longest, and length data
    circularity_data <- subset(track_data, sheet_name == "Circularity")[, time_cols]
    area_data <- subset(track_data, sheet_name == "Area (um2)")[, time_cols]
    length_data <- subset(track_data, sheet_name == "TotalLength (um)")[, time_cols]

    # Find the first non-NA value in area_data to use as the initial area
    initial_area <- NA
    for (val in area_data) {
      if (!is.na(val) && val <= 75 && val >= 10) {
        initial_area <- val
        break
      }
    }
    
    initial_circle <- NA
    for (val in circularity_data) {
      if (!is.na(val) && val < 0.92) {
        initial_circle <- val
        break
      }
    }
    
    # Check if we found a valid initial area
    if (!is.na(initial_area)) {
      # Iterate through time points to find when circularity drops below 0.97 and area increases by 10%
      for (j in seq_along(time_cols)) {
        current_circularity <- circularity_data[[j]]
        current_area <- area_data[[j]]
        
        
        # Check if the current values are not NA before making comparisons
        if (!is.na(current_circularity) && !is.na(current_area)) {

          if (current_circularity < 0.94 && current_area >= (breakpoint_value * initial_area * 1.25)) {
            
            L <- length(time_cols)
            confirmed <- FALSE
            if (j + confirm_n <= L) {
              confirmed <- TRUE
              for (k in (j + 1):(j + confirm_n)) {
                next_circ <- circularity_data[[k]]
                next_area <- area_data[[k]]
                if (is.na(next_circ) || is.na(next_area) ||
                    !(next_circ < 0.94 && next_area >= (breakpoint_value * initial_area * 1.25))) {
                  confirmed <- FALSE
                  break
                }
              }
            } else {
              confirmed <- TRUE   # <-- accept when fewer than confirm_n future frames exist
            }
            
            if (!confirmed) {
              next  # keep scanning forward; do not lock in yet
            }
            
            
            selected_time_points[i] <- time_cols[j]  # Store the time point (column name)
            selected_lengths[i] <- length_data[[j]]
            break  # Stop checking once conditions are met
          }
        }
      }
    }
    
    final_length_found <- NA
    for (k in seq_along(length_data)) {
      if (!is.na(length_data[[k]])) {
        final_length_found <- length_data[[k]]
        last_time_points[i] <- time_cols[k]# Keep updating until the last non-NA value is found
      }
    }
    
    final_lengths[i] <- final_length_found  # Store the last non-NA length value
    
  }
  
  # Create a result data frame
  result <- unique(data.frame(ScanArea = df$ScanArea[df$TrackId == track_ids], #this is an experiment date and number ID tag
                              TrackId = track_ids, 
                              selected_time_point = (as.numeric(gsub("[^0-9.]", "", selected_time_points))), #selected in this function correlates to germination
                              selected_time_point_word = selected_time_points, 
                              last_time_point = (as.numeric(gsub("[^0-9.]", "", last_time_points))),
                              selected_length = selected_lengths,
                              final_length = final_lengths)
                   )
  
  result <- result %>%
    mutate(Species = species,
           Media = media,
           Date = date,
           linear_growth_rate = ((final_length - selected_length) / (last_time_point - selected_time_point)),
           exponential_growth_rate = ((log(final_length) - log(selected_length)) / (last_time_point - selected_time_point))
           )
  
  result <- result %>%
    dplyr::select(Species, Media, Date, ScanArea, TrackId, selected_time_point, selected_time_point_word, last_time_point, selected_length, final_length, linear_growth_rate, exponential_growth_rate)
  
  return(result)
}

##############################################################################################################################
#' making a data frame/plot with the length of the individual spore and the relative time, given the point of germination found using the find_time_point 
#' 
#' @param df Data frame containing individual conidia data id identified under TrackId (repetition columns must match hour of the experiment)
#' @param germination_results Data frame from find_time_point() function
#' @param species Character Species/isolate name.
#' @param media Character Growth condition testing  (Ex: fungicide concentration, environmental conditions, temperature, water activity)
#' @param date Character Experiment date. For keeping replicates separate when combining all data

#' @return length_post_germination[1] or length_post_germination[”relative_time_df”] Data Frame length of each conidia, identified with TrackId, with time relative to germination tube formation 
#' @return length_post_germination[2] or length_post_germination[”median_length_df”] Data Frame median length and relative time since germination also includes linear and exponential modeling data
#' @return length_post_germination[3] or length_post_germination[”plot”] is a plot showing conidia length since germination, with median length and linear and exponential growth models
length_post_germination <- function(df, germination_results, species, media, date) {
  
  species_name <- species
  media_type <- media
  date_of_experiemnt <- date
  
  # Get the time point columns (assumed to be all except SampleID and measure_type)
  time_cols <- grep("Repetition", colnames(df), value = TRUE)
  
  # Define the actual time intervals based on the column names
  time_intervals <- sapply(time_cols, function(col) {
    # Extract the numeric part of the "Repetition" label
    as.numeric(sub("Repetition", "", col))
  })
  
  # Filter for length data and merge with germination results
  df_germinated <- df %>%
    filter(sheet_name == "TotalLength (um)") %>%
    inner_join(germination_results, by = "TrackId")
  track_ids <- df_germinated$TrackId
  
  # Initialize a list to store the adjusted length data
  relative_time_data_list <- list()
  
  # Loop through each SampleID in the germinated results
  for (i in seq_len(nrow(df_germinated))) {
    
    track_id <- df_germinated$TrackId[i]
    germination_time_point <- df_germinated$selected_time_point_word[i]  # Get the germination time point
    
    # Subset the original data for this sample and measure_type 'length'
    sample_data <- df %>%
      filter(TrackId == track_id & sheet_name == "TotalLength (um)")
    
    # Extract the length values corresponding to the time columns
    length_values <- as.numeric(sample_data[, time_cols, drop = FALSE])
    # Check if there are any valid length values
    if (all(is.na(length_values))) {
      next  # Skip to the next sample if all lengths are NA
    }
    
    # Get the index of the germination time point
    germination_index <- match(germination_time_point, time_cols)
    
    # Ensure the germination index is valid
    if (!is.na(germination_index) && germination_index <= length(length_values)) {
      # Calculate relative times based on actual intervals
      relative_times <- time_intervals - time_intervals[germination_index]
      
      # Create a data frame for this sample with adjusted times and lengths
      relative_time_data <- data.frame(
        track_id = track_id,
        relative_time = relative_times,
        length = length_values  # Length values directly
      )
      
      # Append this sample's data to the list
      relative_time_data_list[[i]] <- relative_time_data
    }
  }
  
  # Combine all samples' adjusted data into one data frame
  relative_time_data_combined <- bind_rows(relative_time_data_list)
  
  # Remove rows with missing length values
  relative_time_data_combined <- relative_time_data_combined %>%
    filter(!is.na(length))
  
  total_length_median <- relative_time_data_combined %>%
    group_by(relative_time) %>%
    reframe(Median_Length = median(length, na.rm = TRUE),
            log_Median_Length = log(median(length, na.rm = TRUE)),
            n = n(),
            Species = species_name,
            Media = media_type,
            Date = date_of_experiemnt)

  
   relative_time_lm <- lm(Median_Length ~ relative_time, data = total_length_median, subset = (relative_time >= 0 & relative_time <= 24))
  
  # Make predictions
  relative_time_lm_prediction_interval <- predict(
    relative_time_lm, 
    newdata = total_length_median,
    interval="prediction",
    level = 0.95,
    )
  
  total_length_median$lm_predicted <- relative_time_lm_prediction_interval[, "fit"]  
  
  relative_time_exm <- lm(log_Median_Length ~ relative_time, data = total_length_median, subset = (relative_time >= 0 & relative_time <= 24))
  # Make predictions
  relative_time_exm_prediction_interval <- exp(predict(
    relative_time_exm, 
    newdata = total_length_median,
    interval="prediction",
    level = 0.95,
   ))
  
  total_length_median$exm_predicted <- relative_time_exm_prediction_interval[, "fit"]
  
  y_limit <- max(relative_time_data_combined$length[relative_time_data_combined$relative_time >= 0 & relative_time_data_combined$relative_time <= 24]) + 10
  
  plot <- ggplot(relative_time_data_combined, aes(x = relative_time, y = length, group = track_id), 
                 ) +
    geom_line(aes(x = relative_time, y = length, 
                  group = track_id, color = "Individual conidia"), na.rm = TRUE, show.legend = TRUE) +
    geom_point(na.rm = TRUE, aes(color = "Individual conidia"), show.legend = TRUE) +
    
    geom_line(data = total_length_median, aes(x = relative_time, y = Median_Length, col = "Median Length"), na.rm = TRUE, 
              linewidth = 1.5, show.legend = TRUE) +
    xlim(0,24) +
    ylim(0,y_limit) +
    labs(title = "Length Over Time Post-Germination (Germination Time = 0)",
         subtitle = bquote(italic(.(total_length_median$Species)) ~ (.(total_length_median$Media))),
         x = "Relative Time since Germination (Hours)",
         y = "Length (µm)",
         color = "Growth Models") +
    geom_line(data = total_length_median, 
              aes(x = relative_time, y = lm_predicted, col="Linear Growth Model"), 
              linewidth = 2, show.legend = TRUE) +
    geom_line(data = total_length_median, 
              aes(x = relative_time, y = exm_predicted, col="Exponential Growth Model"), 
              linewidth = 2, show.legend = TRUE) +
    scale_color_manual(values = c("Individual conidia" = "black", 
                                  "Median Length" = "#F05039",
                                  "Exponential Growth Model" = "#24796C",
                                  "Linear Growth Model" = "#7b99c9")
                      ) +
    theme_minimal() +
    theme(panel.border = element_rect(colour = "black", fill=NA, linewidth=1),
          axis.text = element_text(size = 14, colour = "black"),
          axis.title.x = element_text(size = 14),
          axis.title.y = element_text(size = 14),
          legend.text = element_text(size = 14),
          legend.title = element_text(size = 14))
  
  
  return(list(relative_time_df = relative_time_data_combined, median_length_df = total_length_median, plot = plot))
}

#####################################################################################
#reframing the whole data set into a pivot for total graphing 

reframing_full_set_pivot <- function(df, track_col = "TrackId", date_col = "Date", media_col = "Media") {
  df_long <- df %>%
    pivot_longer(
      cols = starts_with("Repetition"),
      names_to = "time_point",
      values_to = "spore_length"
    ) %>%
    mutate(
      time_hours = as.numeric(str_extract(time_point, "\\d+\\.*\\d*")),
      {{ track_col }} := as.factor(.data[[track_col]]),
      {{ date_col }} := as.factor(.data[[date_col]]),
      {{ media_col }} := as.factor(.data[[media_col]])
    )
}

########################################################################################
#test data frames to run while changing and making functions that replicate the oCelloScope data but are smaller
test_df <- data.frame(
  ScanArea = "test data frame",
  TrackId = c("A", "A", "A", "B", "B", "B", "C", "C", "C", "D", "D", "D"),
  sheet_name = c("Circularity", "Area (um2)", "TotalLength (um)", 
                 "Circularity", "Area (um2)", "TotalLength (um)",
                 "Circularity", "Area (um2)", "TotalLength (um)", 
                 "Circularity", "Area (um2)", "TotalLength (um)"),
  "Repetition0" = c(0.99, 35, 15, 0.97, 40, 15, 0.99, 35, 15, NA, NA, NA),
  "Repetition5" = c(0.98, 37, 25, 0.96, 55, 17, 0.99, 36, 15, NA, NA, NA),
  "Repetition10" = c(0.94, 50, 30, 0.9, 100, 35, 0.99, 38, 17,  0.96, 45, 25),
  "Repetition15" = c(0.93, 65, 35, 0.87, 190, 40, 0.98, 40, 19, 0.92, 60, 35),
  "Repetition20" = c(0.92, 90, 45, 0.86, 205, 50, 0.97, 40, 20, 0.92, 95, 45),
  "Repetition25" = c(0.90, 130, 50, 0.85, 225, 65, 0.97, 45, 25, 0.92, 150, 55),
  "Repetition30" = c(0.90, 155, 60, 0.84, 250, 80, 0.98, 50, 35, 0.92, 195, 65)
)



#iso_test <- isotropic_growth(test_df, "species", "media", "date")
   # iso_test["isotropic_data"]
    #iso_test["plot"]
    
#find_timepoint_test <- find_time_point(test_df, 1, "species", "media", "date")
   #find_timepoint_test
#relative_length_test <- length_post_germination(test_df, find_timepoint_test)
    #relative_length_test["relative_time_df"]
    #relative_length_test["median_length_df"]
    #relative_length_test["plot"]

