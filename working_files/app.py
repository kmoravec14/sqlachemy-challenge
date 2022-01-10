import numpy as np
import pandas as pd
import datetime as dt
from datetime import datetime as dt,timedelta

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation/date/YEAR-MO-DY/<date><br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/startdate/<start><br/>" 
        f"/api/v1.0/startdate/enddate/<start>/<end>"
    )

@app.route("/api/v1.0/precipitation/date/YEAR-MO-DY/<date>")
def precipitation(date):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of precipitation for a given date"""
    # Query all measurements
    precip = session.query(measurement.date,measurement.station,measurement.prcp).filter(measurement.date == date).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all precip data from given date
    station_precip = []
    for date, station, prcp, in precip:
        precip_dict = {}
        precip_dict["prcp"] = prcp
        precip_dict["station"] = station
        precip_dict["date"] = date
        station_precip.append(precip_dict)

    return jsonify(station_precip)


@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all stations"""
    # Query all stations

    results = session.query(measurement.station).group_by(measurement.station).all()

    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(results))

    return jsonify(all_stations)

@app.route("/api/v1.0/tobs")
def temperatures():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of temperatures for last year of most active station"""
    # Query all stations

    most_active_station = session.query(measurement.station,func.count(measurement.station)).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).all()
    station = most_active_station[0].station

    latest_date = session.query(measurement.date).filter(measurement.station == station).\
        order_by(measurement.date.desc()).first()
    last_year_date = dt.strptime(latest_date[0], "%Y-%m-%d") # string to date
    last_year_date = last_year_date - timedelta(days=365) # date - days
    last_year_date = last_year_date.strftime("%Y-%m-%d") # date to string

    precip = session.query(measurement.date,measurement.prcp,measurement.station).filter(measurement.date > last_year_date).\
        filter(measurement.station == station).\
        order_by(measurement.date).all()

    session.close()

    # Create a dictionary from the row data and append to a list of all precip data from given date
    year_precip = []
    for date, prcp, station in precip:
        precip_dict = {}
        precip_dict["prcp"] = prcp
        precip_dict["date"] = date
        precip_dict["station"] = station
        year_precip.append(precip_dict)

    return jsonify(year_precip)

@app.route("/api/v1.0/startdate/<start>")
def summary_1(start):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Using the most active station id, calculate the lowest, highest, and average temperature for all data after the provided date"""
    # Query all stations - Find most active station

    most_active_station = session.query(measurement.station,func.count(measurement.station)).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).all()
    station = most_active_station[0].station

    # Query desired information

    sum_info = session.query(func.avg(measurement.tobs),func.min(measurement.tobs),func.max(measurement.tobs)).\
        filter(measurement.station == station).\
        filter(measurement.date >= start)
    
    session.close()

    # Create a dictionary from the row data and append to a list of all precip data from given date
    summary = []
    for tave, tmin, tmax in sum_info:
        sum_dict = {}
        sum_dict["tave"] = sum_info[0][0]
        sum_dict["tmin"] = sum_info[0][1]
        sum_dict["tmax"] = sum_info[0][2]
        summary.append(sum_dict)

    return jsonify(summary)

@app.route("/api/v1.0/startdate/enddate/<start>/<end>")
def summary_2(start,end):
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Using the most active station id, calculate the lowest, highest, and average temperature"""
    # Query all stations - Find most active station

    most_active_station = session.query(measurement.station,func.count(measurement.station)).\
        group_by(measurement.station).\
        order_by(func.count(measurement.station).desc()).all()
    station = most_active_station[0].station

    # Query desired information

    sum_info = session.query(func.avg(measurement.tobs),func.min(measurement.tobs),func.max(measurement.tobs)).\
        filter(measurement.station == station).\
        filter(measurement.date >= start).\
        filter(measurement.date <= end)
    
    session.close()

    # Create a dictionary from the row data and append to a list of all precip data from given date
    summary = []
    for tave, tmin, tmax in sum_info:
        sum_dict = {}
        sum_dict["tave"] = sum_info[0][0]
        sum_dict["tmin"] = sum_info[0][1]
        sum_dict["tmax"] = sum_info[0][2]
        summary.append(sum_dict)

    return jsonify(summary)

if __name__ == '__main__':
    app.run(debug=True)
