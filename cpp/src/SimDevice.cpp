#include "SimDevice.h"

SimDevice::SimDevice(int input_UDP_port_num) : m_UDP_port_num(input_UDP_port_num)
{
  socket = new QUdpSocket();
  socket->bind(QHostAddress::LocalHost, input_UDP_port_num);
  startRead();
}

void SimDevice::startRead()
{
  readThread = std::thread(&SimDevice::checkMessages, this);
}

void SimDevice::decodeStartCmd(std::stringstream &inputCmd, int &outputTestDuration, int &outputTestRate)
{
  while (inputCmd.good())
  {
    std::string stringBlock;
    getline(inputCmd, stringBlock, ';');
    if (stringBlock.find("DURATION") != std::string::npos)
    {
      outputTestDuration = std::stoi(stringBlock.substr(9,stringBlock.size()-1));
    }
    else if (stringBlock.find("RATE") != std::string::npos)
    {
      outputTestRate = std::stoi(stringBlock.substr(5,stringBlock.size()-1));
    }
  }
}

void SimDevice::startTest()
{
  // find duration and rate from decoded message string.
  int testDuration = -1;
  int testRate = -1;
  std::mutex mutex;
  mutex.lock();
  std::stringstream strStream(message);
  mutex.unlock();

  decodeStartCmd(strStream, testDuration, testRate);

  std::chrono::seconds testDurationSeconds(testDuration);
  auto start_time = std::chrono::system_clock::now();
  auto end_time = start_time + testDurationSeconds;
  QByteArray statusMessageBytes;
  std::stringstream statusMessageStream;
  int milliVolts = 0;
  int milliAmps = 0;

  while(testStarted)
  {
    std::chrono::duration<double, std::milli> elapsedMilliseconds = std::chrono::system_clock::now()-start_time;
    auto elapsedMillisecondsRounded = std::chrono::duration_cast<std::chrono::milliseconds>(elapsedMilliseconds);
    milliVolts = rand() % 20 - 10;
    milliAmps = rand() % 20 - 10;
    statusMessageStream.str("");
    statusMessageStream << "STATUS;TIME=" << elapsedMillisecondsRounded.count() << ";MV=" << milliVolts << ";MA=" << milliAmps << ";";
    std::string statusMessage = statusMessageStream.str();
    statusMessageBytes.clear();
    statusMessageBytes.append(statusMessage.c_str());
    socket->writeDatagram(statusMessageBytes, sender, port);
    std::this_thread::sleep_for(std::chrono::milliseconds(testRate));
    if (std::chrono::system_clock::now() > end_time) { break; }
  }

  // send final status message
  statusMessageBytes.clear();
  statusMessageBytes.append("STATUS;STATE=IDLE;");
  socket->writeDatagram(statusMessageBytes, sender, port);
  testStarted=false;
  testStopped=true;
}

void SimDevice::sendDatagram(std::string datagramText)
{
  dataToSend.clear();
  dataToSend.append(datagramText.c_str());
  socket->writeDatagram(dataToSend, sender, port);
}

void SimDevice::checkMessages()
{
  message = "";
  std::regex startCommandString("TEST;CMD=START;DURATION=[[:digit:]]+;RATE=[[:digit:]]+;");
  std::regex stopCommandString("TEST;CMD=STOP;");
  QTextCodec *codec = QTextCodec::codecForName("latin1"); //
  while(true)
  {
    if (socket->hasPendingDatagrams())
    {
      QByteArray datagram;
      datagram.resize(socket->pendingDatagramSize());
      socket->readDatagram(datagram.data(), datagram.size(), &sender, &port);
      QString recievedData = datagram.toHex();
      QString string = codec->toUnicode(datagram);
      message = string.toStdString();

      if (std::regex_match(message, startCommandString))
      {
        if (testStarted==false)
        {
          sendDatagram("TEST;RESULT=STARTED;");
          testStarted=true;
          testStopped=false;
        }
        else
        {
          sendDatagram("TEST;RESULT=ERROR;MSG=TEST ALREADY RUNNING. STOP CURRENT TEST FIRST.");
        }
      }
      else if (std::regex_match(message, stopCommandString))
      {
        if (testStarted==true && testStopped==false)
        {
          sendDatagram("TEST;RESULT=STOPPED;");
          testStarted=false;
          testStopped=true;
        }
        else
        {
          sendDatagram("TEST;RESULT=ERROR;MSG=NO TEST CURRENTLY RUNNING.");
        }
      }
    }
  }
}

SimDevice::~SimDevice()
{
  readThread.join();
  delete socket;
}
