from pathlib import Path
from deepgram import Deepgram
import asyncio
import aiohttp
import board
import adafruit_thermal_printer
import serial
import textwrap
from time import sleep

# Your Deepgram API Key
key = Path(__file__).with_name('deepgram-key.txt')
with key.open('r') as file:
    DEEPGRAM_API_KEY = file.read().splitlines()[0]

# URL for the audio you would like to stream
#URL = 'http://stream.live.vc.bbcmedia.co.uk/bbc_world_service'
URL = 'http://127.0.0.1:8888/out.mp3'

async def main():
  # Initialize thermal printer
  ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.69)
  RX = board.RX
  TX = board.TX
  uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=3000)
  printer = ThermalPrinter(uart)
  sleep(5)

  # Initialize the Deepgram SDK
  deepgram = Deepgram(DEEPGRAM_API_KEY)

  # Create a websocket connection to Deepgram
  # In this example, punctuation is turned on, interim results are turned off, and language is set to US English.
  try:
    deepgramLive = await deepgram.transcription.live({ 'punctuate': True, 'interim_results': False, 'language': 'en-US', 'model': 'nova' })
  except Exception as e:
    print(f'Could not open socket: {e}')
    printer.print('Connection failed, check API key')
    printer.feed(1)
    return

  print("starting transcripton...")
  print("")
  printer.print("starting transcription...")
  printer.feed(1)

  # Listen for the connection to close
  deepgramLive.registerHandler(deepgramLive.event.CLOSE, lambda c: print(f'Connection closed with code {c}.'))

  # Listen for any transcripts received from Deepgram and write them to the console
  #deepgramLive.register_handler(deepgramLive.event.TRANSCRIPT_RECEIVED, print_transcript)

  storage = []
  transcription = ""
  inactive = 0
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
            else:
                storage.pop(0)
                inactive += 1

        while len(transcription)>32:
            lines = textwrap.fill(transcription,32).splitlines()
            if lines:
                print(lines[0] + ' ')
                printer.print(lines.pop(0) + ' ')
                transcription = ' '.join(lines) + ' '

        if inactive > 2 and len(transcription): # print any remaining text if no new text has come in for n transcription chunks
            lines = textwrap.fill(transcription,32).splitlines()
            if lines:
                print(lines[0] + ' ')
                print('')
                printer.print(lines.pop(0) + ' ')
                #printer.feed(1)
                transcription = ' '.join(lines)

        # If there's no data coming from the livestream then break out of the loop
        if not data:
            print('no data')
            break

  # Indicate that we've finished sending data by sending the customary zero-byte message to the Deepgram streaming endpoint, and wait until we get back the final summary metadata object
  await deepgramLive.finish()


def print_transcript(json_data):
  try:
    print(json_data['channel']['alternatives'][0]['transcript'])
  except KeyError:
    print()


asyncio.run(main())
