from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from datetime import datetime
import cv2
import threading
import time
import csv


app = Flask(__name__)
sent_time = time.time()
CORS(app)

reader = []
reader_index = 0
start_read_flag = 0

MIN_LENGTH_OF_DATA = 60
MOVING_AVERAGE_WINDOW = 30
DELAY_LAMP_TURN_OFF = 50 # Seconds
FREQUENCY = 0.5  # per second

# Use VideoCapture in a separate thread
class VideoCamera(object):
    """
    Represents a video camera object that captures frames from a given RTSP link.

    Attributes:
        video (cv2.VideoCapture): The video capture object.
        grabbed (bool): Indicates if a frame was successfully grabbed.
        frame (numpy.ndarray): The current frame captured by the camera.
        thread (threading.Thread): The thread used to continuously update the frame.

    Methods:
        __init__(self, rtsp_link): Initializes the VideoCamera object.
        update_frame(self): Continuously updates the frame from the video capture.
        get_frame(self): Encodes the current frame as a JPEG image and returns it.
        __del__(self): Releases the video capture object when the VideoCamera object is destroyed.
    """

    def __init__(self, rtsp_link):
        """
        Initializes the VideoCamera object.

        Args:
            rtsp_link (str): The RTSP link to the video stream.
        """
        self.video = cv2.VideoCapture(rtsp_link)
        self.grabbed, self.frame = self.video.read()
        self.thread = threading.Thread(target=self.update_frame, args=())
        self.thread.daemon = True
        self.thread.start()

    def update_frame(self):
        """
        Continuously updates the frame from the video capture.
        """
        while True:
            self.grabbed, self.frame = self.video.read()

    def get_frame(self):
        """
        Encodes the current frame as a JPEG image and returns it.

        Returns:
            bytes: The encoded frame as a JPEG image.
        """
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        frame = cv2.imencode('.jpg', self.frame, encode_param)[1].tobytes()
        return frame

    def __del__(self):
        """
        Releases the video capture object when the VideoCamera object is destroyed.
        """
        self.video.release()

def gen_frame(camera):
    """
    Generates frames from a camera stream (10 fps).

    Args:
        camera: The camera object used to capture frames.

    Yields:
        bytes: A sequence of frames in the form of bytes.

    Raises:
        None

    Example:
        >>> camera = Camera()
        >>> for frame in gen_frame(camera):
        ...     # Process the frame
        ...     pass
    """
    global sent_time
    while True:
        # To maintain 10 fps
        if time.time() - sent_time >= 0.1:
            frame = camera.get_frame()
            sent_time = time.time()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
           

camera = VideoCamera('rtsp://user:password@ip_camera:554/Streaming/Channels/101')
camera_th = VideoCamera('rtsp://user:password@ip_camera:554/Streaming/Channels/201')

@app.route('/api/video_feed')
def video_feed():
    """
    Returns a video feed from the camera (RGB stream).

    This function generates frames from the camera and returns them as a response with the appropriate MIME type.
    The frames are sent as a multipart/x-mixed-replace stream, which allows for continuous streaming of video.

    Returns:
        Response: A response object containing the video feed.

    """
    global camera
    return Response(gen_frame(camera), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/video_feed_th')

def video_feed_th():
    """
    Returns a video feed from the camera (thermal stream).

    This function generates frames from the camera and returns them as a response with the appropriate MIME type.
    The frames are sent as a multipart/x-mixed-replace stream, which allows for continuous streaming of video.

    Returns:
        Response: A response object containing the video feed.

    """
    global camera_th
    return Response(gen_frame(camera_th), mimetype='multipart/x-mixed-replace; boundary=frame')



## Showing from mp4 videos
def generate_frames_video(video):
    """
    Generates frames from a video file and yields them as a multipart/x-mixed-replace response.

    Args:
        video (cv2.VideoCapture): The video file to generate frames from.

    Yields:
        bytes: The frames of the video as a multipart/x-mixed-replace response.

    Raises:
        None

    Example Usage:
        video = cv2.VideoCapture('path/to/video.mp4')
        for frame in generate_frames_video(video):
            # Process the frame
            pass
    """
    
    last_frame = None
    fps = int(video.get(cv2.CAP_PROP_FPS))
    frame_duration = 1 / fps  # duration of each frame in seconds

    frame_count = 0
    start_time = time.time()
    while True:
        success, frame = video.read()
        frame_count += 1

        if not success:
            # If the video has ended, yield the last frame
            if last_frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + last_frame + b'\r\n')
            continue

        # Convert the image from BGR color (which OpenCV uses) to RGB color
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Encode the image as jpg
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        # Store the frame as the last frame
        last_frame = frame
        # Yield the frame in the content type multipart/x-mixed-replace with boundary frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        # Wait until it's time for the next frame
        while time.time() - start_time < frame_count * frame_duration:
            time.sleep(0.011)

@app.route('/api/test_movie')
def test_movie():
    """
    Generates a video response by calling the `generate_frames_video` function with `video1` as input.

    Returns:
        A Response object with the generated video frames, with the mimetype set to 'multipart/x-mixed-replace; boundary=frame'.
    """
    return Response(generate_frames_video(video1), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/test_movie_th')
def test_movie_th():
    """
    Generates a video response by calling the `generate_frames_video` function with `video1` as input.

    Returns:
        A Response object with the generated video frames, with the mimetype set to 'multipart/x-mixed-replace; boundary=frame'.
    """
    return Response(generate_frames_video(video2), mimetype='multipart/x-mixed-replace; boundary=frame')

video1 = cv2.VideoCapture('../Data_to_use/test1_cropped.mp4') # For Test purposes 
video2 = cv2.VideoCapture('../Data_to_use/test1_thermo_cropped.mp4') # For test Purposes


# Define the Sensor_Data class
class Sensor_Data:
    """
    A class that represents sensor data.

    Attributes:
        stored_temperature (list): A list to store temperature data.
        stored_resistance (list): A list to store resistance data.
        stored_times (list): A list to store the timestamps of the data.
        min_resistance (int): The minimum resistance value.
        moving_average_resistance (list): A list to store the moving average of resistance data.
        lamp_turn_off_index (int): The index at which the lamp turns off.
        lamp_turn_off_flag (int): A flag indicating whether the lamp has turned off.
        geling_point_flag (int): A flag indicating whether the gelling point has been reached.
        geling_point_index (int): The index at which the gelling point is reached.
        two_mins_earlier_lamp_turn_off_index (int): The index at which the lamp turns off two minutes earlier.
        slopes_after_geling_point (list): A list to store the slopes after the gelling point.
        slopes_decreaing_after_gelling_point_flag (int): A flag indicating whether the slopes are decreasing after the gelling point.
        saturation_index (int): The index at which the resistance saturates.
        saturation_flag (int): A flag indicating whether the resistance has saturated.

    Methods:
        reset_data(): Resets all the data lists and flags.
        add_data(data): Adds new data to the respective lists and processes the input data.
        add_data_test(): Adds test data to the respective lists and processes the input data.
        process_input_data(): Processes the input data and performs calculations on the data.
    """
    
    def __init__(self):
        # Initialize the lists
        self.stored_temperature = []
        self.stored_resistance = []
        self.stored_times = []
        self.min_resistance = 0
        self.moving_average_resistance = []
        self.lamp_turn_off_index = 0
        self.lamp_turn_off_flag = 0
        self.geling_point_flag = 0
        self.geling_point_index = 0
        self.two_mins_earlier_lamp_turn_off_index = 0
        self.slopes_after_geling_point = []
        self.slopes_decreaing_after_gelling_point_flag = 0
        self.saturation_index = 0
        self.saturation_flag = 0

    def reset_data(self):
        """
        Resets all the data lists and flags.
        """
        # Reset the lists
        self.stored_temperature = []
        self.stored_resistance = []
        self.stored_times = []
        self.min_resistance = 0
        self.moving_average_resistance = []
        self.lamp_turn_off_index = 0
        self.lamp_turn_off_flag = 0
        self.geling_point_flag = 0
        self.geling_point_index = 0
        self.two_mins_earlier_lamp_turn_off_index = 0
        self.slopes_after_geling_point = []
        self.slopes_decreaing_after_gelling_point_flag = 0
        self.saturation_index = 0
        self.saturation_flag = 0

    def add_data(self, data):
        """
        Adds new data to the respective lists and processes the input data.

        Args:
            data (dict): A dictionary containing the temperature and resistance data.

        Returns:
            bool: True if the data is successfully added and processed.
        """
        # Add the data to the respective lists
        self.stored_temperature.append(data['temperature'])
        self.stored_resistance.append(data['resistance'])
        # stored time is in the format of YYYY-MM-DD HH:MM:SS AM/PM in as string
        stored_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
        self.stored_times.append(str(stored_time))
        self.process_input_data()
        return True
        
    def add_data_test(self):
        """
        Adds test data to the respective lists and processes the input data.

        Returns:
            bool: True if the test data is successfully added and processed.
        """
        try:
            global reader
            global reader_index
            if start_read_flag:
                data = reader[reader_index]
                self.stored_temperature.append(float(data[2]))
                self.stored_resistance.append(float(data[1]))
                # stored time is in the format of YYYY-MM-DD HH:MM:SS AM/PM in as string
                stored_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")
                self.stored_times.append(str(stored_time))
                reader_index += 1
                self.process_input_data()
                return True
        except Exception as e:
            return jsonify({'message': 'Invalid data'}), 400
        
    def process_input_data(self):
        """
        Processes the input data and performs calculations on the data.

        Returns:
            bool: True if the input data is successfully processed.
        """
        # After MIN_LENGTH_OF_DATA datapoints, we start calculating the moving average of resistance datahistory
        if len(self.stored_resistance) > MIN_LENGTH_OF_DATA:
            # Calculate the moving average of the resistance data
            moving_average_resistance = sum(
                self.stored_resistance[-MOVING_AVERAGE_WINDOW:]) / MOVING_AVERAGE_WINDOW
            self.moving_average_resistance.append(moving_average_resistance)

            # THE NOISE IS REMOVED USING MOVING AVERAGE
            # ON THE DENOISED DATA, WE CHECK WHETHER THE SLOPE IS POSITIVE OR NEGATIVE
            # IF THE SLOPE IS POSITIVE, WE CHECK WHETHER IT WAS ALSO POSITIVE DELAY_LAMP_TURN_OFF DATA POINTS EARLIER
            # IF IT WAS POSITIVE DELAY_LAMP_TURN_OFF DATA POINTS EARLIER, WE CONSIDER THAT THE GELING POINT HAS BEEN REACHED, SO WE SEND AN ALERT
            if not self.lamp_turn_off_flag and len(self.moving_average_resistance) > int(DELAY_LAMP_TURN_OFF*FREQUENCY):
                # Check if the slope is positive
                if self.moving_average_resistance[-1] > self.moving_average_resistance[-2]:
                    # Check if the slope was also positive int(DELAY_LAMP_TURN_OFF*FREQUENCY) data points earlier
                    if self.moving_average_resistance[-(int(DELAY_LAMP_TURN_OFF*FREQUENCY))] > self.moving_average_resistance[-(int(DELAY_LAMP_TURN_OFF*FREQUENCY)+1)]:
                        
                        # Set the lamp turn off point index
                        self.lamp_turn_off_index = len(
                            self.stored_resistance) - 1
                        self.two_mins_earlier_lamp_turn_off_index = len(
                            self.stored_resistance) - 1 - int(DELAY_LAMP_TURN_OFF*FREQUENCY)
                        self.lamp_turn_off_flag = 1

            ### WE WANT TO FIND THE GELING POINT SEPERATELY FOR VISUALIZATION PURPOSES ONLY
            if not self.lamp_turn_off_flag and len(self.moving_average_resistance) > int(DELAY_LAMP_TURN_OFF*FREQUENCY):
            # Check if the slope is positive   
                if self.moving_average_resistance[-1] > self.moving_average_resistance[-2]:
                    if self.geling_point_flag == 0:
                        self.geling_point_index = len(self.stored_resistance) - 1
                    self.geling_point_flag = 1
                else:
                    self.geling_point_flag = 0
            
            # THE RESISTANCE WILL START TO INCREASE AFTER THE GELLING POINT, AND THEN AFTER SOME TIME IT SATURATES
            # IF THE RESISTANCE IS SATURATED, WE RESET THE DATA
            # THE SATURATED SLOPE IS 150 MEGAOHM PER MINUTE

            # AFTER THE GELING POINT, WE START TO TRACK THE SLOPES
            if self.lamp_turn_off_flag:
                # Check the DENOISED DATA AND CALCULATE SLOPE ON THAT
                slope = self.moving_average_resistance[-1] - \
                    self.moving_average_resistance[-int(FREQUENCY*MOVING_AVERAGE_WINDOW)-1]
                self.slopes_after_geling_point.append(slope)
                if len(self.slopes_after_geling_point) > 2:
                    # Check if the slope is decreasing
                    if self.slopes_after_geling_point[-1] < self.slopes_after_geling_point[-2]:
                        self.slopes_decreaing_after_gelling_point_flag = 1
                if self.slopes_decreaing_after_gelling_point_flag:
                    # Check if the slope is saturated
                    if slope < 150 and not self.saturation_index:
                        self.saturation_index = len(self.stored_resistance) - 1
                        self.saturation_flag = 1
        return True


# Create an instance of Sensor_Data
sensor_data = Sensor_Data()

# Define the POST endpoint

@app.route('/api/add_data', methods=['POST'])
def post_data():
    """
    Adds the data received from the request to the respective lists.

    Returns:
        A JSON response indicating the success or failure of adding the data.

    Raises:
        Exception: If the data received is invalid.

    Example Usage:
        response = post_data()
    """
    # Get the data from the request
    try:
        data = request.get_json()
    except Exception as e:
        print(e)
        return jsonify({'message': 'Invalid data'}), 400
    # Add the data to the respective lists
    sensor_data.add_data(data)

    # Return a success message
    return jsonify({'message': 'Data added successfully'}), 200


@app.route('/api/get_data', methods=['GET'])
def get_data():
    """
    Retrieves the stored resistance data along with other related information.

    Returns:
        A JSON response containing the following data:
        - 'stored_resistance': The stored resistance values.
        - 'stored_temperature': The stored temperature values.
        - 'stored_time': The stored time values.
        - 'lamp_turn_off_flag': The flag indicating if the lamp is turned off.
        - 'lamp_turn_off_index': The index at which the lamp is turned off.
        - 'two_mins_earlier_lamp_turn_off_index': The index two minutes earlier than the lamp turn off index.
        - 'saturation_flag': The flag indicating if the data has reached saturation.
        - 'saturation_index': The index at which the data has reached saturation.
        - 'moving_average_resistance': The moving average of the resistance values.
        - 'slopes': The slopes of the resistance values after the geling point.
        - 'geling_point_index': The index at which the geling point is detected.
        - 'gel_point_flag': The flag indicating if the geling point is detected.

    HTTP Status Code:
        200 (OK) - The request was successful.
    """
    # Return the stored resistance list
    # sensor_data.add_data_test() # For test purposes
    return jsonify({
        'stored_resistance': sensor_data.stored_resistance,
        'stored_temperature': sensor_data.stored_temperature,
        'stored_time': sensor_data.stored_times, 
        'lamp_turn_off_flag': sensor_data.lamp_turn_off_flag,
        'lamp_turn_off_index': sensor_data.lamp_turn_off_index,
        'two_mins_earlier_lamp_turn_off_index': sensor_data.two_mins_earlier_lamp_turn_off_index,
        'saturation_flag': sensor_data.saturation_flag,
        'saturation_index': sensor_data.saturation_index,
        'moving_average_resistance': sensor_data.moving_average_resistance,
        'slopes': sensor_data.slopes_after_geling_point,
        "geling_point_index": sensor_data.geling_point_index,
        "gel_point_flag": sensor_data.geling_point_flag
    }), 200


@app.route('/api/reset_data', methods=['GET'])
def reset_data():
    """
    Resets the stored data and sets the video frames to the beginning.

    Returns:
        A JSON response with a success message and HTTP status code 200.
    """
    global start_read_flag
    start_read_flag = 1
    sensor_data.reset_data()
    video1.set(cv2.CAP_PROP_POS_FRAMES, 0)
    video2.set(cv2.CAP_PROP_POS_FRAMES, 0)
    return jsonify({'message': 'Data reset successfully'}), 200

@app.route('/api/init_sensor_data', methods=['GET'])
def init_sensor_data():
    """
    Initializes the sensor data by resetting the data, reading the data from a text file,
    and storing it in a global variable.

    Returns:
        A JSON response containing a success message and HTTP status code 200.
    """
    sensor_data.reset_data()
    global reader
    global reader_index
    global start_read_flag
    start_read_flag = 0
    reader_index = 0
    txt_data_dir = "../Data_to_use/09.04_test1/optimold_c_716_240409_144515.txt"
    with open(txt_data_dir, 'r') as file:
        reader = list(csv.reader(file, delimiter=','))

    return jsonify({'message': 'Sensor Data initialized successfully'}), 200

########################
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
