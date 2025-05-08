import logging
import numpy as np
import json

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
        return float(obj)
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


def transform_datamatrix_to_clean_structure(output, years_setting, geo_pattern=None):
    """
    Transform DataMatrix objects into a clean, hierarchical JSON structure.

    Args:
        output (dict): Dictionary of DataMatrix objects from model runner
        years_setting (list): Year settings [start_year, current_year, future_year, end_year, step]
        geo_pattern (str): Geographic pattern string (defaults to "Switzerland|Vaud|EU27")

    Returns:
        dict: Cleaned hierarchical structure with countries and years
    """
    logger.info(f"Starting transformation for {len(output)} sectors")

    cleaned_output = {}

    # Countries mapping based on geo_pattern
    if geo_pattern:
        countries = geo_pattern.split("|")
    else:
        countries = ["Switzerland", "Vaud", "EU27"]  # Default

    # Base years derived from years_setting
    base_years = list(range(years_setting[0], years_setting[1] + 1, years_setting[4]))
    base_years.extend([years_setting[2], years_setting[3]])
    base_years = sorted(set(base_years))  # Remove duplicates and sort

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

        # Log array shape
        array_shape = array.shape if hasattr(array, "shape") else "unknown"
        logger.info(f"Processing {sector}: array shape {array_shape}")

        # Get country and year labels from col_labels
        country_labels = col_labels.get("Country", [])
        year_labels = [str(y) for y in col_labels.get("Years", [])]
        variable_labels = col_labels.get("Variables", [])

        # If no variable labels found, try col_labels directly
        if not variable_labels and isinstance(col_labels, list):
            variable_labels = col_labels

        # Fix: Check if we have at least countries, years and variables
        if not country_labels:
            country_labels = countries
        if not year_labels:
            year_labels = [str(y) for y in base_years]

        # Initialize the country structure
        cleaned_output[sector] = {"countries": {}}

        # Process each country
        country_stats = {}
        for country_name in country_labels:
            # Get country index either from idx or by position
            country_idx = idx.get(country_name)
            if country_idx is None:
                try:
                    country_idx = countries.index(country_name)
                except ValueError:
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
                    try:
                        year_int = int(year) if year.isdigit() else None
                        if year_int and year_int in base_years:
                            year_idx = base_years.index(year_int)
                        else:
                            continue  # Skip if year can't be found
                    except (ValueError, TypeError):
                        continue  # Skip if year can't be processed

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
    logger.info("Finalizing data structure for JSON serialization")
    cleaned_output = _convert_numpy_types(cleaned_output)

    return cleaned_output
