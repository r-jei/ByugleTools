#################################
	BYUGLE MIRROR
################################
Readme.txt updated June 5, 2018

1. GENERAL INFORMATION: WHAT DOES IT DO?

The program makes a copy of every video thumbnail and put the copies here: http://videoweb.lib.byu.edu/images/BYU_thumbs/

The directory structure of BYU_thumbs exactly matches that of the video server (fletcher). So for instance, if there's a video file on fletcher at:
BYU/HBLL/ERS/2017/2017FEB03 - ERS - James Galvin.mp4

the program will copy the video's existing thumbnail into:
http://videoweb.lib.byu.edu/images/BYU_thumbs/HBLL/ERS/2017/2017FEB03 - ERS - James Galvin.jpg

It does not automatically maintain this relationship between thumbnail and video servers, meaning that if I go in and reorganize the way the video files are stored, I would have to run this program again if I wanted to keep things mirror-imaged.

It's non-destructive: Old thumbnails are not deleted, and their URLs are recorded in the Notes section of the video's Admin Edit page rather than simply being overwritten with the URL of the new thumbnail. 

Also, the program adds the Date, Series, Speaker, Title information to the video description (if it's not already there.) This is because searching Byugle only returns hits from the Title and Description fields. By putting the name of the speaker in the video description, it becomes possible to search by speaker as well. (So, this is just a workaround for how dumb Byugle is).

##############################
##############################

2. POSSIBLE ISSUES AND TROUBLESHOOTING:

Byugle Mirror records the ID of every video it processes in log.txt. If something goes wrong, examining the metadata of the offending video can be helpful. So if I have VID_ID: 786, I know that I can check that video out at byugle.lib.byu.edu/editVideoDataAdmin.php?vid=786

If the streaming URL of the video is long enough, the new thumbnail's URL will be too long (i.e. longer than 200 characters). Byugle will reject the new thumbnail URL in this case. When this program was first used, (June 4 2018), 25 videos out of the 1896 on Byugle had this issue. 

I've had some problems with unicode characters (Å, é, ƒ, ø, etc.). As far as I'm aware the issue is resolved but if there are problems, and you notice unicode characters in the video metadata, it's worth checking out.


