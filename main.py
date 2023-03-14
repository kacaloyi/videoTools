from __future__ import print_function
import os
import sys
import tempfile
import logging

import ffmpy

from scenedetect.video_manager import VideoManager
from scenedetect.scene_manager import SceneManager
from scenedetect.frame_timecode import FrameTimecode
from scenedetect.stats_manager import StatsManager
from scenedetect.detectors import ContentDetector
from scenedetect import detect, ContentDetector
from scenedetect import split_video_ffmpeg
from scenedetect import SceneManager, open_video, ContentDetector
'''
文档参考：
http://scenedetect.com/projects/Manual/en/latest/
http://scenedetect.com/projects/Manual/en/latest/api.html#overview

'''


STATS_FILE_PATH = 'testvideo.stats.csv'

#视频合并
def  video_clip_concat(videolist:list,outputfile:str):
    # 创建临时文件
    temp_dir = tempfile.mktemp()
    os.mkdir(temp_dir)
    concat_file = os.path.join(temp_dir, 'concat_list.txt')

    with open(concat_file, 'w', encoding='utf-8') as f:
        ss = []
        while videolist:
            ss += 'file '+ videolist.pop()

        f.write('\n'.join(ss))
        f.close()

    ff = ffmpy.FFmpeg(
        global_options=['-f', 'concat'],
        inputs={concat_file: None},
        outputs={outputfile: ['-c', 'copy']}
    )

    ff.run()
    return

'''
#ffmpeg -i video_name.mp4 -vf select='eq(pict_type\,I)' -vsync 2 -s 1920*1080 -f image2 keyframe-%02d.jpeg
各参数解释:
-i :输入文件，这里的话其实就是视频；
-vf:是一个命令行，表示过滤图形的描述。选择过滤器select会选择帧进行输出：pict_type和对应的类型:PICT_TYPE_I 表示是I帧，即关键帧；
-vsync 2:阻止每个关键帧产生多余的拷贝；
-f image2 name_%02d.jpeg:将视频帧写入到图片中，样式的格式一般是: “%d” 或者 “%0Nd”
-s:分辨率，1920*1080

'''
#抽取视频中的所有关键帧，存储为图片，可用于AI训练
#参数是视频文件名和输出目录
def get_video_keyframes(videofile:str,outputpath:str='./'):
    from scenedetect.platform import (tqdm, invoke_command, CommandTooLong, get_file_name,
                                  get_ffmpeg_path)   
    logger = logging.getLogger('keyframe_video')

    if isinstance(videofile, list):
        raise ValueError('用一个字符串文件名，不要用列表,一次一个视频')
    
    keyname = os.path.basename(videofile).split('.')[0]

    if  os.path.exists(outputpath) ==False:
        os.mkdir(outputpath)

    try:
        call_list = ['ffmpeg']
        call_list +=['-i']
        call_list +=[videofile]
        call_list +=['-vf']
        call_list +=["select='eq(pict_type\,I)'"]
        call_list +=['-vsync']
        call_list +=['2']
        call_list +=["-f"]
        call_list +=["image2"]
        call_list +=[outputpath+'/'+keyname+'-%08d.jpeg']
        
        #call_list += ['-v', 'quiet'] 
        # Only show ffmpeg output for the first call, which will display any
        # errors if it fails, and then break the loop. We only show error messages
        # for the remaining calls.
        call_list += ['-v', 'error']
        ret_val = invoke_command(call_list)
        if ret_val != 0:
            # TODO(v0.6.2): Capture stdout/stderr and display it on any failed calls.
            logger.error('Error splitting video (ffmpeg returned %d).', ret_val)
            
    except CommandTooLong:
        logger.error("命令行太长了")
    except OSError:
        logger.error("系统出错了")
        return

    return

# 视频随机抽走一帧，避免视频重复。
def extract_frame(videofile: str, output: str, fps, weight, height, start, end):
    import cv2
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    videoWriter = cv2.VideoWriter(output, fourcc, fps, (weight, height))
    vc = cv2.VideoCapture(videofile)
    if vc.isOpened():
        ret, frame = vc.read()
    else:
        ret = False
    count = 0  # count the number of pictures
    while ret:
        ret, frame = vc.read()
        if start <= count <= end:
            count += 1
            continue
        else:
            videoWriter.write(frame)
            count += 1
    print(count)
    videoWriter.release()
    vc.release()


#会消耗不少时间，没有卡住，不用慌
#场景侦测
def scenelist(videofile):

    print("会消耗不少时间，没有卡住，不用慌")
    scene_list = detect(videofile, ContentDetector())
    for i, scene in enumerate(scene_list):
        print('Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
        i+1,
        scene[0].get_timecode(), scene[0].get_frames(),
        scene[1].get_timecode(), scene[1].get_frames(),))

#按场景切割
def scenesplit(videofile,scene_list):
    print("会消耗不少时间，没有卡住，不用慌")
    path = videofile.split(".")[0]
    if  os.path.exists(path) ==False:
        os.mkdir(path)
    #scene_list = detect('my_video.mp4', ContentDetector())
    split_video_ffmpeg(videofile, scene_list,show_output=True,
                       arg_override="-vcodec copy -acodec copy",
                       output_file_template = path+'/$VIDEO_NAME-$SCENE_NUMBER.mp4',)


#试用sceneManager和阈值
def find_scenes(video_path, threshold=27.0):
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold))
    # Detect all scenes in video from current position to end.
    scene_manager.detect_scenes(video)
    # `get_scene_list` returns a list of start/end timecode pairs
    # for each scene that was found.
    return scene_manager.get_scene_list()

#带回调,带捕捉硬件视频流。
def test_api_device_callback(test_video_file: str):
    """Demonstrate how to use a webcam/device/pipe and a callback function.
    Instead of calling `open_video()`, an existing `cv2.VideoCapture` can be used by
    wrapping it with a `VideoCaptureAdapter.`"""
    import cv2
    import numpy
    from scenedetect import SceneManager, ContentDetector, VideoCaptureAdapter

    # Callback to invoke on the first frame of every new scene detection.
    def on_new_scene(frame_img: numpy.ndarray, frame_num: int):
        print("New scene found at frame %d." % frame_num)

    # We open a file just for test purposes, but we can also use a device or pipe here.
    cap = cv2.VideoCapture(test_video_file)
    video = VideoCaptureAdapter(cap)
    # Now `video` can be used as normal with a `SceneManager`. If the input is non-terminating,
    # either set `end_time/duration` when calling `detect_scenes`, or call `scene_manager.stop()`.
    total_frames = 1000
    scene_manager = SceneManager(stats_manager=StatsManager())
    scene_manager.add_detector(ContentDetector())
    scene_manager.detect_scenes(video=video,  callback=on_new_scene)
    #scene_manager.detect_scenes(video=video, duration=total_frames, callback=on_new_scene)
   # Save per-frame statistics to disk.
    filename = '%s.stats.csv' % test_video_file
    scene_manager.stats_manager.save_to_csv(csv_file=filename)

    return scene_manager.get_scene_list()

"""Demonstrate how to use a webcam/device/pipe and a callback function.
Instead of calling `open_video()`, an existing `cv2.VideoCapture` can be used by
wrapping it with a `VideoCaptureAdapter.`"""

import numpy
from scenedetect import SceneManager, ContentDetector, VideoCaptureAdapter
def default_calll_back(frame_img: numpy.ndarray, frame_num: int):
        print("New scene found at frame %d." % frame_num)


def main_scene_split(videofile:str,
                     starttime:FrameTimecode|None=None,
                     endtime:FrameTimecode|None=None,
                     threshold:float=27.0,
                     callback=default_calll_back):
    #一次拆分一个视频，不要多个。
    video_manager = VideoManager([videofile])
    base_timecode = video_manager.get_base_timecode()

    try:
        
        scene_manager = SceneManager(stats_manager=StatsManager())
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        # Set video_manager duration to read frames from 00:00:00 to 00:00:20.
        video_manager.set_duration(start_time=starttime, end_time=endtime)

        # Set downscale factor to improve processing speed.
        video_manager.set_downscale_factor()

        # Start video_manager.
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager,  callback=callback)
        #scene_manager.detect_scenes(video=video, duration=total_frames, callback=on_new_scene)
        # Save per-frame statistics to disk.
        filename = '%s.stats.csv' % videofile
        scene_manager.stats_manager.save_to_csv(csv_file=filename)

        scenesplit(videofile,scene_manager.get_scene_list())

    finally:
        video_manager.release()

    return 

def main():
# Create a video_manager point to video file testvideo.mp4. Note that multiple
# videos can be appended by simply specifying more file paths in the list
# passed to the VideoManager constructor. Note that appending multiple videos
# requires that they all have the same frame size, and optionally, framerate.

    video_manager = VideoManager(['test.mp4'])
    stats_manager = StatsManager()
    scene_manager = SceneManager(stats_manager)
# Add ContentDetector algorithm (constructor takes detector options like threshold).
    scene_manager.add_detector(ContentDetector())
    base_timecode = video_manager.get_base_timecode()

    try:
        # If stats file exists, load it.
        if os.path.exists(STATS_FILE_PATH):
            # Read stats from CSV file opened in read mode:
            with open(STATS_FILE_PATH, 'r') as stats_file:
                stats_manager.load_from_csv(stats_file, base_timecode)
                start_time = base_timecode + 20 # 00:00:00.667
                end_time = base_timecode + 20.0 # 00:00:20.000

                # Set video_manager duration to read frames from 00:00:00 to 00:00:20.
                video_manager.set_duration(start_time=start_time, end_time=end_time)

                # Set downscale factor to improve processing speed.
                video_manager.set_downscale_factor()

                # Start video_manager.
                video_manager.start()

                # Perform scene detection on video_manager.
                scene_manager.detect_scenes(frame_source=video_manager)

                # Obtain list of detected scenes.
                scene_list = scene_manager.get_scene_list(base_timecode)

                # Like FrameTimecodes, each scene in the scene_list can be sorted if the
                # list of scenes becomes unsorted.
                print('List of scenes obtained:')

                for i, scene in enumerate(scene_list):
                    print(' Scene %2d: Start %s / Frame %d, End %s / Frame %d' % (
                    i+1,
                    scene[0].get_timecode(), scene[0].get_frames(),
                    scene[1].get_timecode(), scene[1].get_frames(),))

                # We only write to the stats file if a save is required:
            if stats_manager.is_save_required():
                with open(STATS_FILE_PATH, 'w') as stats_file:
                    stats_manager.save_to_csv(stats_file, base_timecode)

    finally:
          video_manager.release()


if __name__ == "__main__":
    videofile = sys.argv[1]
    #arg2 = sys.argv[2]
    #scenelist(videofile)
    #scenesplit(videofile,test_api_device_callback(videofile))
    #main()

    
    #main_scene_split(videofile)
    get_video_keyframes(videofile,"./keyframes")
