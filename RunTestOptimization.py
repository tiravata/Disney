from SchedulingOptimization import SchedulingOptimization

if __name__ == '__main__':
    TravelTimeFile = 'C:/PythonTestProgram/Data/DisneyData/TravelingTimeBetweenAttraction.csv'
    WaitTimeFile = 'C:/PythonTestProgram/Data/DisneyData/AttractionWaitTime.csv'
    PlayTimeFile = 'C:/PythonTestProgram/Data/DisneyData/AttractionPlayTime.csv'
    schOpt = SchedulingOptimization(TravelTimeFile, WaitTimeFile, PlayTimeFile)
    schOpt.print_Data()
    TestSolution = ['A1', 'A2', 'A3']
    TestImportance = [100.0, 100.0, 50.0]
    TestCurrentWeekDayID = 3
    TestStartTime = 9*60
    TestEndTime = 17*60
    TestParameterDict = {"Importance_Adj": 1.0, "WaitingTime_Adj": 0.01, "TravelTime_Adj":0.01}
    (FinalSolution, FinalSolutionDetail, FinalScore) = schOpt.evaluate_Solution(TestSolution, TestImportance, TestStartTime, TestEndTime, TestParameterDict, TestCurrentWeekDayID)
    print "Current_Solution = %s"%(FinalSolution)
    print "Total_Solution_Score = %f"%(FinalScore)
    print "Current_Solution_Detail = %s"%(FinalSolutionDetail)

    (OptSolution, OptImportant, OptTotalScore) = schOpt.run_ConstructionHeuristic(['A1', 'A2', 'A3'], [100.0, 50.0, 90.0], TestStartTime, TestEndTime, TestParameterDict, TestCurrentWeekDayID)
    print "Opt_Solution = %s"%(OptSolution)
    print "Opt_Importance = %s"%(OptImportant)
    print "Opt_Total_Solution_Score = %f"%(OptTotalScore)
    (FinalSolution, FinalSolutionDetail, FinalScore) = schOpt.evaluate_Solution(OptSolution, OptImportant, TestStartTime, TestEndTime, TestParameterDict, TestCurrentWeekDayID)
    print "Current_Solution = %s"%(FinalSolution)
    print "Total_Solution_Score = %f"%(FinalScore)
    print "Current_Solution_Detail = %s"%(FinalSolutionDetail)


    (OptSolution, OptImportant, OptTotalScore) = schOpt.run_LocalSearchImprovingHeuristic(OptSolution, ['A1', 'A2', 'A3'], [100.0, 50.0, 90.0], TestStartTime, TestEndTime, TestParameterDict, TestCurrentWeekDayID, 100)
    print "Opt_Solution = %s"%(OptSolution)
    print "Opt_Importance = %s"%(OptImportant)
    print "Opt_Total_Solution_Score = %f"%(OptTotalScore)
