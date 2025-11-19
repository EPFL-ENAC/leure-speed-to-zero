import logging
import numpy as np

logger = logging.getLogger("uvicorn")


def _convert_numpy_types(obj):
    """
    Convert NumPy types to standard Python types for JSON serialization.

    Args:
        obj: Any Python object that might contain NumPy types

    Returns:
        Object with all NumPy types converted to standard Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        # Preserve the precision of floating-point numbers up to 10 decimal
        return round(float(obj), 10)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_convert_numpy_types(item) for item in obj)
    else:
        return obj


def transform_datamatrix_to_clean_structure_by_dataframe(output):
    """
    Transform DataMatrix objects into a clean, hierarchical JSON structure using the
    built-in fast_write_df method.
    """
    logger.info(f"Starting transformation for {len(output)} sectors")
    cleaned_output = {}

    for sector, datamatrix in output.items():
        if not hasattr(datamatrix, "fast_write_df"):
            logger.warning(
                f"DataMatrix for {sector} missing required methods, skipping"
            )
            continue

        try:
            # Convert DataMatrix to DataFrame, then to dict records
            df = datamatrix.fast_write_df()
            dict_data = df.to_dict(orient="records")

            # Store the results
            cleaned_output[sector] = dict_data

        except Exception as e:
            logger.error(f"Error processing sector {sector}: {str(e)}")

    logger.info(f"Transformation completed for {len(cleaned_output)} sectors")
    return cleaned_output


def transform_datamatrix_to_clean_structure(output):
    """
    Transform DataMatrix objects into a clean, hierarchical JSON structure.

    Args:
        output (dict): Dictionary of DataMatrix objects from model runner

    Returns:
        dict: Cleaned hierarchical structure with countries and years
    """
    logger.info(f"Starting transformation for {len(output)} sectors")

    cleaned_output = {}

    for sector, datamatrix in output.items():
        # Get DataMatrix elements
        if not hasattr(datamatrix, "__dict__"):
            logger.warning(
                f"DataMatrix for {sector} has no __dict__ attribute, skipping"
            )
            continue

        dm_dict = datamatrix.__dict__

        # Check for required elements
        if (
            "array" not in dm_dict
            or "col_labels" not in dm_dict
            or "idx" not in dm_dict
        ):
            logger.warning(
                f"DataMatrix for {sector} missing required elements, skipping"
            )
            continue

        array = dm_dict["array"]
        col_labels = dm_dict.get("col_labels", {})
        idx = dm_dict.get("idx", {})

        # Get country and year labels from col_labels
        country_labels = col_labels.get("Country", [])
        year_labels = [str(y) for y in col_labels.get("Years", [])]
        variable_labels = col_labels.get("Variables", [])

        # If no variable labels found, try col_labels directly
        if not variable_labels and isinstance(col_labels, list):
            variable_labels = col_labels

        # Initialize the country structure
        cleaned_output[sector] = {"countries": {}, "units": {}}

        # Extract unit information if available
        units = {}
        # Try to get units from col_labels
        if "Units" in col_labels and isinstance(col_labels["Units"], dict):
            units = col_labels["Units"]
        # Check if units are stored in a separate attribute
        elif hasattr(datamatrix, "units") and datamatrix.units:
            units = datamatrix.units
        # Check if units are stored in the dm_dict
        elif "units" in dm_dict and dm_dict["units"]:
            units = dm_dict["units"]

        # Store units in output
        for var_name in variable_labels:
            if var_name in units:
                cleaned_output[sector]["units"][var_name] = units[var_name]
            else:
                cleaned_output[sector]["units"][
                    var_name
                ] = ""  # Empty string if no unit is found

        # Process each country
        country_stats = {}
        for country_name in country_labels:
            # Get country index from idx
            country_idx = idx.get(country_name)
            if country_idx is None:
                continue  # Skip if country can't be found

            cleaned_output[sector]["countries"][country_name] = []
            values_by_year = 0

            # Process each year
            for year in year_labels:
                # Get year index
                year_idx = (
                    idx.get(year)
                    if year in idx
                    else (
                        idx.get(int(year))
                        if year.isdigit() and int(year) in idx
                        else None
                    )
                )

                if year_idx is None:
                    continue  # Skip if year can't be found

                year_data = {"year": str(year)}
                values_found = 0

                # Process each variable
                for var_name in variable_labels:
                    var_idx = idx.get(var_name)
                    if var_idx is None:
                        continue  # Skip if variable not found

                    try:
                        # Access the data based on the number of dimensions in the array
                        if len(array.shape) == 3:
                            value = array[country_idx, year_idx, var_idx]
                        elif len(array.shape) == 4:
                            value = array[country_idx, year_idx, var_idx, 0]
                        else:
                            continue  # Skip unsupported array shapes

                        if isinstance(value, np.ndarray):
                            value = (
                                value.item()
                            )  # Convert numpy scalar to Python scalar

                        year_data[var_name] = value
                        values_found += 1
                    except Exception:
                        year_data[var_name] = None

                if values_found > 0:
                    cleaned_output[sector]["countries"][country_name].append(year_data)
                    values_by_year += values_found

            # Keep track of how much data was found for this country
            country_stats[country_name] = len(
                cleaned_output[sector]["countries"][country_name]
            )

        # Log summary for this sector
        populated_countries = sum(1 for count in country_stats.values() if count > 0)
        logger.info(
            f"Sector {sector}: populated {populated_countries} countries, {len(variable_labels)} variables"
        )

    # Convert NumPy types to standard Python types
    cleaned_output = _convert_numpy_types(cleaned_output)

    return cleaned_output


def transform_lever_data_for_echarts(lever_data_dict):
    """
    Transform lever data from get_lever_data_to_plot() into ECharts-friendly format.

    Args:
        lever_data_dict (dict): Dictionary with keys 1,2,3,4 and DataMatrix values

    Returns:
        dict: ECharts-ready data structure with series for each lever position
    """
    logger.info(
        f"Starting lever data transformation for {len(lever_data_dict)} lever positions"
    )

    result = {
        "lever_positions": {},
        "metadata": {"countries": [], "years": [], "variables": [], "units": {}},
    }

    for lever_position, datamatrix in lever_data_dict.items():
        if not hasattr(datamatrix, "fast_write_df"):
            logger.warning(
                f"DataMatrix for lever position {lever_position} missing fast_write_df method, skipping"
            )
            continue

        try:
            # Convert DataMatrix to DataFrame
            df = datamatrix.fast_write_df()

            # Convert to records format
            records = df.to_dict(orient="records")

            # Store the records for this lever position
            result["lever_positions"][lever_position] = records

            # Extract metadata (from first lever position)
            if lever_position == list(lever_data_dict.keys())[0]:
                if "Country" in df.columns:
                    result["metadata"]["countries"] = sorted(
                        df["Country"].unique().tolist()
                    )
                if "Years" in df.columns:
                    result["metadata"]["years"] = sorted(df["Years"].unique().tolist())

                # Extract variables and units from column names
                for col in df.columns:
                    if col not in ["Country", "Years"]:
                        # Parse variable[unit] format
                        if "[" in col and "]" in col:
                            var_name = col.split("[")[0]
                            unit = col.split("[")[1].split("]")[0]
                            result["metadata"]["variables"].append(var_name)
                            result["metadata"]["units"][var_name] = unit
                        else:
                            result["metadata"]["variables"].append(col)
                            result["metadata"]["units"][col] = ""

        except Exception as e:
            logger.error(f"Error processing lever position {lever_position}: {str(e)}")

    # Convert to JSON-serializable format
    result = _convert_numpy_types(result)

    logger.info(
        f"Lever data transformation completed for {len(result['lever_positions'])} positions"
    )
    return result
