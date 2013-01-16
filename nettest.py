import subprocess
import re
import threading
import time


LOCK = threading.RLock()
RESULT_ARRAY = []
RESULT_TO_WAIT = 0

def addWaiting():
  global LOCK
  global RESULT_ARRAY
  global RESULT_TO_WAIT
  LOCK.acquire()
  try:
    RESULT_TO_WAIT += 1
  finally:
    LOCK.release()

def writeResult(result):
  global LOCK
  global RESULT_ARRAY
  global RESULT_TO_WAIT
  LOCK.acquire()
  try:
    RESULT_TO_WAIT -= 1
    RESULT_ARRAY += [result]
  finally:
    LOCK.release()

def getResult():
  global LOCK
  global RESULT_ARRAY
  global RESULT_TO_WAIT
  LOCK.acquire()
  try:
    if len(RESULT_ARRAY):
      result = RESULT_ARRAY[0]
      RESULT_ARRAY = RESULT_ARRAY[1:]
      needToWait = True
    else:
      result = None
      needToWait = bool(RESULT_TO_WAIT)
  finally:
    LOCK.release()
  return (result, needToWait)


class NetTester(threading.Thread):
  def __init__(self, address, comment = ""):
    threading.Thread.__init__(self)
    self.address = address
    self.comment = comment
    addWaiting()

  def run(self):
    result = ping(self.address, 2)
    if not result[0]:
      writeResult(self.convertResult(result))
      return
    result = ping(self.address, 12)
    writeResult(self.convertResult(result))

  def convertResult(self, result):
    replyTime = 9999999
    if result[0]:
      replyTime = result[2]
    #address, packets, received portion, rely time, comment 
    return (self.address, result[1], float(result[0]) / result[1], replyTime, self.comment)




def ping(address, count):
  handler = subprocess.Popen(
      ["ping", address, "-c " + str(count), "-i 0.5"],
      stdout = subprocess.PIPE); 

  #print handler.stdout.read()

  singleResultString = "\d+ bytes from \d+.\d+.\d+.\d+: icmp_req=\d+ ttl=\d+ time=(.*) ms\n"
  statResultString = "(\d+) packets transmitted, (\d+) received, .*% packet loss, time .*ms\n"
  statResultString2 = "rtt min/avg/max/mdev = (.*)/(.*)/(.*)/(.*) ms\n"

  singleResultPattern = re.compile(singleResultString)
  statResultPattern = re.compile(statResultString)
  statResultPattern2 = re.compile(statResultString2)

  send = 0
  received = 0
  avgTime = 0
  times = []

  while True:
    line = handler.stdout.readline()
    if not line:
      break
    
    result = singleResultPattern.match(line)
    if result:
      times += [float(result.group(1))] 
      continue;
    result = statResultPattern.match(line)
    if result:
      send = int(result.group(1))
      received = int(result.group(2))
      continue;
    result = statResultPattern2.match(line)
    if result:
      avgTime = float(result.group(2))
      continue;

  # return (number of packets received,
  #         number of packets send,
  #         average reply time,
  #         every single reply tme)
  return (received, send, avgTime, times)

def printHeader():
  print "packets  \treceived  \ttime  \taddress  \t\tcomment"

def printResult(result):
  print str(result[1]) + "\t" +\
        str("%.0f%%" % (result[2]*100)) +\
        "\t" +\
        str(result[3]) + " ms" +\
        "\t" +\
        str(result[0]) +\
        "\t\t" +\
        result[4]

def main():
  addressList = [("www.baidu.com", ""),
                 ("www.bing.com", ""),
                 ("www.163.com", "")]

  addressFile = open("address")
  if not addressFile:
    print "could not find address file."
    return

  pattern = re.compile("([\w\.]+)\s[\n]?(.*)\n")

  while True:
    line = addressFile.readline()
    if not line:
      break
    mat = pattern.match(line)
    if mat:
      #print mat.group(1)
      #print "=====" + mat.group(2)
      addressList += [(mat.group(1), mat.group(2))]
    
  for address, comment in addressList:
    tester = NetTester(address, comment)
    tester.start()

  allResult = []
  while True:
    while True:
      result, wait = getResult()
      if result:
        #printResult(result)
        allResult += [result]
      else:
        break
    if not wait:
      break
    time.sleep(0.5)

  print "==============="
  printHeader()
  allResult.sort(key = lambda x: x[3])
  for i in range(len(allResult)):
    printResult(allResult[i])
  


main()



#print ping("www.baidu.com", 4)
