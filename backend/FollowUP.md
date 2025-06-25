Hello hello,

As discussed with Pierre, find below some notes for the app.

@Gino:
do you agree that we won’t do intermediate levers like 1.1 or 3.2 etc ?
we need to decide what we want to show as hoovering information when going over the lever settings. Maybe it could be good to show the graph with the lever settings?

Other Calculators apps:
CityCalc: https://eucitycalc.climact.com/pathways?region=FR0196&visualisation=0&mode=1
The Global Calculator: https://tool.globalcalculator.net/globcalc.html?levers=22rfoe2e13be1111c2c2c1n31hfjdcef222hp233f211111fn2211111111/dashboard/en

If you want to play around with the interface, choose Vaud as a country in the config_docker_eu.yml file and look at the following:

Buildings

The first 4 sub-tabs until "Heating emissions » have working plots

The lever that work are:

- « Technology and fuels » / « Building envelope » : lever 1,2 show different results
- « Technology and fuels » / « Technology and fuel share »: lever 1,2 show different results

Some plots are unaffected by changes, but plots in « Heating emissions » tab are always affected

PastedGraphic-1.png

Transport

All the sub-tabs starting with « Passenger » have working plots

The lever that work for lever 1,2,4 are:
-Travel/Passenger distance
-Travel/Mode of transport
-Travel/Occupancy
-Transport/Passenger efficiency
-Transport/Passenger technology

Some plots are unaffected by changes, but « Passenger GHG emissions per mode » is always affected.

Changing the lever Boundary conditions/Demographics & long-term / Population affects all plots in the sub-tabs mentioned above.

Pierre let me know if I forgot something or if questions come up in the following days.

Best,
Paola
