import React from "react";
import { useState } from "react";
import { useEffect } from "react";
import ReactECharts from "echarts-for-react";
import "./Dashboard.css";
import axios from "axios";

const ip_backend = "127.0.0.1";

// src={`http://${ip_backend}:5000/video_feed`}
// State to hold the temperature

let lamp_flag = false;
let saturation_flag = false;
let gel_flag = false;

let lamp_index = 0;
let saturation_index = 0;
let gel_index = 0;

const formatChartData = (data, type) => {
  console.log(data.lamp_turn_off_flag);
  let datetime = data.stored_time;
  let value;
  if (type === "temperature") {
    value = data.stored_temperature;
  } else if (type === "resistance") {
    value = data.stored_resistance;
  }
  lamp_flag = data.lamp_turn_off_flag;
  saturation_flag = data.saturation_flag;
  gel_flag = data.gel_point_flag;

  lamp_index = data.lamp_turn_off_index;
  saturation_index = data.saturation_index;
  gel_index = data.geling_point_index;

  const xAxisData = datetime;
  const seriesData = value;
  // set the min for the y-axis, its 15 if its temperature and 80 if its resistance
  const min = type === "temperature" ? 15 : 80;
  const max = type === "temperature" ? 40 : 1000;
  return {
    dataZoom: [
      {
        // Enable zooming inside the chart for the X axis
        type: "slider",
        filterMode: "none",
        xAxisIndex: 0,
        start: 0,
        end: 100,
        min,
        max,
      },
      {
        // Enable zooming inside the chart for the Y axis
        type: "slider",
        filterMode: "none",
        yAxisIndex: 0,
        min,
        max,
      },
    ],
    tooltip: {
      trigger: "axis",
    },
    xAxis: {
      type: "category",
      data: xAxisData,
      axisLabel: {
        formatter: function (value) {
          return value.split(" ")[1];
        },
      },
    },
    yAxis: {
      type: "log",
      // min: 1,
      axisLabel: {
        formatter: "{value}",
      },
    },
    series: [
      {
        data: seriesData,
        type: "line",
        markLine: {
          symbol: "none", // Hides the symbol at the end of the line
          data: [
            {
              xAxis: !gel_flag ? 0 : gel_index, // Position of the first vertical line
              lineStyle: {
                color: "blue", // Color of the first line
              },
              label: {
                show: false, // Set to true if you want to show labels
              },
            },
            {
              xAxis: !lamp_flag ? 0 : lamp_index, // Position of the first vertical line
              lineStyle: {
                color: "red", // Color of the first line
              },
              label: {
                show: false, // Set to true if you want to show labels
              },
            },
            {
              xAxis: !saturation_flag ? 0 : saturation_index, // Position of the first vertical line
              lineStyle: {
                color: "black", // Color of the first line
              },
              label: {
                show: false, // Set to true if you want to show labels
              },
            },
          ],
        },

        smooth: true,
      },
    ],
    title: {
      text: `${type.toUpperCase()}`,
      left: "center",
    },
  };
};

const Dashboard = () => {
  const [chartDataTemperature, setchartDataTemperature] = useState(null);
  const [chartDataResistance, setchartDataResistance] = useState(null);

  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const fetchDataInit = async () => {
      try {
        const response = await axios.get(
          `http://${ip_backend}:5000/api/init_sensor_data`
        );
        // For test purposes
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchDataInit();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(
          `http://${ip_backend}:5000/api/get_data`
        );
        const data = response.data;

        setchartDataTemperature(formatChartData(data, "temperature"));
        setchartDataResistance(formatChartData(data, "resistance"));
        console.log(chartDataResistance);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    fetchData();

    const intervalId = setInterval(fetchData, 2098);
    return () => clearInterval(intervalId);
  }, []);

  const handleReset = () => {
    // Code to handle reset functionality
    const resetData = async () => {
      try {
        const response = await axios.get(
          `http://${ip_backend}:5000/api/reset_data`
        );
        setIsVisible(true);
        // Handle the response data here
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    resetData();
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-section header operator-section">
        <img src="images/logo.PNG" alt="Trygons" />
        <div className="right-elements">
          <p
            className={
              lamp_flag ? "message-placeholder-off" : "message-placeholder"
            }
          >
            {lamp_flag ? "Turn The Lamp OFF" : "Lamp must be ON"}
          </p>
          <button className="reset-button" onClick={handleReset}>
            Reset
          </button>
        </div>
      </div>
      <div className="column-container">
        <div className="left-column">
          <div className="dashboard-section">
            {isVisible && (
              <img
                className="stream"
                src={`http://${ip_backend}:5000/api/video_feed`}
                alt="Camera Stream 1"
              />
            )}
          </div>
          <div className="dashboard-section">
            {isVisible && (
              <img
                className="stream"
                src={`http://${ip_backend}:5000/api/video_feed_th`}
                alt="Camera Stream 2"
              />
            )}
          </div>
        </div>
        <div className="right-column">
          <div className="dashboard-section">
            <div className="chart-placeholder">
              {chartDataResistance && (
                <ReactECharts
                  option={chartDataResistance}
                  style={{ height: "30vh", width: "45vw", minWidth: "450px" }}
                />
              )}
            </div>
          </div>
          <div className="dashboard-section">
            <div className="chart-placeholder">
              {" "}
              {chartDataTemperature && (
                <ReactECharts
                  option={chartDataTemperature}
                  style={{ height: "30vh", width: "45vw", minWidth: "450px" }}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
