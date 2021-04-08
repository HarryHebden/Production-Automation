#ifndef SIMDEVICE_H
#define SIMDEVICE_H
#include <iostream>
#include <string>
#include <stdexcept>
#include <QObject>
#include <QtNetwork/QUdpSocket>
#include <QByteArray>
#include <QTextCodec>
#include <thread>
#include <chrono>
#include <regex>
#include <mutex>

class SimDevice
{
public:
  SimDevice(int input_UDP_port_num);
  ~SimDevice();
  void startTest();
  void stopTest();
  bool testStarted = false;

private:
  void startRead();
  void checkMessages();
  void startTestThread();
  void sendDatagram(std::string datagramText);
  void decodeStartCmd(std::stringstream &inputCmd, int &outputTestDuration, int &outputTestRate);

  std::string message = "";
  std::thread readThread;
  QUdpSocket *socket;
  QHostAddress sender;
  u_int16_t port;
  QByteArray dataToSend;
  bool continueReading = true;
  bool testStopped = false;
  bool unknownMessage = false;
  int m_UDP_port_num = -1;
};

#endif //SIMDEVICE_H
