# SOLAR FARM ENERGY PRODUCTION SIMULATOR
#### Video Demo:  [CS50P Final Project 2024 - Solar Farm Energy Production Simulator](https://youtu.be/WAlqNmj93tU)

#### Files in project:
* project.py (The whole program exists in this file. Contains 6x functions, 1x class (With attributes and methods) in addition to main().)
* test_project.py (Contains tests for all 6x functions.)
* requirements.txt (List of pip-installable libraries used in program.)
* README.md (This file your reading now or previewing.)

> [!IMPORTANT]
> In order to use this program you have to obtain your own free-tier API Key from Solcast. Here is the setup instructions:
> 1. Obtain an API Key: Sign up at [Solcast](https://toolkit.solcast.com.au/register?_ga=2.227312413.1484810716.1726757064-941402816.1720113127&_gl=1%2a1c1qtva%2a_gcl_au%2aMTQwNTcxNDE5Ni4xNzIwMTEzMTI3%2a_ga%2aOTQxNDAyODE2LjE3MjAxMTMxMjc.%2a_ga_BYH3TC3R79%2aMTcyNjc1OTIyOS4xOS4wLjE3MjY3NTkyMjkuMC4wLjA) and choose “Researcher” to get a free-tier API Key.
> 2. Create an env File: In the root directory of the project, create a file named ".env"
> 3. Add Your API Key: Inside the env file, add the following line:
API_KEY=your_api_key_here
> 4. Load Environment Variables: Ensure these requirements are satisfied:
> * Library is installed: Make sure to pip install python-dotenv
> * Import of libraries at top of file: from dotenv import load_dotenv & import os
> * main() has these lines: load_dotenv() & api_key = os.getenv('API_KEY')

#### Description:

My project is a tool to simulate, estimate and visualise the electric energy production potential of any solar panel / solar farm location in the world, based on coordinates, size of solar panel area and solar panel specifications.
The project currently has no front-end / user interface and has to be operated within a code environment.

This is achieved through several steps handled by functions and classes. All stages will be explained in further detail later.:
#### Step 1: Fetch user input.
#### Step 2: Fetch historical ambient temperature and solar irradiance data for the provided location and time period through an API call (Solcast).
#### Step 3: Manipulate the years of data collected to get monthly irradiance totals and ambient temperature averages through the years, as well as some other values used in further calculations.
#### Step 4: Calculate actual electric energy production. Achieved by running the raw irradiance and temperature data through a SolarPanel class / object's calculation methods using certain formulas. (Simulation step.)
#### Step 5: Visualise data. Take the month by month energy production data and visualise them using plots. Either a year by year totals plot, or month by month (Over the years) average plot, depending on user input.

Factors taken into consideration:
- Solar irradiance conditons for the location
- Tilt angle of solar panels (Panels being fixed tilt and not sun tracking)
- Weather and cloud coverage
- Real adjusted solar panel efficency as a product of ambient air temperature, heating effects of panel absorbing irradiance and panel specifications.
- Power conversion / inverter loss from DC to AC current. (4%)

Factors not taken into consideration:
- Terrain shading
- Snow or dust coverage on panels
- Reduction in efficiency of modules due to degradation over the years. This program makes calculation based on new / original state of panels.
- Heat dissipation from power cables and grid inefficiencies.

The estimations of this program will therefore be on the slight optimistic side of real yield.

Detailed explanation of functions and class:

#### Step 1 - Fetch user input:
Responsible function: get_variables()

I debated whether to do this through the use of Command Line Arguments (CLA) and parsing the inputs. I ultimately, due to the number of input values,
decided that it would be cleaner and easier input control to make use of the input() function and consecutively prompt the user this way.
This function recieves all the relevant input variables for the program;
- "latitude" and "longitude" (Coordinates). These are validated through the use of a regex pattern. (These are also converted to the coordinates' address equivalent using reverse geocoding, through the Geopy library, which the function also returns as "location".)
- "years". Number of years back from current year to fetch data for. (Must be between 2 and 8 years.)
- "panel_area". The total solar panel area size in square meters.
- "STC_eff". The solar panel model used in the simulation / estimation's efficiency in Standard Test Conditions. Provided in percentage and is stated by the manufacturer in the documentation of the panel.
- "temp_coeff". The temperature coefficient of PMax. This is how much the module efficiency is affected by cell temperature variations. Also state by manufacturer in the documentation of the panel.

#### Step 2 - Fetch data:
Responsible functions: generate_date_ranges() and get_solar_data()

This is the part of the code where the API call is made for the historical data used in the estimations. I debated several data providers and ultimately landed on Solcast (https://www.solcast.com/) as the best one.
They seemed to provide the most accurate data, had clear instructions on how to use their API and provided what I was looking for, which was historical data. The only downside is they require you to
register an account with them in order to get an API Key. This generally comes at a price, but in the context of research (Which I deemed this project) they provide a free API Key with a request limit. (See instruction on how to set this up).

The provider has a limit of 1 month of historical data per API request, which required me to create a generator function (generate_date_ranges()) to feed the fetching function (get_solar_data()), in order to
fetch several years of data at a time. The generator function builds strings containing the start and end of the time interval to fetch data for, and increments through the years, one month at a time for the provided number of years.
It yields one interval at a time inside a loop, where get_solar_data() constructs the appropriate query string and makes the API call.
As for the actual data I'm collecting, the criteria is provided in the query string. The irradiance type I'm retrieving is GTI (Global Tilted Irradiance), where weather, like cloud coverage etc,
is accounted for. It also takes into account the tilt angle of the panels. In my case Solcast handles this for me by automatically calculating an optimising the tilt angle based on the longitude.
What I recieve is then the some of the most accurate and realistic data on solar irradiance available, location and tilt angle taken into account. Additionally also ambient temperature used later on.
All this data is fetched in JSON format, and "Normalized", meaning cleaned up and structured in DataFrames using the Pandas library for easier manipulation. With a data resolution of 30 minute increments, spanning the years provided.


#### Step 3 - Manipulate data for monthly values:
Responsible function: calculate_monthly_data()

This function's task is to manipulate / peform calculations on the data provided by the get_solar_data() to turn the short interval input data into relevant monthly data.
It recieves a Pandas DataFrame from the the get_solar_data(), peforms aggregations using features of the Pandas library and returns a dataframe contaning (among other values) the **monthly** values (month by month, year by year) of:
- Total monthly raw GTI irradiance
- Average monthly daytime temperature (Daytime because nightime temps are irrelevant, as active hours of a solar panel are only during daytime.)
- Average hourly GTI by month.

#### Step 4 - Calculate / simulate actual electric energy production:
Responsible class: SolarPanel

This part of the program happens in main() and makes use of the SolarPanel class.
For accurate energy estimates we need to take several factors into consideration. A simple calculation of energy yield is raw solar irradiance * solar cell efficiency rating * area of solar panel(s).
However the solar cell's real efficiency depends on the temperature of the cell itself, which is impacted by irradiance (sun energy) at the given moment, and ambient temperature. I did not however
take into account the cooling effects of the wind in this calculation, which would be miniscule.
As the temperature of PV cells increase, the output drops. Additionally conversion loss from DC to AC current is accounted for at 4% loss.
Calculating the cell temperature, then calculating the adjusted actual efficiency based off of this, then using this adjusted efficience to calculate real yield is this class / objects mission in life.
The logic of the simulation is simply to apply virtual sun and ambient temperature to a virtual solar panel, and using photovoltaic formulas to produce the energy yield.
SolarPanel represents it's real life counterpart; A solar panel, containing all relevant attributes and functionality of a solar panel:

Attributes: (Some are standard constants used in PV testing, some are variables provided by the user.)
Standard constants used in PV testing
- NOCT: Nominal Operating Cell Temperature. Typically 45 degrees Celsius. (Stated by cell manufacturer).
- GNOCT: Nominal Operating Cell Temperature irradiance. Typically 800 W/m2. (Stated by cell manufacturer).
- STC Temperature: Standard Test Condition temperature. Typically 25 degrees Celsius. (Stated by cell manufacturer).

Variables provided by the user through input() that varies between solar panel models:
- STC Efficiency: Module efficiency at Standard Test Conditions in percentage (%). Varies by cell type. (Stated by cell manufacturer).
- Temperature coefficient: Temperature coefficient of PMax. (How much module efficiency is affected by cell temp variations). Varies by cell type. (Stated by cell manufacturer).

Methods: (Making use of photovoltaic formulas.)
- calculate_celltemp():
Formula used: Cell Temp = Ambient Temp + (GTIavg / GNOCT) × (NOCT−20°C)
- calculate_efficiency():
Formula used: Adjusted efficiency = STC Efficiency × (1 − Temp Coefficient / 100 × (Cell Temp − STC Temp))
- calculate_yield():
Formula used: Y = GTI × Panel Area × Adjusted efficiency x Inverter efficiency

This calculation step happens in a loop, iterating over every month in the provided dataframe. Ie. if the user called for 5 years of historic data, every month
throughout those years will have their own energy yield value calculated based on the steps above. The results are added back into the dataframe in it's own column.

#### Step 5 - Visualise data:
Responsible function: plot_data()

The last step in the program is to plot / visualise the data. This function takes (among other) a parameter where the user decides what data they want visualised, between yearly totals or monthly averages. In this programs use case both are handled for better insight.
The dataframe containing the calculated monthly (throughout the years) yields is passed to the function. The function creates a common figure for both plots, then depending on the plot_type parameter
utilises a fork in the road for the appropriate plot to be created. The further aggregation of the yield data is done using Seaborn's built in aggregation tools.
Units of measurements are accounted for. The plot type of use is the barplot in order to stack the data up against each other to properly visualise variations over the years or the months.
I (with the help of the CS50 Duck Debugger) created a custom color pallette for the bars based on ranking of the bars. Tallest bar is darkest, shortest bar is lightest. This design decision was
taken in order for the user be able to easily spot value / height differences between the bars.
Initially this last step of aggregation was done again using the Pandas library, however the Seaborn library had a neat feature called "error bars". This would only be accessible if
the aggregation was done internally in Seaborn. The error bare can be setup in several ways. I set it up to showcase the spread of the underlying data for the month plot. Since the
month plot shows monthly averages (Ie. the average of the past 5 August months if 5 years of data is used), I thought it to be interesting to further visualise to the user the spread of the underlying data this way.
So the "error bar" is added as a bar on top of the main bars, where the top represents the highest yielding August (for example), and the bottom represents the lowest yielding August.
This way the user has an idea of the average for the month and what to expect, but also the extremes one can expect from each individual month.
An info box with key values is also added to the plot to give a quick overview over the most relevant values in both plot types. Location of the solar farm. Size of the solar farm
and key yield values like Max yielding year / month, min yielding year / month and average yield for the years / months. A horizontal dashed line is also added over the bars in both plot types
to visualise the average year / month, and give the user a visual of whether the bar (year or month) is performing below or above the total average.
The figure of each plot type is then returned from the function, and (by main()) stored in a PDF file, ready to be downloaded by the user.
