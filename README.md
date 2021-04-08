# Production-Automation
Two simple apps for simulating communicating with test devices.

## Python Test Controller
### Requirements
This app requirements were to be built with Python 3 and PyQt and allowed the user to:
- connect with a test device at a specified IP address on a specified port
- define test duration
- start a test
- force a test to stop early
- see a live plot of measured values during the test
- write test results to a PDF containing the plotted data and some information about the test

### Building the Python Environment
Python 3.8.5 was used in the development and testing of this device, but an older version may suffice.
A conda virtual environment was also used in development of this app which can be found under python/RLtester.yml
If anaconda is installed, this environment can be recreated and then activated using:
```
conda env create -f RLtester.yml
conda activate RLtester
```

### Running the TestController
To run the testController.py, simply call the script using: 
```
python3 testController.py
```
The interface is very basic and simple and should be self explanatory, allowing the required functionality some basic status messages for the user to observe operation.

## C++ Simulated Device (RLSimDevice)
### Requirements 
This app requirements were to be built using C++ with the following behaviour:
- The device listens for UDP packets. Unknown messages are ignored by the device.
- The device sends responses to the IP address and port number from which the request was received.
- All messages are strings consisting of keywords and values separated by semicolons. All numerical values are integers. The strings are encoded using ISO-8859-1 (Latin 1).
- Packet descriptions are as follows (uppercase indicates literal values, lowercase indicates values to be filled in as appropriate):
- Start a test of the given duration, with status reporting at the specified rate:
"TEST;CMD=START;DURATION=s;RATE=ms;"
DURATION is test duration, in seconds
RATE is how often the device should report status during the test, in milliseconds
- The test will stop after the given duration, or when device receives the stop command:
"TEST;CMD=STOP;"
- The start and stop commands will result in one of the following responses:
"TEST;RESULT=STARTED;" - the test was started successfully
"TEST;RESULT=STOPPED;" - the test was stopped successfully
"TEST;RESULT=error;MSG=reason;" - a test was already running, or was already stopped
- While the test is running, the device will send status messages at the specified rate:
"STATUS;TIME=ms;MV=mv;MA=ma;"
TIME is milliseconds since test start
MV, MA are millivolts and milliamps, respectively.
- After the test has finished (or if the test was stopped), the device will send one final status message:
"STATUS;STATE=IDLE;"

### Building from Source C++
The C++ app RLSimDevice requires a C++11 Compiler, and CMake version 3.10 or higher. 
Dependencies are the standard library and two extra Qt5 libraries Qt5Core and Qt5Network.
Follow the commands below to build if the above are satisfied.

```
git clone https://github.com/HarryHebden/Production-Automation.git
cd Production-Automation/cpp
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

### Running
To run the RLSimDevice app make sure to give it a UDP Port number to listen to on the command line, then use Ctrl+C to exit the device when finished.
```
./RLSimDevice 49181
```
