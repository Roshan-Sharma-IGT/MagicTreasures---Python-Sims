# This is a sample Python script.
import math
import time
import numpy as np
import random
import xlsxwriter
import pandas as pd
import openpyxl
import re

startTime = time.time()

SampleSize = int(math.pow(10, 6))
FreeSpins = 8
ExtraFreeSpinPerSymbol = 3
InitialPotValue = 5
MaxPotValue = 51

MBandFGStateProbs = np.array(pd.read_excel('FG probs.xlsx', sheet_name="MB and FG"))
ScatHitsWeightsOnReel = np.array(pd.read_excel('FG probs.xlsx', sheet_name="Scat Hits"))
MBTriggerProbs = np.array(pd.read_excel('FG probs.xlsx', sheet_name="MB Trigger Probs"))
PatternWeights = np.array(pd.read_excel('FG probs.xlsx', sheet_name="Pattern Weights"))
MB_SCAT1pattern = np.array(pd.read_excel('FG probs.xlsx', sheet_name="MB_SCAT1"))
MB_SCAT2pattern = np.array(pd.read_excel('FG probs.xlsx', sheet_name="MB_SCAT2"))
MB_SCAT3pattern = np.array(pd.read_excel('FG probs.xlsx', sheet_name="MB_SCAT3"))


def reelStopResult():
    t = len(ScatHitsWeightsOnReel[:, 1])
    spinOutCome = np.zeros(5)
    for reel in range(0, 5):
        spinOutCome[reel] = np.random.choice(range(0, t), 1, p=ScatHitsWeightsOnReel[:, reel + 1])
    return spinOutCome


def CountFGandMBs(reelstop):
    numberOfMBs = 0
    numberOfFGs = 0
    if reelstop[2] > 6:
        numberOfMBs = reelstop[2] - 6
    for x in reelstop:
        if x == 5:
            numberOfFGs += 1

    return numberOfMBs, numberOfFGs


def CORCheck(reelstops):
    # print(reelstops)
    connectedReels = 0
    numberScats = 0
    theMultiplier = 1
    for x in reelstops:
        if x > 0:
            connectedReels += 1
            if x > 4:
                if x > 6:
                    theMultiplier = 1.2
            else:
                numberScats += x

        else:
            break

    if connectedReels < 3:
        return 0
    else:
        return numberScats * theMultiplier


def MBPotTriggerPlacement(reelStop, ballsToPlace):
    # print(PatternWeights[:, ballsToPlace + 1])
    paternIndex = np.random.choice(range(1, 6), 1, p=PatternWeights[:, ballsToPlace + 1])
    MB_SCAT1 = MB_SCAT1pattern[ballsToPlace - 1, paternIndex]
    MB_SCAT2 = MB_SCAT2pattern[ballsToPlace - 1, paternIndex]
    MB_SCAT3 = MB_SCAT3pattern[ballsToPlace - 1, paternIndex]

    screenAfterPlacement = np.array(5)
    numCORonaReel = np.zeros(5)
    MBandCOR = 0
    for t in range(0, 5):
        if t < 4:
            if reelStop[t] > 4:
                numCORonaReel[t] = 0
            else:
                numCORonaReel[t] = reelStop[t]

        else:
            if reelStop[t-1] == 0 and MB_SCAT2 == 0:
                numCORonaReel[t] = 0
                MB_SCAT3 = 0
            else:
                if reelStop[t] > 4:
                    numCORonaReel[t] = 0
                else:
                    numCORonaReel[t] = reelStop[t]
    MBandCOR = np.sum(numCORonaReel) + MB_SCAT1 + MB_SCAT2 + MB_SCAT3
    #MBandCOR = np.sum(numCORonaReel)# +MB_SCAT1 + MB_SCAT2 + MB_SCAT3

    return MBandCOR


def playAGame(freeGames):
    SpinsPlayed = 0
    RemainingSpins = freeGames
    CORprizeHits = 0
    CORandMBlprizeHits = 0
    potHits = np.zeros((4, MaxPotValue + 1))
    ThePotValue = InitialPotValue
    while RemainingSpins > 0:
        spinOutCome = reelStopResult()
        numberOfMBLanded = int(CountFGandMBs(spinOutCome)[0])
        numberOfFGLanded = int(CountFGandMBs(spinOutCome)[1])

        RemainingSpins += numberOfFGLanded * 3 - 1
        triggerProb = MBTriggerProbs[ThePotValue - 1, numberOfMBLanded]
        Trigger = np.random.choice([0, 1], 1, p=[triggerProb, 1 - triggerProb])

        potHits[Trigger + 2, ThePotValue] += 1

        if ThePotValue < 47:
            ThePotValue += numberOfMBLanded

        CORprizeHits += CORCheck(spinOutCome)
        if Trigger == 0:
            CORandMBlprizeHits += MBPotTriggerPlacement(spinOutCome, ThePotValue)

        potHits[Trigger, ThePotValue] += 1
        SpinsPlayed += 1

    return potHits, SpinsPlayed, CORprizeHits, CORandMBlprizeHits


def RunTheSim(sampleSize):
    ThePotHits = np.zeros((4, MaxPotValue + 1))
    TotalSpinsPlayed = np.zeros(900)
    TotalCORHIts = 0
    TotalCORandMBhits = 0
    for x in range(1, sampleSize + 1):
        y = playAGame(FreeSpins)
        ThePotHits = np.add(ThePotHits, y[0])
        TotalSpinsPlayed[y[1]] += y[1]
        TotalCORHIts += y[2]
        TotalCORandMBhits += y[3]

        if x % (sampleSize / 10) == 0:
            print("Complete ", x / sampleSize * 100, "%")
    OutputDataFrame = pd.DataFrame(ThePotHits)
    FGOutputDataFrame = pd.DataFrame(TotalSpinsPlayed)
    return OutputDataFrame, FGOutputDataFrame, TotalCORHIts, TotalCORandMBhits


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    OutPut = RunTheSim(SampleSize)
    print(' CORs with multiplier: ', OutPut[2])
    print(' COR and MBs without  multiplier: ', OutPut[3])
    OutPut[0].transpose().to_excel('OutPut1.xlsx', sheet_name='MB trigger hits in FG')
    OutPut[1].to_excel('OutPut2.xlsx', sheet_name='FGs')
    # print("--- %s Spins Played ---" % OutPut[1])
print("--- %s Minutes ---" % ((time.time() - startTime) / 60))
