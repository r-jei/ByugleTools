import os
import sys
from Handler import Handler
from mirror import Mirror

def main(argv):
    
    incorrect_input = False
    
    if len(argv)<4:
        incorrect_input = True
    else:
        USERNAME = argv[1]
        PASSWORD = argv[2]
        START_ID = argv[3]

    if len(argv) == 4:
        END_ID = str(int(argv[3])+1)
        
    if len(argv) == 5:
        if int(argv[4]) > int(START_ID):
            END_ID = str(int(argv[4])+1)
        else:
            incorrect_input = True

    if len(argv)>5:
        incorrect_input = True

    if incorrect_input:
        print 'Usage: python mirror.py username password vid_id_start vid_id_end\n' +\
                'vid_id_start must be less than vid_id_end'
        return
    
    welcome = "\n#######################################\n WELCOME TO THE BYUGLE MIRROR PROGRAM\n" + \
    "#######################################\n"
    print(welcome)

    mirror = Mirror( USERNAME, PASSWORD )
    
    for ID in range(int(START_ID),int(END_ID)):
        result = mirror.update_video( str(ID) )

if __name__ == "__main__":
    main(sys.argv)
