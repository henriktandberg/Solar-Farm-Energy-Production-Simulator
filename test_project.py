from project import get_variables
from project import generate_date_ranges
from project import get_solar_data
from project import calculate_daily_data
from project import calculate_monthly_data
from project import plot_data
from project import SolarPanel
import pytest
import requests
import pandas as pd
from dotenv import load_dotenv
import os
from matplotlib.figure import Figure
from geopy.geocoders import Nominatim
from unittest.mock import patch


# The concept of storing the API Key in an .env file and importing using dotenv and os libraries was suggested by CS50 Duck Debugger.
load_dotenv()
api_key = os.getenv("API_KEY")


# The use of fixtures was a suggested approach by CS50 Duck Debugger
# Create a pytest fixture to test functions independently. Some functions in project alters and returns a new dataframe. This fixture makes sure every function can access the initial dataframe
# create the new alteration, and be tested individually. Also makes test program more efficient as API call only has to be made once.
@pytest.fixture
def solar_data():
    return get_solar_data("-33.856784", "151.215297", api_key, 2)


# The use of Nominatim module in GeoPy library for reverse geolocation was suggested in a YouTube video I watched.
# Create an instance of a Location object to use throughout tests.
@pytest.fixture
def location():
    geoLoc = Nominatim(user_agent="GetLoc")
    return geoLoc.reverse("-33.856784, 151.215297")


def test_get_variables(location):
    # The use of patch was a suggested approach by CS50 Duck Debugger.
    # Side effect is a list of inputs to all the input calls of the function. 1. = Latitude. 2. = Longitude. 3. = Years. 4. = Panel Area (m2). 5. = STC Module Efficiency. 6. = Temperature Coefficient.
    # Test valid input case
    with patch("builtins.input", side_effect=["-33.856784", "151.215297", "5", "20", "21.48", "-0.340"]):
        result = get_variables()
        expected_output = ("-33.856784", "151.215297", location, 5, 20, 21.48, -0.340)
        assert result == expected_output


def test_generate_date_ranges():
    # Test valid input cases
    try:
        list(generate_date_ranges(2))  # Edge case, lower bound
        list(generate_date_ranges(10))  # Edge case, upper bound
    except Exception as e:
        pytest.fail(f"Unexpected exception {e}")

    # Test that the function raises the correct errors for invalid input
    with pytest.raises(TypeError):
        list(generate_date_ranges("cat"))  # Not an integer

    with pytest.raises(ValueError):
        list(generate_date_ranges(1))  # Below valid range

    with pytest.raises(ValueError):
        list(generate_date_ranges(11))  # Above valid range

    # Check correct functionality. First setting up data. OBS: DATES ARE BASED ON 2024. MATCH DATES DEPENDING ON CURRENT YEAR.
    expected_firstrange_start = "2022-01-01T00:00:00Z"
    expected_firstrange_end = "2022-01-31T23:59:59Z"
    expected_lastrange_start = "2023-12-01T00:00:00Z"
    expected_lastrange_end = "2023-12-31T23:29:59Z"
    result = list(generate_date_ranges(2))
    first_range = result[0]
    last_range = result[-1]
    # Assert correct datatype
    start, end = first_range
    assert isinstance(start, str)
    assert isinstance(end, str)
    # Assert correct dates in first date range
    start, end = first_range
    assert start == expected_firstrange_start
    assert end == expected_firstrange_end
    # Assert correct dates in last date range
    start, end = last_range
    assert start == expected_lastrange_start
    assert end == expected_lastrange_end


def test_get_solar_data(solar_data):
    # Test for correct object type returned. initial_dataframe is the pytest fixture.
    assert isinstance(solar_data, pd.DataFrame)

    # Test for correct columns in object
    expected_columns = ["Air Temp", "W/m2 (GTI)", "Period end", "Period", "Sun Hours"]
    assert all(column in solar_data.columns for column in expected_columns)

    # Test inputs and that the function raises the correct errors
    # Test latitude
    with pytest.raises(ValueError):
        get_solar_data("-91", "151.215297", api_key, 2)
    # Test longitude
    with pytest.raises(ValueError):
        get_solar_data("-33.856784", "181", api_key, 2)
    # Test year parameter
    with pytest.raises(ValueError):
        get_solar_data("-33.856784", "151.215297", api_key, 15)
    # Test API Key
    with pytest.raises(requests.HTTPError):
        get_solar_data("-33.856784", "151.215297", 1, 2)


def test_calculate_daily_data(solar_data):
    # Test for correct object type returned
    daily_data = calculate_daily_data(solar_data)
    assert isinstance(daily_data, pd.DataFrame)

    # Test for correct columns in object
    expected_columns = [
        "Total GTI (Wh/m2)",
        "Total Sun Hours",
        "Average Daytime Temp",
        "Average hourly GTI (W/m2)",
        "Energy Yield (KWh)",
    ]
    assert all(column in daily_data.columns for column in expected_columns)

    # Test that the function correctly validates argument datatype / object type
    with pytest.raises(TypeError):
        calculate_daily_data("cat")


def test_calculate_monthly_data(solar_data):
    # Test for correct object type returned
    monthly_data = calculate_monthly_data(solar_data)
    assert isinstance(monthly_data, pd.DataFrame)

    # Test for correct columns in return object
    expected_columns = [
        "Total GTI (Wh/m2)",
        "Total Sun Hours",
        "Average Daytime Temp",
        "Average hourly GTI (W/m2)",
        "Energy Yield (KWh)",
    ]
    assert all(column in monthly_data.columns for column in expected_columns)

    # Test that the function correctly validates argument datatype / object type
    with pytest.raises(TypeError):
        calculate_monthly_data("cat")


def test_plot_data(solar_data, location):
    # Validate input dataframe
    df = calculate_monthly_data(solar_data)
    assert isinstance(df, pd.DataFrame)

    # Test for correct columns in input object
    expected_columns = [
        "Total GTI (Wh/m2)",
        "Total Sun Hours",
        "Average Daytime Temp",
        "Average hourly GTI (W/m2)",
        "Energy Yield (KWh)",
    ]
    assert all(column in df.columns for column in expected_columns)

    # Test that the function raises the correct errors
    # Test df parameter object type validation
    with pytest.raises(TypeError):
        plot_data("cat", "Months", 1, location)

    # Test plot_type datatype validation
    with pytest.raises(TypeError):
        plot_data(df, 15, 1, location)

    # Test correct plot_type alternative use
    with pytest.raises(ValueError):
        plot_data(df, "cat", 1, location)

    # Test panel_area datatype validation
    with pytest.raises(TypeError):
        plot_data(df, "Months", 5.5, location)

    # Test panel_area negative integer validation
    with pytest.raises(ValueError):
        plot_data(df, "Months", -15, location)

    # Test location parameter object type validation
    with pytest.raises(TypeError):
        plot_data(df, "Months", "1", "cat")

    # Mock data. This logic is handled in main() in the program.
    Panel = SolarPanel(45, 800, 25, 21.48, -0.340)
    for index, row in df.iterrows():
        df.at[index, "Energy Yield (KWh)"] = Panel.calculate_yield(row["Average Daytime Temp"], row["Average hourly GTI (W/m2)"], row["Total GTI (Wh/m2)"], 1)
    # Test for correct object type returned
    figure = plot_data(df, "Months", 1, location)
    assert isinstance(figure, Figure)
