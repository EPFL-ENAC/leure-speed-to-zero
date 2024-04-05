# Changelog

## ParisCalc-Alpha_Database-1.5
### Summary
Paris demonstrator first working version, from knime to TPE.


## v1.3
### Added
- Use an Excel file to configure levers and added headlines and groups in the levers endpoint
- Use an Excel file to configure calculated output metrics
- Implemented calculated metrics as sums of other columns
- Added simple cache mechanism for last runs
### Fixes
- It seems that there can be DB timeouts due to long running times of the workflows when using the Knime backend. This was fixed by recreating the DB connection when querying. 
### Modified
- Error management:
  - API returns an empty response with code 200 if no output metric was found. 
  - If only part of the metrics were found they are returned with a code 200 as well.
  - If a calculated metric is missing one of its components, the whole calculated metric will not be returned.

## v1.1
### Added
- Logging to a file in addition to console

### Modified
- Improved Missing Values node performance
- Include database reads in build

### Fixes
- Prevent model crash if a node doesn't exist in the list of output nodes
- Correction of database_reader_node build metode
- Add final test (db comparison) at the end of the test_data-processing test
- Update math formula multi column to avoid self.expression to be overwritten
- Fixed Column Aggregator that was not resetting properly, creating inconsistent results between runs.

## v1.0.2  
- First version of the converter able to convert the workflow "data-processing" in the repo "_interactions"
- API code copied from other repo.