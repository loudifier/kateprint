from pathlib import Path
from deepgram import Deepgram
import asyncio
import aiohttp
import board
import adafruit_thermal_printer
import serial
import textwrap
import time
import os

# Your Deepgram API Key
#key = Path(__file__).with_name('deepgram-key.txt')
key = Path('/boot/deepgram-key.txt')
with key.open('r') as file:
    DEEPGRAM_API_KEY = file.read().splitlines()[0]

# URL for the audio you would like to stream
#URL = 'http://stream.live.vc.bbcmedia.co.uk/bbc_world_service'
URL = 'http://127.0.0.1:8888/out.mp3'

# Printer config
#version = Path(__file__).with_name('fwversion.txt')
version = Path('/boot/fwversion.txt')
with version.open('r') as file:
    FWVERSION = float(file.read().splitlines()[0])
rate = Path(__file__).with_name('baudrate.txt')
#rate = Path('/boot/baudrate.txt')
with rate.open('r') as file:
    BAUDRATE = file.read().splitlines()[0]


async def main():
  # Initialize thermal printer
  ThermalPrinter = adafruit_thermal_printer.get_printer_class(FWVERSION)
  RX = board.RX
  TX = board.TX
  uart = serial.Serial("/dev/serial0", baudrate=BAUDRATE, timeout=3000)
  printer = ThermalPrinter(uart)
  time.sleep(5)

  # Initialize the Deepgram SDK
  deepgram = Deepgram(DEEPGRAM_API_KEY)

  # Create a websocket connection to Deepgram
  # In this example, punctuation is turned on, interim results are turned off, and language is set to US English.
  try:
    deepgramLive = await deepgram.transcription.live({ 'punctuate': True, 'interim_results': False, 'language': 'en-US', 'model': 'nova' })
  except Exception as e:
    print(f'Could not open socket: {e}')
    printer.print('Connection failed, check wifi and API key')
    printer.feed(1)
    return

  print("starting transcripton...")
  print("")
  #printer.print("starting transcription...")
  #printer.feed(1)

  # Listen for the connection to close
  deepgramLive.registerHandler(deepgramLive.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))

  # Listen for any transcripts received from Deepgram and write them to the console
  #deepgramLive.register_handler(deepgramLive.event.TRANSCRIPT_RECEIVED, print_transcript)

  storage = []
  transcription = ""
  inactive = 0
  qrseconds = 13 # time needed to print QR without colliding with text
  qrtimeout = 60 # time to wait after printing qr code before printing another qr code
  qrtimer = time.time() - qrtimeout
  def store_data(data: any) -> None:
        storage.append(data)
  deepgramLive.registerHandler(deepgramLive.event.TRANSCRIPT_RECEIVED, store_data)

  # Listen for the connection to open and send streaming audio from the URL to Deepgram
  async with aiohttp.ClientSession() as session:
    async with session.get(URL) as audio:
      while True:
        data = await audio.content.readany()
        deepgramLive.send(data)

        if storage:
            if len(storage[0]['channel']['alternatives'][0]['transcript']):
                transcription += storage.pop(0)['channel']['alternatives'][0]['transcript'] + ' '
                inactive = 0
            else:
                storage.pop(0)
                inactive += 1

        if (time.time() - qrtimer) > qrseconds:
            while len(transcription)>32:
                lines = textwrap.fill(transcription,32).splitlines()
                if lines:
                    if 'artist' in transcription.lower() and (time.time() - qrtimer) > qrtimeout:
                        qrtimer = time.time()
                        os.system('lp -o fit-to-page -o orientation-requested=3 /home/$USER/kateprint/qr.png')
                        #time.sleep(10)
                    print(lines[0] + ' ')
                    printer.print(lines.pop(0) + ' ')
                    transcription = ' '.join(lines) + ' '

            if inactive > 0 and len(transcription): # print any remaining text if no new text has come in for n transcription chunks
                lines = textwrap.fill(transcription,32).splitlines()
                if lines:
                    if 'artist' in transcription.lower() and (time.time() - qrtimer) > qrtimeout:
                        qrtimer = time.time()
                        os.system('lp -o fit-to-page -o orientation-requested=3 /home/$USER/kateprint/qr.png')
                        #time.sleep(10)
                    print(lines[0] + ' ')
                    print('')
                    printer.print(lines.pop(0) + ' ')
                    printer.feed(1)
                    transcription = ' '.join(lines)

            # If there's no data coming from the livestream then break out of the loop
            if not data:
                #print("No data from stream. Try 'sudo systemctl restart vlcmic.service'")
                print("No data from stream, restarting vlcmic...")
                os.system("sudo systemctl restart vlcmic.service")
                #break

  # Indicate that we've finished sending data by sending the customary zero-byte message to the Deepgram streaming endpoint, and wait until we get back the final summary metadata object
  await deepgramLive.finish()


def print_transcript(json_data):
  try:
    print(json_data['channel']['alternatives'][0]['transcript'])
  except KeyError:
    print()


asyncio.run(main())
