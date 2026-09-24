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


def _units_from_datamatrix(datamatrix, col_labels, dm_dict):
    """Look up the raw {variable_name: unit} dict a DataMatrix carries."""
    if "Units" in col_labels and isinstance(col_labels["Units"], dict):
        return col_labels["Units"]
    if hasattr(datamatrix, "units") and datamatrix.units:
        return datamatrix.units
    return dm_dict.get("units", {})


def _flattened_variables(col_labels):
    """List the (flat_name, var_name, cat_name) triples to read off a DataMatrix.

    Most sectors are 3D (Country x Years x Variables) and each variable is its
    own flat name. Some (e.g. "crop", "land-use") are 4D: Variables x
    Categories1, e.g. "agr_domestic-production_afw" x "crop-cereal" - those are
    flattened here into "agr_domestic-production_afw_crop-cereal" the same way
    other sectors already name their per-category fields (cat_name is None for
    the 3D case, signalling there is no Categories1 axis to index).
    """
    variable_labels = col_labels.get("Variables", [])
    category_labels = col_labels.get("Categories1")
    if not category_labels:
        return [(var, var, None) for var in variable_labels]
    return [
        (f"{var}_{cat}", var, cat) for var in variable_labels for cat in category_labels
    ]


def _get_array_value(array, indices):
    """Extract a scalar from array at the given index tuple."""
    try:
        value = array[indices]
        if isinstance(value, np.ndarray):
            value = value.item()
        return value
    except Exception:
        return None


def _resolve_year_idx(idx, year):
    """Resolve a year label to its position on the DataMatrix's Years axis."""
    if year in idx:
        return idx.get(year)
    if year.isdigit() and int(year) in idx:
        return idx.get(int(year))
    return None


def _process_country_data(array, idx, country_idx, year_labels, flattened_vars):
    """Process all year data for a single country."""
    country_data = []
    ndim = len(array.shape)

    for year in year_labels:
        year_idx = _resolve_year_idx(idx, year)
        if year_idx is None:
            continue

        year_data = {"year": str(year)}
        values_found = 0

        for flat_name, var_name, cat_name in flattened_vars:
            var_idx = idx.get(var_name)
            if var_idx is None:
                continue

            if cat_name is None:
                indices = (country_idx, year_idx, var_idx)
            else:
                cat_idx = idx.get(cat_name)
                if cat_idx is None:
                    continue
                indices = (country_idx, year_idx, var_idx, cat_idx)

            if len(indices) != ndim:
                continue

            value = _get_array_value(array, indices)
            if value is not None:
                year_data[flat_name] = value
                values_found += 1

        if values_found > 0:
            country_data.append(year_data)

    return country_data


def _transform_single_datamatrix(datamatrix):
    """Transform one DataMatrix into {"countries": ..., "units": ...}.

    Returns None if `datamatrix` doesn't have the shape of a DataMatrix, so the
    caller can decide how to handle it (e.g. treat it as a dict of DataMatrices).
    """
    if not hasattr(datamatrix, "__dict__"):
        return None

    dm_dict = datamatrix.__dict__
    if "array" not in dm_dict or "col_labels" not in dm_dict or "idx" not in dm_dict:
        return None

    array = dm_dict["array"]
    col_labels = dm_dict.get("col_labels", {})
    idx = dm_dict.get("idx", {})

    country_labels = col_labels.get("Country", [])
    year_labels = [str(y) for y in col_labels.get("Years", [])]
    flattened_vars = _flattened_variables(col_labels)

    units_source = _units_from_datamatrix(datamatrix, col_labels, dm_dict)
    result = {
        "countries": {},
        "units": {
            flat_name: units_source.get(var_name, "")
            for flat_name, var_name, _cat_name in flattened_vars
        },
    }

    for country_name in country_labels:
        country_idx = idx.get(country_name)
        if country_idx is None:
            continue
        result["countries"][country_name] = _process_country_data(
            array, idx, country_idx, year_labels, flattened_vars
        )

    return result


def _merge_sector_result(target, source):
    """Merge one DataMatrix's transformed output into a sector's combined result.

    Some sectors (e.g. "crop") come back from the model as several DataMatrices
    bundled in a plain dict (production, losses, self-sufficiency ratios, ...)
    instead of one - this joins their rows by region/year into a single sector
    so the frontend sees one flat set of fields, same as any other sector.
    """
    target["units"].update(source["units"])

    for region, rows in source["countries"].items():
        by_year = {row["year"]: row for row in target["countries"].get(region, [])}
        for row in rows:
            by_year.setdefault(row["year"], {"year": row["year"]}).update(row)
        target["countries"][region] = sorted(
            by_year.values(), key=lambda r: int(r["year"])
        )


def transform_datamatrix_to_clean_structure(output):
    """
    Transform DataMatrix objects into a clean, hierarchical JSON structure.

    Args:
        output (dict): Dictionary of DataMatrix objects from model runner. A
            handful of sectors (e.g. "crop") come back as a plain dict of
            several DataMatrices bundled together instead of a single one.

    Returns:
        dict: Cleaned hierarchical structure with countries and years
    """
    logger.info(f"Starting transformation for {len(output)} sectors")

    cleaned_output = {}

    for sector, datamatrix in output.items():
        single = _transform_single_datamatrix(datamatrix)

        if single is not None:
            cleaned_output[sector] = single
        elif isinstance(datamatrix, dict):
            combined = {"countries": {}, "units": {}}
            for sub_name, sub_datamatrix in datamatrix.items():
                sub_result = _transform_single_datamatrix(sub_datamatrix)
                if sub_result is None:
                    logger.warning(
                        f"Sub-datamatrix '{sub_name}' of sector '{sector}' is not "
                        "a recognizable DataMatrix, skipping"
                    )
                    continue
                _merge_sector_result(combined, sub_result)
            cleaned_output[sector] = combined
        else:
            logger.warning(
                f"DataMatrix for {sector} is neither a DataMatrix nor a dict of "
                "DataMatrices, skipping"
            )
            continue

        populated_countries = sum(
            1 for rows in cleaned_output[sector]["countries"].values() if rows
        )
        logger.info(
            f"Sector {sector}: populated {populated_countries} countries, "
            f"{len(cleaned_output[sector]['units'])} variables"
        )

    # Convert NumPy types
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
        f"Lever data transformation completed for "
        f"{len(result['lever_positions'])} positions"  # type: ignore
    )
    return result
