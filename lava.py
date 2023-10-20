#!/usr/bin/env python3
# NeoPixel library strandtest example
# Author: Tony DiCola (tony@tonydicola.com)
#
# Direct port of the Arduino NeoPixel library strandtest example.  Showcases
# various animations on a strip of NeoPixels.

import time
from rpi_ws281x import PixelStrip, Color
import argparse
import multiprocessing as mp
import os
import array as arr
import random

# LED strip configuration:
LED_COUNT = 1200  # Number of LED pixels.
LED_PIN = 18  # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN = 10        # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10  # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255  # Set to 0 for darkest and 255 for brightest
LED_INVERT = False  # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0  # set to '1' for GPIOs 13, 19, 41, 45 or 53
MAX_LAVA_TEMP_C = 1200

ledDegC = [0] * LED_COUNT
oldLedDegC = [0] * LED_COUNT
pixelCount = [2, 100, 300, 200, 600]

IDLE = 0
BUILDING = 1
FLOWING = 2
ENDING = 3


def subStrip_getLedCount(subStrip):
    return pixelCount[subStrip]


def subStrip_getStartLed(subStrip):
    start = 0

    if subStrip > 0:
        for i in range(subStrip):
            start += pixelCount[i]
    return start


def subStrip_getFinalLed(subStrip):
    end = 0

    for i in range(subStrip+1):
        end += pixelCount[i]
    return end


def showStrip(local_strip, temperatures):
    for i in range(LED_COUNT):
        local_strip.setPixelColor(i, setTemperature(temperatures[i]))
    local_strip.show()


def setTemperature(degC):
    lavaColor = 0
    if degC >= 600 and degC <= 1200:
        normalizedDegC = (degC - 600) / 600
        brightness = normalizedDegC * 255
        red = int(252 * brightness / LED_BRIGHTNESS)
        green = int(90 * brightness / LED_BRIGHTNESS * normalizedDegC)
        blue = int(3 * brightness / LED_BRIGHTNESS)
        lavaColor = Color(red, green, blue)
    return lavaColor


def interpolateLavaDegC(index, factor):
    maxIndex = len(lavaFlowDegC) - 1
    a = index % 25
    b = a + 1
    if b > maxIndex:
        b = 0
    degC = lavaFlowDegC[a] * (1 - factor) + lavaFlowDegC[b] * factor
    return degC


def lavaShimmer(strip, subStrip = 0, smooth = 0.0):
    for i in range(subStrip_getStartLed(subStrip), subStrip_getFinalLed(subStrip), 1):
        if smooth == 0:
            oldLedDegC[i] = random.randint(625, 650)

        ledDegC[i] = ledDegC[i] * (1 - smooth) + oldLedDegC[i] * smooth


def lavaBuild(local_strip, subStrip=0, smooth = 0.0, degC=1200):
    if smooth == 0:
        for i in range(subStrip_getStartLed(subStrip), subStrip_getFinalLed(subStrip), 1):
            oldLedDegC[i] = ledDegC[i]

    for i in range(subStrip_getStartLed(subStrip), subStrip_getFinalLed(subStrip), 1):
        ledDegC[i] = oldLedDegC[i] * (1 - smooth) + degC * smooth


def lavaDownhill(local_strip, subStrip=0, smooth=0.0, newValue=650):
    lastPixelIndex = subStrip_getFinalLed(subStrip) - 1

    # print('Smooth = ', smooth)
    if smooth == 0:
        for i in range(subStrip_getStartLed(subStrip), subStrip_getFinalLed(subStrip), 1):
            oldLedDegC[i] = ledDegC[i]
            # print('oldLedColors[', i, '] = ', 'ledColors[', i, ']')
    elif smooth < 1:
        for i in range(0, subStrip_getLedCount(subStrip)-1, 1):
            ledDegC[lastPixelIndex - i] = oldLedDegC[lastPixelIndex - i] * (1 - smooth) + oldLedDegC[lastPixelIndex - (i + 1)] * smooth

            firstLed = subStrip_getStartLed(subStrip)
            ledDegC[firstLed] = oldLedDegC[firstLed] * (1 - smooth) + newValue * smooth
    else:
        firstLed = subStrip_getStartLed(subStrip)
        for j in range(firstLed, firstLed + int(smooth), 1):
            for i in range(0, subStrip_getLedCount(subStrip)-1, 1):
                ledDegC[lastPixelIndex - i] = ledDegC[lastPixelIndex - (i + 1)]

        for j in range(firstLed, firstLed + int(smooth), 1):
            ledDegC[j] = newValue


# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip1 = PixelStrip(LED_COUNT, 13, LED_FREQ_HZ, 5, LED_INVERT, LED_BRIGHTNESS, 1)

    # Intialize the library (must be called once before other functions).
    strip.begin()
    strip1.begin()

    print('Press Ctrl-C to quit.')
    print('Lava display')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:

        for subStrip in range(5):
            print('SubStrip ', subStrip, " from ", subStrip_getStartLed(subStrip), ' to ', subStrip_getFinalLed(subStrip))

        startTime = time.time()
        degC = 600

        state = IDLE

        while True:

            now = time.time()

            elapsedTime = now - startTime

            if state == BUILDING:
                degC = 1200
                for smooth in range(5):
                    lavaBuild(strip1, 0, smooth/5.0)
                    lavaShimmer(strip1, 1, smooth/5.0)
                    showStrip(strip1, ledDegC)
                state = FLOWING

            elif state == FLOWING:
                degC = random.randint(700, 1100)
                speed = 1.0
                if speed <= 1:
                    for smooth in range(int(speed+1)):
                        lavaDownhill(strip1, 1, smooth/speed, degC)
                        showStrip(strip1, ledDegC)
                else:
                    lavaDownhill(strip1, 1, speed, degC)
                    showStrip(strip1, ledDegC)

                if elapsedTime > 20:
                    state = ENDING

            elif state == ENDING:
                degC = random.randint(605, 625)
                for smooth in range(6):
                    lavaDownhill(strip1, 0, smooth/5.0, degC)
                    lavaDownhill(strip1, 1, smooth/5.0, degC)
                    showStrip(strip1, ledDegC)
                if elapsedTime > 40:
                    state = IDLE
                    startTime = now

            else:
                degC = random.randint(625, 650)
                for smooth in range(6):
                    # lavaShimmer(strip1, 0, smooth/5.0)
                    # lavaShimmer(strip1, 1, smooth/5.0)
                    lavaDownhill(strip1, 0, smooth/5.0, degC)
                    lavaDownhill(strip1, 1, smooth/5.0, degC)
                    showStrip(strip1, ledDegC)
                if elapsedTime > 2:
                    state = BUILDING

    except KeyboardInterrupt:
        if args.clear:
            # colorWipe(strip, Color(0, 0, 0), 10)
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, 0)
            for i in range(strip1.numPixels()):
                strip1.setPixelColor(i, 0)
            strip.show()
            strip1.show()
