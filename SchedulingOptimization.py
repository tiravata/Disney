#Optimization Class
#By Tiravat (TO) Assavapokee
#Developed on February 13, 2016

import time
import random
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime, date
import os

class SchedulingOptimization:
    def __init__(self, TravelTimeFile, WaitingTimeFile, PlayTimeFile, AvailableTimeFile, MaxTravelTime = 120, MaxWaitTime=300, MaxPlayTime=60):
        try:
            #Check if TravelTimeFile Exists
            if not (os.path.exists(TravelTimeFile)):
                raise Exception("Error Reading Input Files (TravelTimeFile)")

            #Check if WaitingTimeFile Exists
            if not (os.path.exists(WaitingTimeFile)):
                raise Exception("Error Reading Input Files (WaitingTimeFile)")

            #Check if PlayTimeFile Exists
            if not (os.path.exists(PlayTimeFile)):
                raise Exception("Error Reading Input Files (PlayTimeFile)")

            #Check if AvailableTimeFile Exists
            if not (os.path.exists(AvailableTimeFile)):
                raise Exception("Error Reading Input Files (AvailableTimeFile)")

            #Dictionary of {AttractionID => Play Time Minute: Int}
            self.PlayTimes = {}
            #Dictionary of (AttractionID1: String, AttractionID2: String) => Travel Time Minute : Int
            self.TravelTimes = {}
            #Dictionary of (AttractionID: String, Day of Week : Int, TimeSlotID : Int) => WaitingTimeInMinutes : Int
            self.WaitingTimes = {}
            #Dictionary of (AttractionID: String, Day of Week: Int) => [(startTime, endTime), (startTime, endTime)]
            self.AvailableTimes = {}

            #List of All AttractionIDs, DayOfWeekIDs, TimeSlotIDs
            self.AttractionList = []
            self.ShowFlagDict = {} #AttractionID = > True False
            self.DayOfWeekDict = {"monday": 0, "tuesday":1, "wednesday":2, "thursday":3, "friday":4, "saturday":5, "sunday": 6}
            self.timeList = [x for x in range(30, 1441, 30)]
            self.TimeSlotDict = {up:id for (id, up) in enumerate(self.timeList)}

            if MaxTravelTime >= 1 and MaxTravelTime <= 120:
                self.MaxTravelTime = MaxTravelTime
            elif MaxTravelTime > 120:
                self.MaxTravelTime = 120
            elif MaxTravelTime < 1:
                self.MaxTravelTime = 1

            if MaxWaitTime >= 1 and MaxWaitTime <= 300:
                self.MaxWaitTime = MaxWaitTime
            elif MaxWaitTime > 300:
                self.MaxWaitTime = 300
            elif MaxWaitTime < 1:
                self.MaxWaitTime = 1

            if MaxPlayTime >= 1 and MaxPlayTime <= 60:
                self.MaxPlayTime = MaxPlayTime
            elif MaxPlayTime > 60:
                self.MaxPlayTime = 60
            elif MaxPlayTime < 1:
                self.MaxPlayTime = 1
            self.initializeData(TravelTimeFile, WaitingTimeFile, PlayTimeFile, AvailableTimeFile)
        except Exception as ex:
            ErrorMessage = "Error Initializing Optimization Problem: "+" ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)


    def initializeData(self, TravelTimeFile, WaitingTimeFile, PlayTimeFile, AvailableTimeFile):
        try:
            #Reading PlayTime File
            PlayTimeDF = pd.read_csv(PlayTimeFile, sep="|", header=0, dtype={"AttractionID": object, "PlayTime": int, "IsShow": bool})
            self.AttractionList = PlayTimeDF.AttractionID.unique().tolist()
            ShowList = PlayTimeDF[PlayTimeDF.IsShow == True].AttractionID.unique().tolist()
            self.ShowFlagDict = {att:(att in ShowList) for att in self.AttractionList}
            for index, row in PlayTimeDF.iterrows():
                att = row['AttractionID']
                rawPlayTime = row['PlayTime']
                if rawPlayTime < 1:
                    rawPlayTime = 1
                elif rawPlayTime > self.MaxPlayTime:
                    rawPlayTime = self.MaxPlayTime
                self.PlayTimes[att] = rawPlayTime

            #Reading WaitingTime File
            WaitingTimeDF = pd.read_csv(WaitingTimeFile, sep="|", header=0, dtype={"AttractionID": object, "DayOfWeekID": object, "TimeSlotID": int, "WaitTime": int})
            for att in self.AttractionList:
                for dow in range(7):
                    for tsID in range(len(self.timeList)):
                        self.WaitingTimes[(att, dow, tsID)] = self.MaxWaitTime
            for index, row in WaitingTimeDF.iterrows():
                att = row['AttractionID']
                if str(row['DayOfWeekID']).lower().strip() not in self.DayOfWeekDict.keys():
                    continue
                dow = self.DayOfWeekDict[str(row['DayOfWeekID']).lower().strip()]
                rawTimeSlotID = row['TimeSlotID']
                if rawTimeSlotID < 30:
                    rawTimeSlotID = 30
                elif rawTimeSlotID > 1440:
                    rawTimeSlotID = 1440
                if rawTimeSlotID % 30 <> 0:
                    rawTimeSlotID = rawTimeSlotID + (30 - (rawTimeSlotID % 30))
                tsID = self.TimeSlotDict[rawTimeSlotID]
                rawWaitTime = row['WaitTime']
                if rawWaitTime < 1:
                    rawWaitTime = 1
                elif rawWaitTime > self.MaxWaitTime:
                    rawWaitTime = self.MaxWaitTime
                self.WaitingTimes[(att,dow,tsID)] = rawWaitTime

            #Start Reading TravelTime
            FileTravelTimeDF = pd.read_csv(TravelTimeFile, sep="|", header=0, dtype={"AttractionID1": object, "AttractionID2": object, "TravelTime": int})
            for att1 in self.AttractionList + ["Entrance"]:
                for att2 in self.AttractionList + ["Entrance"]:
                    if att1 == att2:
                        self.TravelTimes[(att1, att2)] = 5 #take at least 5 min to come back to same ride from the same ride
                    else:
                        self.TravelTimes[(att1, att2)] = self.MaxTravelTime

            for index, row in FileTravelTimeDF.iterrows():
                att1 = row["AttractionID1"]
                att2 = row["AttractionID2"]
                rawTravelTime = row["TravelTime"]
                if rawTravelTime < 5:
                    rawTravelTime = 5
                elif rawTravelTime > self.MaxTravelTime:
                    rawTravelTime = self.MaxTravelTime
                self.TravelTimes[(att1,att2)] = rawTravelTime


            #Start Reading AvailableTime
            FileAvailableTimeDF = pd.read_csv(AvailableTimeFile, sep="|", header=0, dtype={"AttractionID":object, "DayOfWeekID": object, "StartTime": int, "EndTime": int})
            FileAvailableTimeDF.sort_values(by=["AttractionID","DayOfWeekID","StartTime"], ascending=[True, True, True])
            for att in self.AttractionList:
                for dow in range(7):
                    self.AvailableTimes[(att, dow)] = list()
            from collections import defaultdict
            self.AvailableTimes = defaultdict(list)
            for index, row in FileAvailableTimeDF.iterrows():
                att = row["AttractionID"]
                dow = row["DayOfWeekID"]
                startTime = row["StartTime"]
                endTime = row["EndTime"]
                if (att, dow) in self.AvailableTimes:
                    self.AvailableTimes[(att, dow)].append((startTime, endTime))
        except Exception as ex:
            ErrorMessage = "Error Initializing Data: "+" ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)

    def print_Data(self):
        try:
            print "===== Traveling Time Information =================="
            print self.TravelTimes
            print "==================================================="
            print "====== Waiting Time Information ==================="
            print self.WaitingTimes
            print "==================================================="
            print "====== Play Time Information ======================"
            print self.PlayTimes
            print "==================================================="
            print "====== Show Dict Information ======================"
            print self.ShowFlagDict
            print "==================================================="
            print "====== Attraction Available Time =================="
            print self.AvailableTimes
            print "==================================================="
        except Exception as ex:
            ErrorMessage = "Error Printing Data: "+" ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)

    def calculateWaitTime(self, AttractionID, ArrivalTime, weekDayID):
        try:
            ExtraWaitTime = 0
            if self.ShowFlagDict[AttractionID] == False:
                #if this attraction is not a show
                if ArrivalTime > 1440:
                    raise Exception("Arrival Time Value too high in calculateWaitTime")
                if ArrivalTime <= 0:
                    raise Exception("Arrival Time Value too low in calculateWaitTime")
                if AttractionID not in self.AttractionList:
                    raise Exception("Attrition ID (%s) is not in AttritionList"%(AttractionID))
                AdjustArrivalTime = ArrivalTime

                #Check if attraction is available at this time or not
                #if yes, we will just calculate waiting time as usual
                #if no, we will wait until the attraction become available
                for (i, (startTime, endTime)) in enumerate(self.AvailableTimes[(AttractionID, weekDayID)]):
                    if (AdjustArrivalTime < startTime):
                        ExtraWaitTime = startTime - AdjustArrivalTime
                        AdjustArrivalTime = startTime
                        break
                    elif (AdjustArrivalTime >= startTime) and (AdjustArrivalTime <= endTime):
                        ExtraWaitTime = 0
                        break
                    elif (AdjustArrivalTime > endTime):
                        if (i == len(self.AvailableTimes[(AttractionID, weekDayID)]) - 1):
                            return 1440
                        else:
                            continue

                if AdjustArrivalTime % 30 != 0:
                    AdjustArrivalTime = AdjustArrivalTime + (30 - (AdjustArrivalTime % 30))

                return self.WaitingTimes[(AttractionID, weekDayID, self.TimeSlotDict[AdjustArrivalTime])] + ExtraWaitTime
            else:
                #If this attraction is a show
                if ArrivalTime > 1440:
                    raise Exception("Arrival Time Value too high in calculateWaitTime")
                if ArrivalTime <= 0:
                    raise Exception("Arrival Time Value too low in calculateWaitTime")
                if AttractionID not in self.AttractionList:
                    raise Exception("Attrition ID (%s) is not in AttritionList"%(AttractionID))
                AdjustArrivalTime = ArrivalTime

                #Check if we arrive before on ontime for show or not
                #if yes, we will just calculate waiting time as usual
                #if no, we will wait until next show time
                for (i, (startTime, endTime)) in enumerate(self.AvailableTimes[(AttractionID, weekDayID)]):
                    if (AdjustArrivalTime <= startTime):
                        ExtraWaitTime = startTime - AdjustArrivalTime
                        AdjustArrivalTime = startTime
                        break
                    else:
                        if (i == len(self.AvailableTimes[(AttractionID, weekDayID)]) - 1):
                            return 1440
                        else:
                            continue

                return ExtraWaitTime

        except Exception as ex:
            ErrorMessage = "Error calculating Waiting Time: " + " ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)

    def calculateNextAvailableTime(self, AttractionID, ArrivalTime, weekDayID):
        try:
            #if this is not show
            #    if ArrivalTime falls between StartTime and EndTime ... then return (0, ArrivalTime, StartTime, EndTime)
            #    if Arrival Time <= Start Time of interval
            #       then return (WaitTime, StartTime, StartTime, EndTime)
            #    if ArrivalTime > end time of all intervals then return None
            #    if this function return None, we should skip this attraction
            #if this is show
            #    if ArrivalTime <= Start Time, then return (WaitTime, StartTime, StartTime, EndTime)
            #    if Arrival Time > Start Time for all intervals, then return None
            #    if this function return None, we should skip this show
            if ((AttractionID, weekDayID) in self.AvailableTimes) and (AttractionID in self.ShowFlagDict):
                if self.ShowFlagDict[AttractionID] == False:
                    for (startTime, endTime) in self.AvailableTimes[(AttractionID, weekDayID)]:
                        if ArrivalTime < startTime:
                            return (startTime-ArrivalTime, startTime, startTime, endTime)
                        elif ArrivalTime >= startTime and ArrivalTime <= endTime:
                            return (0, ArrivalTime, startTime, endTime)
                    return None

                if self.ShowFlagDict[AttractionID] == True:
                    for (startTime, endTime) in self.AvailableTimes[(AttractionID, weekDayID)]:
                        if ArrivalTime <= startTime:
                            return (startTime - ArrivalTime, startTime, startTime, endTime)
                    return None
            else:
                return None
        except Exception as ex:
            ErrorMessage = "Error calculating next available time: " + " ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)

    def evaluate_Solution(self, Solution, Importance, StartTime, EndTime, ParameterDict, weekDayID):
        #Solution is the list of AttractionID in order
        try:
            SolutionDetail = []
            CanAttendList = []
            TotalScore = 0.0
            #The higher the score, the better the solution is
            #(1) Important * Adjust Weight Importance
            #(2) - Total Weight Time * Adjust Weight Wait Time
            #(3) - Total Travel Time * Adjust Travel Time
            if StartTime < 0 or StartTime > 1440:
                raise Exception("StartTime is out of range")
            if EndTime < 0 or EndTime > 1440:
                raise Exception("EndTime is out of range")
            if StartTime >= EndTime:
                raise Exception("StartTime >= EndTime")
            if Solution == None or len(Solution) == 0:
                raise Exception("No Solution Given to Evaluate")
            if Importance == None or len(Importance) == 0 or len(Importance) <> len(Solution):
                raise Exception("Error in Importance Score List")

            #Adding First one
            Done = False
            LastAttraction = None
            currentAttraction = Solution[0]
            currentImportance = Importance[0]
            currentTime = StartTime
            currentTravelTime = self.TravelTimes[("Entrance", currentAttraction)]
            nextArrivalTime = currentTime + currentTravelTime
            currentWaitingTime = self.calculateWaitTime(currentAttraction, nextArrivalTime, weekDayID)
            nextFinishTime = nextArrivalTime + currentWaitingTime + self.PlayTimes[currentAttraction]
            if nextFinishTime + self.TravelTimes[(currentAttraction, "Entrance")] < EndTime:
                CanAttendList.append(currentAttraction)
                TotalScore += currentImportance * ParameterDict["Importance_Adj"]
                TotalScore -= currentWaitingTime * ParameterDict["WaitingTime_Adj"]
                TotalScore -= currentTravelTime * ParameterDict["TravelTime_Adj"]
                SolutionDetail.append("Travel:(Entrance=>%s):[%d-%d]"%(currentAttraction, currentTime, nextArrivalTime))
                SolutionDetail.append("Wait:(%s):[%d-%d]"%(currentAttraction, nextArrivalTime, nextArrivalTime + currentWaitingTime))
                SolutionDetail.append("Play:(%s):[%d-%d]"%(currentAttraction, nextArrivalTime + currentWaitingTime, nextFinishTime))
            else:
                Done = True
                LastAttraction = None

            if not Done and len(Solution) > 1:
                for (i, currSolution) in enumerate(Solution[1:]):
                    currentAttraction = currSolution
                    currentImportance = Importance[i+1]
                    currentTime = nextFinishTime
                    currentTravelTime = self.TravelTimes[(Solution[i], currentAttraction)]
                    nextArrivalTime = currentTime + currentTravelTime
                    currentWaitingTime = self.calculateWaitTime(currentAttraction, nextArrivalTime, weekDayID)
                    nextFinishTime = nextArrivalTime + currentWaitingTime + self.PlayTimes[currentAttraction]
                    if nextFinishTime + self.TravelTimes[(currentAttraction, "Entrance")] < EndTime:
                        CanAttendList.append(currentAttraction)
                        TotalScore += currentImportance * ParameterDict["Importance_Adj"]
                        TotalScore -= currentWaitingTime * ParameterDict["WaitingTime_Adj"]
                        TotalScore -= currentTravelTime * ParameterDict["TravelTime_Adj"]
                        SolutionDetail.append("Travel:(%s=>%s):[%d-%d]"%(Solution[i], currentAttraction, currentTime, nextArrivalTime))
                        SolutionDetail.append("Wait:(%s):[%d-%d]"%(currentAttraction, nextArrivalTime, nextArrivalTime + currentWaitingTime))
                        SolutionDetail.append("Play:(%s):[%d-%d]"%(currentAttraction, nextArrivalTime + currentWaitingTime, nextFinishTime))
                        LastAttraction = currentAttraction
                    else:
                        break

                if LastAttraction is not None:
                    TotalScore -= self.TravelTimes[(LastAttraction, "Entrance")]* ParameterDict["TravelTime_Adj"]
                    SolutionDetail.append("Travel:(%s=>Entrance):[%d-%d]"%(LastAttraction, nextFinishTime, nextFinishTime + self.TravelTimes[(LastAttraction, "Entrance")]))

            return (CanAttendList, SolutionDetail, TotalScore)
        except Exception as ex:
            ErrorMessage = "Error Evaluating Solution: "+" ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)

    def run_ConstructionHeuristic(self, SelectedAttractionList, SelectedImportantList, StartTime, EndTime, ParameterDict, weekDayID):
        try:
            Solution = []
            Important = []
            TotalScore = 0.0
            #calculate from start time traveling to each attraction in the list
            #get important of each attraction in the list
            #get waiting time of each attraction in the list
            #Calculate Score for each attraction based on traveling time to this attraction, important of this attraction, and waiting time of this attraction
            #pick the attraction from the list with maximum score
            #check if we select this attraction as next attraction, what is the next time to finish this attraction
            #finish time = current finish time + travel time + wait time + play time
            #calculate est_end_time = finish time + travel time from this attraction to exit
            #if est_end_time is more than EndTime => remove this attraction (not possible) and try next attraction
            #otherwise => select this attraction to join solution list and remove this attraction from the list and repeat the process again
            #update current finish time = finish time
            #if list is empty, then we stop the algorithm and return the solution and important list

            AttractionImportantList = [(a, i) for (a, i) in zip(SelectedAttractionList, SelectedImportantList) if a in self.AttractionList]
            index = 0
            maxIndex = len(AttractionImportantList)
            currentTime = StartTime
            currentLocation = "Entrance"
            while(len(AttractionImportantList) > 0 and index < maxIndex):
                index += 1
                #Calculate Score
                bestOne = None
                RemoveList = []
                for (att, imp) in AttractionImportantList:
                    #important score, travel time score, waiting time score
                    TravelTime = self.TravelTimes[(currentLocation, att)]
                    ArrivingTime = currentTime + TravelTime
                    WaitingTime = self.calculateWaitTime(att, ArrivingTime, weekDayID)
                    PossibleExitTime = ArrivingTime + WaitingTime + self.PlayTimes[att] + self.TravelTimes[(att, "Entrance")]
                    if PossibleExitTime > EndTime:
                        RemoveList.append(att)
                        continue
                    else:
                       Score = imp * ParameterDict["Importance_Adj"]
                       Score -= WaitingTime * ParameterDict["WaitingTime_Adj"]
                       Score -= TravelTime * ParameterDict["TravelTime_Adj"]
                       if bestOne is None:
                           bestOne = (att, imp, Score)
                       else:
                           if Score > bestOne[2]:
                               bestOne = (att, imp, Score)
                if bestOne is None:
                    break
                else:
                    Solution.append(bestOne[0])
                    Important.append(bestOne[1])
                    TotalScore += bestOne[2]
                    AttractionImportantList_Temp = [(att, imp) for (att, imp) in AttractionImportantList if att <> bestOne[0] and att not in RemoveList]
                    AttractionImportantList = AttractionImportantList_Temp
                    TravelTime = self.TravelTimes[(currentLocation, bestOne[0])]
                    ArrivingTime = currentTime + TravelTime
                    WaitingTime = self.calculateWaitTime(bestOne[0], ArrivingTime, weekDayID)
                    PlayTime = self.PlayTimes[bestOne[0]]
                    currentTime = currentTime + TravelTime + WaitingTime + PlayTime
                    currentLocation = bestOne[0]

            return (Solution, Important, TotalScore)
        except Exception as ex:
            ErrorMessage = "Error Run Construction Heuristic: " + " ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)

    def run_LocalSearchImprovingHeuristic(self, initialSolution, SelectedAttractionList, SelectedImportantList, StartTime, EndTime, ParameterDict, weekDayID, max_niterations):
        try:
            attractionToImportantDict = {att:imp for (att, imp) in zip(SelectedAttractionList, SelectedImportantList) if att in self.AttractionList}
            wipSelectedAttractionSet = set([att for att in initialSolution if att in self.AttractionList])
            wipNonSelectedAttractionSet = set([att for att in SelectedAttractionList if att not in wipSelectedAttractionSet and att in self.AttractionList])
            currentBestSolution = [att for att in initialSolution if att in self.AttractionList]
            currentBestImportant = [attractionToImportantDict[att] for att in currentBestSolution]
            currentSolution = currentBestSolution[:]
            currentImportant = [attractionToImportantDict[att] for att in currentSolution]
            currentBestScore = self.evaluate_Solution(currentBestSolution, currentImportant, StartTime, EndTime, ParameterDict, weekDayID)[2]
            improvement = True
            iteration = 0
            if(max_niterations <= 1): max_niterations = 50
            while(improvement and iteration < max_niterations):
                improvement = False
                IterationSwapAtt1 = None
                IterationSwapAtt2 = None
                BestSolutionThisIteration = currentSolution[:]
                BestImportantThisIteration = currentImportant[:]
                #Loop to search for candidate attraction (to swap with other either swap place or swap out
                #we will then loop to search for best swap both inside and outside
                #we will calculate score for each alternative and pick best alternative
                #if best alternative of the candidate attraction is better than bestScore so far, we will put it in candidate list
                #After evaluate all candidate attraction
                #if candidate list is empty, break and set improvement to False
                #other wise pick candidate with best improvement and update BestSolution BestScore and CurrentSolution and continue to next iteration
                for candAtt in currentSolution:
                    for swapAtt in wipSelectedAttractionSet:
                        if(candAtt == swapAtt): continue
                        newTrialSolution = currentSolution[:]
                        newTrialImportant = currentImportant[:]
                        #replace candAtt in newTrialSolution with swapAtt
                        #also replace swapAtt with candAtt by using index
                        Index1 = currentSolution.index(candAtt)
                        Index2 = currentSolution.index(swapAtt)
                        newTrialSolution[Index1] = swapAtt
                        newTrialSolution[Index2] = candAtt
                        newTrialImportant[Index1] = currentImportant[Index2]
                        newTrialImportant[Index2] = currentImportant[Index1]
                        TrialEvalResult = self.evaluate_Solution(newTrialSolution, newTrialImportant, StartTime, EndTime, ParameterDict, weekDayID)
                        newTrialSolutionReal = TrialEvalResult[0]
                        TrialSolutionScore = TrialEvalResult[2]

                        if(TrialSolutionScore > currentBestScore):
                            currentBestSolution = newTrialSolutionReal[:]
                            currentBestImportant = [attractionToImportantDict[att] for att in currentBestSolution]
                            currentBestScore = TrialSolutionScore
                            improvement = True

                    for swapAtt in wipNonSelectedAttractionSet:
                        newTrialSolution = currentSolution[:]
                        newTrialImportant = currentImportant[:]
                        Index1 = currentSolution.index(candAtt)
                        newTrialSolution[Index1] = swapAtt
                        newTrialImportant[Index1] = attractionToImportantDict[swapAtt]
                        TrialEvalResult = self.evaluate_Solution(newTrialSolution, newTrialImportant, StartTime, EndTime, ParameterDict, weekDayID)
                        newTrialSolutionReal = TrialEvalResult[0]
                        TrialSolutionScore = TrialEvalResult[2]

                        if(TrialSolutionScore > currentBestScore):
                            currentBestSolution = newTrialSolutionReal[:]
                            currentBestImportant = [attractionToImportantDict[att] for att in currentBestSolution]
                            currentBestScore = TrialSolutionScore
                            improvement = True

                #Find Best Solution for this iteration
                #If there is improvement, update data structures
                #If no improvement, set improvement to False and break out
                if(improvement == True):
                    currentSolution = currentBestSolution[:]
                    currentImportant = [attractionToImportantDict[att] for att in currentSolution]
                    wipSelectedAttractionSet = set([att for att in currentSolution if att in self.AttractionList])
                    wipNonSelectedAttractionSet = set([att for att in SelectedAttractionList if att not in wipSelectedAttractionSet and att in self.AttractionList])

                iteration += 1

            return (currentBestSolution, currentBestImportant, currentBestScore)
        except Exception as ex:
            ErrorMessage = "Error Run Local Search Improving Heuristic: " + " ".join([str(x) for x in ex.args])
            print ErrorMessage
            raise Exception(ErrorMessage)