
/*
Results-Request:

	http://apiBaseURL/results or any other URL

request body:

	The request contains an array of default levers which are then applied to each country in the model

	Exceptions to the default levers for single countries can be defined in the exceptions-property (optional property)

	The request also contains an array of info about the desired outputs. ('outputs')

notes:
- lever as letter or number? (it is a letter on the front-end)
- exceptions property is optional
- output ids are taken from the excel spreadsheet
- "allCountries": true 	//this flag is optional, if it is set and true, the response for this output should contain the values for all countries

One request only triggers one model-run
*/

{
	"levers": {
		"default": [3,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4],
		"exceptions": {
			"DE": [1,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4,4]
		}
	},
	"outputs": [
		{
			"id": "bld_residential-energy_oil[kWh/year]"
		},
		{
			"id": "bld_residential-energy_gas[kWh/year]",
			"allCountries": true
		},
		{
			"id": "bld_residential-energy_bio[kWh/year]"
		}
	]
}

/*
Results-Response:
the response is an array of objects which contain the values for each requested output

each output object's data property contains the following:
	- aggregated EU values
	- a set of values for each country that was defined as an exception in the request
	- If the flag "allCountries" was set to true for an output, then for this output a value-set for each country of the model is returned
*/

[
	{
		"id": "tec_eff-gas-condens[kWht/kWhc]",
		"timeAxis": [1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001], //until 2050
		"data": {
			"EU": [1232,2223,1223,2223,4323,3456,2223,1223,2223,4323], //array with values, order according to time-axis
			"DE": [1232,2223,7834,5676,4323,5676,5098,1223,4323,4323]

		}
	},
	{
		"id": "tec_eff-gas-low[kWht/kWhc]",
		"timeAxis": [1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001],
		"data": {
			"EU": [1232,2223,1223,2223,4323,3456,2223,1223,2223,5098],
			"BE": [1232,7834,1223,4323,4323,5676,5098,1223,4323,4323]
			"DE": [1232,2223,1223,7834,4323,5676,5098,1223,4323,3456],
			"PO": [1232,2223,7834,4323,4323,5676,5098,1223,4323,4323]
			//..all other countries, since the request had the allCountries-flag set to true for this id
		}
	},
	{
		"id": "tec_eff-oil-low[kWht/kWhc]",
		"timeAxis": [1990,1991,1992,1993,1994,1995,1996,1997,1998,1999,2000,2001],
		"data": {
			"EU": [1232,2223,7834,4323,4323,5676,5098,1223,4323,4323],
			"DE": [1232,2223,3762,4323,4323,9108,5098,1223,4323,4323]
		}
	}
]
