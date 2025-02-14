# SOLAR FARM ENERGY PRODUCTION SIMULATOR
#### Video Demo:  [CS50P Final Project 2024 - Solar Farm Energy Production Simulator](https://youtu.be/WAlqNmj93tU)

#### Files in project:
* project.py (The whole program exists in this file. Contains 6x functions, 1x class (With attributes and methods) in addition to main().)
* test_project.py (Contains tests for all 6x functions.)
* requirements.txt (List of pip-installable libraries used in program.)
* README.md (This file you're reading now or previewing.)

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

This is achieved through several steps handled by functions and classes.:
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
