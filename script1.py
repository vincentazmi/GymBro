import gspread, datetime, sys
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
except FileNotFoundError as e:
    print("Please make sure 'creds.json' is in the same directory as this script")
    raise e

client = gspread.authorize(creds)

sheet = client.open("Copy of GYM").sheet1


NAMES = []
daysData = sheet.row_values(1) # whole first row

for i in range(1,len(daysData)): # 1, to skip product of vincent
    if daysData[i] != '':
        NAMES.append([i+1,daysData[i]])

# add end column index for n-1 days        
for i in range(1,len(NAMES)):
    NAMES[i-1].append(NAMES[i][0]-1)

dayNames = [i for i in daysData if i != ''][1:] # just names first row
exerciseNames = [i for i in sheet.row_values(2) if i != ''] # exercise names

# add end column index for the last day
NAMES[-1].append(len(exerciseNames)*8+2)



WEEK_ROW = datetime.date.today().isocalendar().week - 21 # week row
##print(WEEK_ROW)
weekData = sheet.row_values(WEEK_ROW) # week data (kg, reps)
CHANGES_MADE = False # changes made to week data

# make weekData as long as there are columns
if len(weekData) < NAMES[-1][2]:
    for i in range(len(weekData),NAMES[-1][2]):
        weekData.append('')

##print(NAMES[-1][2],len(weekData))
##print(NAMES)

# Replace end column index with exercise count
for i in range(len(NAMES)):
    NAMES[i][2] = int((NAMES[i][2]-NAMES[i][0]+1)/8)


def mainMenu():
    print("*** Editing: Week starting",weekData[1],"***\n")
    text = "Which day would you like to edit?\nC - Change week\n"
    for i in range(len(dayNames)):
        text += "{} - {}\n".format(i+1,dayNames[i])
    option = input(text+"0 - Quit\n")

    # input validation
    if option.upper() == "C":
        if CHANGES_MADE: applyChanges()
        changeWeek()
        option = mainMenu()
    try:
        option = int(option)
        if option > text.count('\n') or option < 0: raise
    except:
        print("Please try again option={}\n".format(option))
        option = mainMenu()

    if option == 0: return option
    exerciseSelect(option)
    return mainMenu()

def exerciseSelect(dayIndex):
    text = "Which exercise would you like to edit?\n"

    # Count exercises prior to selected day
    prevExercises = 0
    for i in range(dayIndex-1): # dayIndex is from 1-4
        prevExercises += NAMES[i][2]

    exerciseCount = NAMES[dayIndex-1][2]
    for i in range(exerciseCount):
        

        # Missing sets
        setCount = 0
        for setNum in range(4):
##            print(2+(prevExercises+i)*8+setNum*2)
            try: setKG = weekData[2+(prevExercises+i)*8+setNum*2]
            except: setKG = None
            
            if setKG == None or setKG == '': setCount += 1
##            else: print("*",setKG)
            
##        if setCount > 0: text += " (Missing {}/4 Sets)\n".format(setCount)
        text += "{} - [{}/4] {}\n".format(i+1, 4-setCount, exerciseNames[i+prevExercises])
##        else: text += "\n"
        
    option = input(text+"0 - Back\n")
    # input validation
    try:
        option = int(option)
        if option > text.count('\n') or option < 0: raise
    except:
        print("Please try again\n")
        option = exerciseSelect(dayIndex)

    if option == 0: return option
    setSelect(option+prevExercises)
    return exerciseSelect(dayIndex)

def setSelect(exerciseIndex):
    col = (exerciseIndex-1)*8+2

    text = ""
    for i in range(4):
        try:
            setKG = weekData[col + i*2]
            setReps = weekData[col + i*2 +1]
            if setKG == '': setKG = '_'
            if setReps == '': setReps = '_'
        except:
            setKG = '_'
            setReps = '_'
        text += "Set {} - {}kg x{}\n".format(i+1, setKG, setReps)

    option = input(text+"0 - Back\n")

    # input validation
    try:
        option = int(option)
        if option > text.count('\n') or option < 0: raise
    except:
        print("Please try again\n")
        option = setSelect(exerciseIndex)

##    print(CHANGES_MADE)
    if option == 0: return option
    editSet(col+(option-1)*2)
    return setSelect(exerciseIndex)

def editSet(setIndex):
    print("Old - {}kg x{}\n".format(weekData[setIndex],weekData[setIndex+1]))
    kg = input("KG: ")
    reps = input("Reps: ")

    try:
        kg = int(kg)
        reps = int(reps)
    except:
        print("Please try again")
        kg, reps = editSet(setIndex)
        
    weekData[setIndex] = str(kg)
    weekData[setIndex+1] = str(reps)
    
    global CHANGES_MADE
    CHANGES_MADE = True
    
    return kg, reps

def applyChanges():
    newData = []
    for x in weekData:
        if x == '-':
            newData.append('')
        else:
            newData.append(x)
            
    sheet.update('A{}:HJ{}'.format(WEEK_ROW,WEEK_ROW),[newData])

def changeWeek():
    upOrDown = input("""You are editing week starting {}
P - Previous week
N - Next week
""".format(weekData[1]))
    if upOrDown == "0": return
    elif upOrDown.upper() == "P": updateWeek(0)
    elif upOrDown.upper() == "N": updateWeek(1)
    
    else:
        print("Try again or 0 to Exit")
        return changeWeek()

def updateWeek(upOrDown):
    global WEEK_ROW
    global weekData
    if upOrDown: # 1 = next week
        WEEK_ROW += 1
    else: # 0 = prev week
        WEEK_ROW -= 1
    if WEEK_ROW < 5: WEEK_ROW = 5 # First week is on row 5
    elif WEEK_ROW > 31: WEEK_ROW = 31 # Last week of 2023 is on row 31

    weekData = sheet.row_values(WEEK_ROW) # week data (kg, reps)

if __name__ == "__main__":
    mainMenu()
    
    if CHANGES_MADE: applyChanges()





    
