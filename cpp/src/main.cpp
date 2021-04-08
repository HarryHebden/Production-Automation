/*
SimDevice is an application built by request of RL as part of a job application.
This application should:
- take an input port number to listen to
- listen to that port number for UDP packets, ignoring unknown messages
- sends responses to the IP address and port number from which the request was recieved.
- all messages are strings consisting of keywords and values(integers) separated by semicolons.
- strings are encoded using ISO-8859-1 (Latin 1)
  Example Test start string:
    "TEST;CMD=START;DURATION=s;RATE=ms"
  After the test duration, or if given a stop signal:
    "TEST;CMD=STOP;"
  The start and stop commands result in the following responses:
    "TEST;RESULT=STARTED;"
    "TEST;RESULT=STOPPED;"
    "TEST;RESULT=error;MSG=reason;"
  Status messages are sent at the specified rate, examples:
    "STATUS;TIME=ms;MV=mv;MA=ma;"
  After the test has finished(or if stopped), the device sends one final status message:
  "STATUS;STATE=IDLE;"
Authored by Harry Hebden 2021
*/

#include <iostream>
#include <string>
#include <stdexcept>
#include <QCoreApplication>
#include <QObject>
#include <QtNetwork/QUdpSocket>
#include <QByteArray>
#include <QTextCodec>
#include <thread>
#include <chrono>
#include <signal.h>
#include "SimDevice.h"

void signal_callback_handler(int signum)
{
  std::cout << "[INFO]: Caught Signal: " << signum << "\n";
  std::exit(signum);
}

int main(int argc, char *argv[])
{
  signal(SIGINT, signal_callback_handler);

  if (argc < 2)
  {
    std::cout << "[ERROR]: Not enough input arguments. Please input a UDP port number to listen to.\n" ;
    return -1;
  }

  int UDP_port_num = -1;
  std::string arg = argv[1];
  try {
    std::size_t pos;
    UDP_port_num = std::stoi(arg, &pos);
    if (pos < arg.size())
    {
      std::cerr << "[ERROR]: Incorrect input; Trailing characters after number: " << arg << '\n';
      return -1;
    }
  }
  catch (std::invalid_argument const &ex)
  {
    std::cerr << "[ERROR]: Incorrect input UDP Port Number - Invalid number: " << arg << '\n';
    return -1;
  }
  catch (std::out_of_range const &ex)
  {
    std::cerr << "[ERROR]: Incorrect input UDP Port Number - Number out of range: " << arg << '\n';
    return -1;
  }

  std::cout << "[INFO]: Successful setup; Listening on port: " << UDP_port_num << '\n';
  SimDevice device(UDP_port_num);

  while (true)
  {
    if (device.testStarted==true)
    {
      device.startTest();
    }
  }

  return 0;
}
