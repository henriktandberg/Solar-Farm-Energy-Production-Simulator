import sys
import requests
import seaborn as sns
import re
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from geopy.geocoders import Nominatim
from matplotlib.backends.backend_pdf import PdfPages
from geopy.location import Location
from dotenv import load_dotenv
import os


# Constants
NOCT = 45 # Nominal Operating Cell Temperature in °C
G_NOCT = 800  # Nominal Irradiance in W/m²
STC_temp = 25 # Temperature coefficient per °C


class SolarPanel:
    def __init__(self, NOCT, G_NOCT, STC_temp, STC_eff, temp_coeff):
        self.NOCT = NOCT # Nominal Operating Cell Temperature. Typically 45 degrees Celsius. (Provided by cell manufacturer).
        self.G_NOCT = G_NOCT # Nominal Operating Cell Temperature irradiance. Typically 800 W/m2. (Provided by cell manufacturer).
        self.STC_temp = STC_temp # Standard Test Condition temperature. Typically 25 degrees Celsius. (Provided by cell manufacturer).
        self.STC_eff = STC_eff # Module efficiency at Standard Test Conditions in percentage (%). Varies by cell type. (Provided by cell manufacturer).
        self.temp_coeff = temp_coeff # Temperature coefficient of PMax. (How much module efficiency is affected by cell temp variations). Varies by cell type. (Provided by cell manufacturer).

        # Getters and setters to prevent invalid instance attributes, both upon object construction and attempts to change the attributes elsewhere.
        @property
        def NOCT(self):
            return self._NOCT

        @NOCT.setter
        def NOCT(self, NOCT):
            if NOCT != 45:
                raise ValueError("Invalid NOCT")
            else:
                self._NOCT = NOCT

        @property
        def G_NOCT(self):
            return self._G_NOCT

        @G_NOCT.setter
        def G_NOCT(self, G_NOCT):
            if G_NOCT != 800:
                raise ValueError("Invalid G_NOCT")
            else:
                self._G_NOCT = G_NOCT

        @property
        def STC_temp(self):
            return self._STC_temp

        @STC_temp.setter
        def STC_temp(self, STC_temp):
            if STC_temp != 25:
                raise ValueError("Invalid STC_temp")
            else:
                self._STC_temp = STC_temp

        @property
        def STC_eff(self):
            return self._STC_eff

        @STC_eff.setter
        def STC_eff(self, STC_eff):
            if not 10 < STC_eff < 30:
                raise ValueError("Invalid STC_eff")
            else:
                self._STC_eff = STC_eff

        @property
        def temp_coeff(self):
            return self._temp_coeff

        @temp_coeff.setter
        def temp_coeff(self, temp_coeff):
            if not -0.5 < temp_coeff < -0.3:
                raise ValueError("Invalid temp_coeff")
            else:
                self._temp_coeff = temp_coeff

    # Methods
    # Calculate cell temperature based on ambient temp and irradiance conditions
    def calculate_celltemp(self, daytemp, Hourly_GTI): # Hourly_GTI = Average hourly GTI in W
        cell_temp = daytemp + (Hourly_GTI / self.G_NOCT) * (self.NOCT - 20)
        return cell_temp # Average cell temperature for the time interval of interest.

    # Adjust STC panel efficiency to real panel efficiency based on real world cell temperature, STC cell temperature and temp coefficient
    def calculate_efficiency(self, daytemp, Hourly_GTI):
        cell_temp = self.calculate_celltemp(daytemp, Hourly_GTI)
        adjusted_efficiency = self.STC_eff * (1 - (self.temp_coeff/100) * (cell_temp - self.STC_temp))
        adjusted_efficiency = adjusted_efficiency / 100 # Efficiency in fractional value and not percentage for calculation.
        return adjusted_efficiency

    # Calculate electric energy yield based on irradiance data, size of panel area and adjusted, real panel efficiency.
    def calculate_yield(self, daytemp, Hourly_GTI, Total_GTI, panel_area): #Total_GTI = Total GTI in Wh
        adjusted_efficiency = self.calculate_efficiency(daytemp, Hourly_GTI)
        energy_yield = (Total_GTI * panel_area * adjusted_efficiency) / 1000 # Energy yield in KWh
        energy_yield = energy_yield * 0.96 # Account for 96% inverter efficiency (4% loss in DC to AC conversion)
        return energy_yield

def main():
    # Load API Key. The concept of storing the API Key in an .env file and importing using dotenv and os libraries was suggested by CS50 Duck Debugger.
    load_dotenv()
    api_key = os.getenv('API_KEY')
    # Retrieve variables for production location coordinates, number of years of historical data, size of solar farm, solar panel specifications and API Key
    latitude, longitude, location, years, panel_area, STC_eff, temp_coeff = get_variables()
    # Retrieve raw irradiance and temperature data, clean up data and return as a DataFrame
    data = get_solar_data(latitude, longitude, api_key, years)
    # Manipulate the data and create monthly averages through the years
    monthly_data = calculate_monthly_data(data)
    # Initiate SolarPanel object to simulate photovoltaic energy production
    Panel = SolarPanel(NOCT, G_NOCT, STC_temp, STC_eff, temp_coeff)
    # Simulation process. Monthy by month averaged solar irradiance data and ambient temp is applied to SolarPanel's yield calculation method, and added to yield column in dataframe.
    # Like raw sun irradiance hitting a PV panel, creating electricity
    for index, row in monthly_data.iterrows():
        monthly_data.at[index, "Energy Yield (KWh)"] = Panel.calculate_yield(row["Average Daytime Temp"], row["Average hourly GTI (W/m2)"], row["Total GTI (Wh/m2)"], panel_area)
    # Visualize the energy production yields through plots. One plot for yearly totals, and one for monthly averages (through the years).
    yearly_plot = plot_data(monthly_data, "Years", panel_area, location)
    monthly_plot = plot_data(monthly_data, "Months", panel_area, location)
    # Save bar plots to a PDF
    with PdfPages("solar-yield-analysis.pdf") as pdf:
        pdf.savefig(yearly_plot)
        pdf.savefig(monthly_plot)


def get_variables():
    ## Retrieve all variables needed for program to function, and validate them

    # Retrieves latitude and validates
    for _ in range(3):
        latitude = input("Latitude: ").strip()
        match = re.fullmatch(r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)$", latitude)
        if match:
            latitude = match.group(0)
            break
        else:
            print("Invalid latitude or format. Use decimal degrees.")
    else:
        sys.exit("Failed to provide valid latitude after 3 attempts.")

    # Retrieves longitude and validates
    for _ in range(3):
        longitude = input("Longitude: ").strip()
        match = re.fullmatch(r"^[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$", longitude)
        if match:
            longitude = match.group(0)
            break
        else:
            print("Invalid longitude or format. Use decimal degrees.")
    else:
        sys.exit("Failed to provide valid longitude after 3 attempts.")

    # The use of Nominatim module in GeoPy library for reverse geolocation was suggested in a YouTube video I watched.
    # Converts coordinates to location name for later use
    geoLoc = Nominatim(user_agent="GetLoc")
    location = geoLoc.reverse(f"{latitude}, {longitude}", language="en-gb")

    # Number of years back from current year to fetch data
    for _ in range(3):
        try:
            years = int(input("Number of years back from current year to fetch data for (integer format): ").strip())
            if not (2 <= years <= 10):
                raise ValueError
        except ValueError:
            print("Year must be an integer value between 2 and 10.")
        else:
            break
    else:
        sys.exit("Failed to provide valid year after 3 attempts.")

    # Fetch size of solar farm in m2
    for _ in range(3):
        try:
            panel_area = int(input("Total panel area in m2: ").strip())
            if panel_area < 0:
                raise ValueError
        except ValueError:
            print("Panel area must be a positive integer.")
        else:
            break
    else:
        sys.exit("Failed to provide valid total panel area after 3 attempts.")


    # Fetch Standard Test Condition module efficiency
    for _ in range(3):
        try:
            STC_eff = float(input("Module efficiency at standard test conditions (%): ").strip(" %"))
            if not 10 < STC_eff < 30:
                raise ValueError
        except ValueError:
            print("Module efficiency at STC must be a value between 10 and 30.")
        else:
            break
    else:
        sys.exit("Failed to provide valid module efficiency after 3 attempts.")

    # Fetch Temperature coefficient of PMax
    for _ in range(3):
        try:
            temp_coeff = float(input("Temperature coefficient of PMax(% per degree celsius): ").strip(" %"))
            if not -0.5 < temp_coeff < -0.3:
                raise ValueError
        except ValueError:
            print("Temperature coefficient of PMax must be a value between -0.5 and -0.3.")
        else:
            break
    else:
        sys.exit("Failed to provide valid temperature coefficient of PMax after 3 attempts.")


    return latitude, longitude, location, years, panel_area, STC_eff, temp_coeff


def generate_date_ranges(years):
    ## Generator function to feed "start" and "end" parameteres for the API call.
    # Each parameter set / date range representing one month of data. The generator counts backwards "years" number of years (provided by the year parameter) from the current year.

    # Validate function argument
    if not isinstance(years, int):
        raise TypeError("Years parameter expects an integer.")
    if not 2 <= years <= 10:
        raise ValueError("Year must be an integer value between 2 and 10.")

    # Generates the start/end parameters and yields them.
    start_year = date.today().year - years
    start_date = datetime(start_year, 1, 1)
    end_date = start_date + relativedelta(years=years) - timedelta(days=1)
    current_start = start_date
    while current_start < end_date:
        current_end = current_start + relativedelta(months=1) - timedelta(seconds=1)
        if current_end > end_date:
            current_end = end_date.replace(hour=23, minute=29, second=59)
        yield current_start.strftime("%Y-%m-%dT%XZ"), current_end.strftime("%Y-%m-%dT%XZ")
        current_start = current_end + timedelta(seconds=1)


def get_solar_data(latitude, longitude, api_key, years):
    ## Retrieves historical ambient temperature and irradiance data from API (1 month at a time, with data in 30 minute intervals) for the provided duration.
    ## Creates a pandas dataframe of it for easier data manipulation. Irradiance type is GTI (Global Tilted Irradiance), where both weather conditions and tilt angle of panel is considered.

    # Validate function arguments
    match = re.fullmatch(r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)$", latitude)
    if match:
        latitude = match.group(0)
    else:
        raise ValueError("Invalid latitude or format. Use decimal degrees.")

    match = re.fullmatch(r"^[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$", longitude)
    if match:
        longitude = match.group(0)
    else:
        raise ValueError("Invalid longitude or format. Use decimal degrees.")

    if not isinstance(years, int):
        raise TypeError("Years parameter expects an integer.")
    if not 2 <= years <= 10:
        raise ValueError("Year must be an integer value between 2 and 10.")

    # Build query strings, make API calls and store fetched JSON data in a list
    all_data = []
    url = "https://api.solcast.com.au/data/historic/radiation_and_weather?"
    for start, end in generate_date_ranges(years):
        payload = {
            "latitude": latitude,
            "longitude": longitude,
            "output_parameters": ["gti", "air_temp"],
            "array_type": "fixed",
            "start": start,
            "end": end,
            "format": "json",
            "api_key": api_key,
            }
        # Store all JSON data in one list
        response = requests.get(url, params=payload)
        if response.status_code == 200:
            all_data.append(response.json())
        else:
            raise requests.HTTPError("Failed to fetch data either due to wrong API key or a problem with the API sever.")

    # Normalize the list of data as one dataframe per month (list element), and store them one by one in a new list of data frames.
    normalised_data = []
    for month in range(len(all_data)):
        normalised_data.append(pd.json_normalize(all_data[month]["estimated_actuals"]))
    # Concatenate all the dataframes into one big dataframe called "df"
    df = pd.concat(normalised_data, ignore_index=True)

    # Rename columns, and add Sun Hours column
    df.columns = ["Air Temp", "W/m2 (GTI)", "Period end", "Period"]
    df["Sun Hours"] = 0
    # Converts Period end column in dataframe into a datetime object for easier date/time manipulation
    df["Period end"] = pd.to_datetime(df["Period end"])
    # Removes the timezone information (UTC timezone offset) for groupby method to work by accessing dt (datetime) attributes / methods of dataframe
    df["Period end"] = df["Period end"].dt.tz_localize(None)
    # Counts up the sun hours of the dataframe using pandas internal optimizations. Adds 0.5 sun hours because each row represents a 30 minute interval.
    df["Sun Hours"] = df["Sun Hours"].astype(float)
    df.loc[df["W/m2 (GTI)"] > 0, "Sun Hours"] = 0.5
    # Initializes Daytime Temp column, then populates it with only daytime temperatures extracted from the Air Temp column. Used for more precise Cell Temp calculations during production hours.
    df["Daytime Temp"] = None
    df.loc[df["W/m2 (GTI)"] > 0, "Daytime Temp"] = df["Air Temp"]
    return df


def calculate_daily_data(df): # Note: Not currently used in main(), but available for use. Plot_data will need adjustment.
    # CS50 Duck Debugger in addition to online resources like stackoverflow.com and YouTube helped assist me on how to use the Pandas library.
    # Performs calculations on the short interval input data for daily temperature averages, total irradiance, total sun hours and average hourly GTI
    # The model used for calculating average temperature and average hourly GTI is based on only using data during sun hours for more accurate estimations.

    # Validate correct function usage
    if not isinstance(df, pd.DataFrame):
        raise TypeError("calculate_daily_data's df parameter expects a pandas.DataFrame object as input.")

    # Groups the data day by day, month by month, year by year and calculates the daily number of sun hours. Daytime temp and GTI is sumed for later calculations.
    daily_df = df.groupby([df["Period end"].dt.year, df["Period end"].dt.month, df["Period end"].dt.day]).agg({
    "Daytime Temp": "sum", # Total of daytime temperature values
    "W/m2 (GTI)": "sum",  # Total GTI per day
    "Sun Hours": "sum"}) # Total sun hours per day

    # Calculate the averaged daytime temperature by first transorming the data to hourly values (*= 0.5) as original data is in 30 minute intervals.
    # Then divide that number by the number of daily sun hours.
    daily_df["Daytime Temp"] *= 0.5
    daily_df["Daytime Temp"] = daily_df["Daytime Temp"] / daily_df["Sun Hours"]

    # Convert GTI from W to Wh by multiplying by 0.5 (since each interval is 30 minutes) for the total daily GTI
    daily_df["W/m2 (GTI)"] = daily_df["W/m2 (GTI)"].astype(float)
    daily_df["W/m2 (GTI)"] *= 0.5

    # Renames the columns to totals and averages
    daily_df = daily_df.rename(columns={"W/m2 (GTI)": "Total GTI (Wh/m2)", "Sun Hours": "Total Sun Hours", "Daytime Temp": "Average Daytime Temp"})
    # Renames indexes to Year, Month, Day
    daily_df = daily_df.rename_axis(["Year", "Month", "Day"])

    # Calculate daily average hourly GTI for the cell temp calculation
    # OBS: Potential division by zero. Handle cases where sun hours might be zero
    daily_df["Average hourly GTI (W/m2)"] = None
    daily_df["Average hourly GTI (W/m2)"] = daily_df["Total GTI (Wh/m2)"] / daily_df["Total Sun Hours"]

    # Replace potential "None" values in "Average hourly GTI (W/m2)" (Due to zero division if Total Sun Hours = 0 at some point) with 0.
    daily_df["Average hourly GTI (W/m2)"] = daily_df["Average hourly GTI (W/m2)"].fillna(0)

    # Initialize Energy Yield column for later calculation
    daily_df["Energy Yield (KWh)"] = None

    return daily_df


def calculate_monthly_data(df):
    # CS50 Duck Debugger in addition to online resources like stackoverflow.com and YouTube helped assist me on how to use the Pandas library.
    # Performs calculations on the short interval input data for monthly temperature averages, total irradiance, total sun hours and average hourly GTI
    # The model used for calculating average temperature and average hourly GTI is based on only using data during sun hours for more accurate estimations.

    # Validate correct function usage
    if not isinstance(df, pd.DataFrame):
        raise TypeError("calculate_monthly_data's df parameter expects a pandas.DataFrame object as input.")

    # Groups the data month by month, year by year and calculates monthly values of average daily Daytime Temp, total daily GTI and total daily Sun Hours
    monthly_avg_df = df.groupby([df["Period end"].dt.year, df["Period end"].dt.month]).agg({
    "Daytime Temp": "sum",  # Monthly total of daytime temperature values
    "W/m2 (GTI)": "sum",  # Total GTI per month
    "Sun Hours": "sum"}) # Total sun hours per month

    # Calculate the averaged monthly temperature by first transorming the data to hourly values (*= 0.5) as original data is in 30 minute intervals.
    # Then divide that number by the number of monthly sun hours.
    monthly_avg_df["Daytime Temp"] *= 0.5
    monthly_avg_df["Daytime Temp"] = monthly_avg_df["Daytime Temp"] / monthly_avg_df["Sun Hours"]

    # Convert GTI from W to Wh by multiplying by 0.5 (since each interval is 30 minutes)
    monthly_avg_df["W/m2 (GTI)"] = monthly_avg_df["W/m2 (GTI)"].astype(float)
    monthly_avg_df["W/m2 (GTI)"] *= 0.5

    # Renames the columns to totals and averages
    monthly_avg_df = monthly_avg_df.rename(columns={"W/m2 (GTI)": "Total GTI (Wh/m2)", "Sun Hours": "Total Sun Hours", "Daytime Temp": "Average Daytime Temp"})
    # Renames indexes to Year, Month, Day
    monthly_avg_df = monthly_avg_df.rename_axis(["Year", "Month"])

    # Calculate monthly average hourly GTI for the cell temp calculation
    monthly_avg_df["Average hourly GTI (W/m2)"] = None
    monthly_avg_df["Average hourly GTI (W/m2)"] = monthly_avg_df["Total GTI (Wh/m2)"] / monthly_avg_df["Total Sun Hours"]

    # Replace potential "None" values in "Average hourly GTI (W/m2)" (Due to zero division if Total Sun Hours = 0 at some point) with 0.
    monthly_avg_df["Average hourly GTI (W/m2)"] = monthly_avg_df["Average hourly GTI (W/m2)"].fillna(0)

    # Initialize Energy Yield column for later calculation
    monthly_avg_df["Energy Yield (KWh)"] = None

    return monthly_avg_df


def plot_data(df, plot_type, panel_area, location):

    # CS50 Duck Debugger in addition to online resources like stackoverflow.com and YouTube helped assist me on how to use the Seaborn and Matplotlib library.
    # Validate correct function usage
    if not isinstance(df, pd.DataFrame):
        raise TypeError("plot_data function must take a Pandas DataFrame object as an argument for the df parameter.")

    elif not isinstance(plot_type, str):
        raise TypeError("plot_data parameter plot_type expects a string.")

    elif plot_type not in ["Months", "Years"]:
        raise ValueError("plot_data parameter plot_type must either be Months or Years.")

    elif not isinstance(panel_area, int):
        raise TypeError("plot_data parameter panel_area expects an integer.")

    elif panel_area < 0:
        raise ValueError("plot_data parameter panel_area must be a positive integer.")

    elif not isinstance(location, Location):
        raise TypeError("plot_data parameter location must take a geopy.location.Location object as an argument.")


    # Reset the index of the dataframe for easier manipulation
    df_reset = df.reset_index()
    month_map = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'}
    df_reset["Month"] = df_reset["Month"].map(month_map)

    # General settings for the plot
    # Adjust the figure size
    plt.figure(figsize=(12, 9))

    # Increase resolution of figure
    plt.rcParams["figure.dpi"] = 360

    # Set gridstyle
    sns.set_style("whitegrid")

    if plot_type == "Years":
        # Group data by year and get the highest yield year
        yearly_totals = df_reset.groupby("Year")["Energy Yield (KWh)"].sum()
        max_year = yearly_totals.max()

    # Change unit of measurement to approprate unit and recalculate values
        if max_year >= 1000:
            df_reset["Energy Yield (KWh)"] = df_reset["Energy Yield (KWh)"] / 1000
            unit = "MWh"
        elif max_year >= 1000000:
            df_reset["Energy Yield (KWh)"] = df_reset["Energy Yield (KWh)"] / 1000000
            unit = "GWh"
        else:
            unit = "KWh"

        # Rename column for clarity
        energy_yield_column = f"Energy Yield ({unit})"
        df_reset = df_reset.rename(columns={"Energy Yield (KWh)": energy_yield_column})

        # Get calculated values in correct unit of measurement
        yearly_totals = df_reset.groupby("Year")[energy_yield_column].sum()
        max_year = yearly_totals.max()
        average_year = yearly_totals.mean()
        min_year = yearly_totals.min()

        # Creates a color palette that adjusts color hue based on height ranking of bars. Tallest = darkest, shortest = lightest.
        ranks = yearly_totals.rank().sub(1).astype(int).array
        palette = sns.color_palette("Blues_d", len(ranks))
        palette_list = np.array(palette)[ranks].tolist()

        # Create the plot. sns.barplot() does the aggregation, which is set to sum (estimator="sum")
        barplot = sns.barplot(x="Year", y=energy_yield_column, hue="Year", palette=palette_list, data=df_reset, estimator="sum", errorbar=None, legend=False)
        barplot.set_title("Total Solar Energy Production Yield by Year", fontsize=16)
        barplot.set_ylabel(f"Total Energy Yield ({unit})")
        plt.xlabel("")
        sns.despine(left=True)

        # Increase the "roof" of the plot
        plt.ylim(0, barplot.get_ylim()[1] * 1.3)

        # Customize grid and locators
        plt.grid(True, which="both", axis="both", alpha=0.3)
        if max_year > 100:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(50))
        elif 0 <= max_year <= 10:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(0.5))
        elif 50 <= max_year <= 99:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(5))
        elif 10 < max_year <= 49:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(2.5))

        # Add yield annotations for the bars
        for p in barplot.patches:
            barplot.annotate(format(p.get_height(), '.2f'),
                     (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha = 'center', va = 'center',
                     xytext = (0, 9),
                     textcoords = 'offset points')

        # Add a horizontal line to visualize the average value of the bars
        barplot.axhline(average_year, color='gray', linestyle='--')

        # Add textbox with max, min and avg values of all yield data
        figure = barplot.get_figure()
        figure.text(0.15, 0.78, f"Location: {location}\nSize of Panel Area: {panel_area} m²\nHighest Year: {max_year:.2f} {unit}\nLowest Year: {min_year:.2f} {unit}\nAvg (Dashed line): {average_year:.2f} {unit}", transform=figure.transFigure, bbox=dict(facecolor='white', boxstyle='round,pad=1', alpha=0.9))

        # Return whole figure
        return figure

    elif plot_type == "Months":
        # Return monthly average energy yields across years

        # Get max average month yield across years before adjusting to appropriate unit of measurement
        monthly_averages = df_reset.groupby("Month")["Energy Yield (KWh)"].mean()

        max_average_month = monthly_averages.max()

        # Change unit of measurement to approprate unit and recalculate values
        if max_average_month >= 1000:
            df_reset["Energy Yield (KWh)"] = df_reset["Energy Yield (KWh)"] / 1000
            unit = "MWh"
        elif max_average_month >= 1000000:
            df_reset["Energy Yield (KWh)"] = df_reset["Energy Yield (KWh)"] / 1000000
            unit = "GWh"
        else:
            unit = "KWh"

        # Rename column for clarity
        energy_yield_column = f"Energy Yield ({unit})"
        df_reset = df_reset.rename(columns={"Energy Yield (KWh)": energy_yield_column})

        # Get average monthly yield, max yield and min yield (Across the years, in correct unit of measurement)
        monthly_averages = df_reset.groupby("Month")[energy_yield_column].mean()
        max_month = monthly_averages.max()
        average_month = monthly_averages.mean()
        min_month = monthly_averages.min()
        # Reindex to ensure the correct order of the months in monthly_averages for the ranking in next step
        monthly_averages = monthly_averages.reindex(["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])

        # Creates a color palette that adjusts color hue based on height ranking of bars. Tallest = darkest, shortest = lightest.
        ranks = monthly_averages.rank().sub(1).astype(int).array
        palette = sns.color_palette("Blues_d", len(ranks))
        palette_list = np.array(palette)[ranks].tolist()

        # Create the plot. sns.barplot() does the aggregation, which is set to mean by default (estimator="mean"))
        barplot = sns.barplot(x="Month", y=energy_yield_column, hue="Month", palette=palette_list, data=df_reset, errorbar=("pi", 100), legend=False)
        barplot.set_title("Average Solar Energy Production Yield By Month", fontsize=16)
        barplot.set_ylabel(f"Average Energy Yield ({unit})")
        plt.xlabel("")
        sns.despine(left=True)

        # Increase the "roof" of the plot
        plt.ylim(0, barplot.get_ylim()[1] * 1.2)

        # Customize grid and locators
        plt.grid(True, which="both", axis="both", alpha=0.3)
        if max_month > 100:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(50))
        elif 0 <= max_month <= 10:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(0.5))
        elif 50 <= max_month <= 99:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(5))
        elif 10 < max_month <= 49:
            plt.gca().yaxis.set_major_locator(plt.MultipleLocator(2.5))

        # Adjust month labels (xticklabels)
        barplot.set_xticks(range(len(barplot.get_xticklabels())))
        barplot.set_xticklabels(barplot.get_xticklabels(), rotation=45, ha='center')

        # Add a horizontal line to visualize the average value of the bars
        barplot.axhline(average_month, color='gray', linestyle='--')

        # Add textbox with max, min and avg values of all yield data
        figure = barplot.get_figure()
        figure.text(0.15, 0.78, f"Location: {location}\nSize of Panel Area: {panel_area} m²\nHighest Average Month: {max_month:.2f} {unit}\nLowest Average Month: {min_month:.2f} {unit}\nAverage Month (Dashed line): {average_month:.2f} {unit}", transform=figure.transFigure, bbox=dict(facecolor='white', boxstyle='round,pad=1', alpha=0.9))

        # Return whole figure
        return figure


if __name__ == "__main__":
    main()
