#!/bin/sh
ffmpeg -video_size 1280x720 -framerate 23.976 -f x11grab -i :0.0+0,0 -f pulse -ac 2 -i default $1
