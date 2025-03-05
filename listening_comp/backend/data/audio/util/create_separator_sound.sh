# Create silent and beep audio segments
ffmpeg -f lavfi -i "anullsrc=r=24000:cl=mono" -t 0.25 -q:a 9 silence.mp3
ffmpeg -f lavfi -i "sine=frequency=1000:duration=0.25" -q:a 9 beep.mp3

# Create a temporary file list
echo "file 'silence.mp3'" > filelist.txt
echo "file 'beep.mp3'" >> filelist.txt
echo "file 'silence.mp3'" >> filelist.txt

# Concatenate the files
ffmpeg -f concat -safe 0 -i filelist.txt -c:a libmp3lame -b:a 192k separator_sound.mp3

# Clean up
rm filelist.txt
rm silence.mp3
rm beep.mp3