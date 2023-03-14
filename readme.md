
视频工具

按场景分解视频
提取视频中的关键帧成图片

用于AI训练取材。

使用方法：
需要相关依赖
需要ffmpeg安装在Path目录中。

文档参考：
http://scenedetect.com/projects/Manual/en/latest/
http://scenedetect.com/projects/Manual/en/latest/api.html#overview


官方网站：[http://ffmpeg.org/](http://ffmpeg.org/)

## **组件**

FFmpeg项目由以下几部分组成：

1.FFmpeg视频文件转换命令行工具,也支持经过实时电视卡抓取和编码成视频文件；

2.ffserver基于HTTP、RTSP用于实时广播的多媒体服务器.也支持时间平移；

3.ffplay用 SDL和FFmpeg库开发的一个简单的媒体播放器；

4.libavcodec一个包含了所有FFmpeg音视频编解码器的库。为了保证最优性能和高可复用性，大多数编解码器从头开发的；

5.libavformat一个包含了所有的普通音视格式的解析器和产生器的库。

安装 

**1. 下载**

下载地址: http://ffmpeg.org/download.html

解压即可

****2. 本地路径配置****

打开“编辑系统环境变量”–>“高级”–>“环境变量” 

找到”`path`“，点选后点击”编辑“，在弹出窗口添加刚才拷贝的’bin’路径

**3. 验证配置成功**

`win+R`打开`cmd`命令行窗口，然后输入`ffmpeg -version`来验证是否配置成功。

查看帧信息

```bash
#第一种 XML 格式
ffprobe -show_frames -select_streams v -of xml out.mp4 >outframes.info
#第二种 场景转换 txt格式
ffprobe -show_frames -of compact=p=0 -f lavfi "movie=foo.mp4,select=gt(scene\,.4)" > foo.txt
```

不需要把整个视频看一遍，抽取视频帧，便于后面的操作。

## 抽帧

**I帧** 表示关键帧，是最完整的帧画面，一般视频封面都选择I帧；

**P帧** 单预测帧，利用之前的I帧或P帧，采用运动预测的方式进行帧间预测编码；

**B帧** 双向预测帧，利用双向帧进行预测编码；

基于ffmeg进行抽帧共有四种方式：

抽取视频关键帧(I/P/B)
抽取视频场景转换帧
根据时间进行均匀抽帧
抽取指定时间的视频帧

**1.抽取视频关键帧(IPB):**
视频关键帧（Video Keyframes）是用于视频压缩和视频编解码的帧，视频关键帧是包含了完整信息的帧，其他的非关键帧将会使用与关键帧的差值进行压缩。视频帧具体可以分为IPB帧三种：

I帧表示关键帧，是最完整的帧画面，一般视频封面都选择I帧；
P帧单预测帧，利用之前的I帧或P帧，采用运动预测的方式进行帧间预测编码；
B帧双向预测帧，利用双向帧进行预测编码；

一般情况下关键帧I帧是信息最多的帧，也是用途最多的帧。在视频检索和视频分类任务中一般都借助I帧来完成，I帧数量少包含的信息却是最多的。

#使用ffprobe提取出IPB帧的时间：

```bash

ffprobe -i 666051400.mp4 -v quiet -select_streams v -show_entries frame=pkt_pts_time,pict_type
```

使用ffmpeg抽取IPB帧到jpg图片：

```bash
# 抽取I帧
ffmpeg -i 666051400.mp4 -vf "select=eq(pict_type\,I)"  -vsync vfr -qscale:v 2 -f image2 ./%08d.jpg
# 抽取P帧
ffmpeg -i 666051400.mp4 -vf "select=eq(pict_type\,P)"  -vsync vfr -qscale:v 2 -f image2 ./%08d.jpg
# 抽取B帧
ffmpeg -i 666051400.mp4 -vf "select=eq(pict_type\,B)"  -vsync vfr -qscale:v 2 -f image2 ./%08d.jpg
```

由于ffmpeg抽取帧并无法按照时间戳来命名，需要

1. 抽取视频场景转换帧
在视频中可以按照视频的镜头切换可以将视频分为不同的场景（scene boundarie）。视频场景抽取算法一般是使用帧间的相似差异程度来衡量，如果视频帧大于某一个阈值则认为是一个新的场景，否则不是一个新的场景。

使用ffmpeg抽取视频场景转换帧的命令：

```bash
# 其中0.1表示帧为新场景的概率
ffmpeg -i 666051400.mp4 -filter:v "select='gt(scene,0.1)',showinfo" -f null - 2>&1
```

3. 均匀抽帧
通过ffmpeg根据时间均匀抽帧的命令行：

```bash
# -r 指定抽取的帧率，即从视频中每秒钟抽取图片的数量。1代表每秒抽取一帧。
ffmpeg -i 666051400.mp4 -r 1 -q:v 2 -f image2 ./%08d.000000.jpg
```

4. 抽取指定时间的帧
通过ffmepg抽取指定时间的帧：

```bash
# 耗时0.07s
ffmpeg -ss 00:00:30 -i 666051400.mp4 -vframes 1 0.jpg
# 耗时0.68s
ffmpeg -i 666051400.mp4 -ss 00:00:30  -vframes 1 0.jpg
```

**抽取指定时间的视频**

```bash
ffmpeg -i input.mp4 -ss 1:05 -t 10 output.mp4
ffmpeg -ss 1:05 -i input.mp4 -t 10 -c:v copy -c:a copy output.mp4
```

-ss 5指定从输入视频第1:05秒开始截取，-t 10指明最多截取10秒;
把-ss 1:05放到-i前面，与原来的区别是，这样会先跳转到第1:05秒在开始解码输入视频，而原来的会从开始解码，只是丢弃掉前1:05秒的结果。

-t 指定所需剪辑的持续时间-t。例如，-ss 40 -t 10指示 FFmpeg 从第 40 秒开始提取 10 秒的视频。

-to 指定结束时间-to。例如，-ss 40 -to 70指示 FFmpeg 从第 40 秒到第 70 秒提取 30 秒的视频。
-c:v 和 -c:a分别指定视频和音频的编码格式。
-c:v copy -c:a copy标示视频与音频的编码不发生改变，而是直接复制，这样会大大提升速度。

合并视频

```bash
//进行视频的合并
ffmpeg -f concat -i list.txt -c copy concat.mp4
```

在list.txt文件中，对要合并的视频片段进行了描述。

内容如下

```bash
file ./split.mp4
file ./split1.mp4
```

常用命令如下

```bash
// 去掉视频中的音频
ffmpeg -i input.mp4 -vcodec copy -an output.mp4
// -an: 去掉音频；-vcodec:视频选项，一般后面加copy表示拷贝

// 提取视频中的音频
ffmpeg -i input.mp4 -acodec copy -vn output.mp3
// -vn: 去掉视频；-acodec: 音频选项， 一般后面加copy表示拷贝

// 音视频合成
ffmpeg -y –i input.mp4 –i input.mp3 –vcodec copy –acodec copy output.mp4
// -y 覆盖输出文件

//剪切视频
ffmpeg -ss 0:1:30 -t 0:0:20 -i input.mp4 -vcodec copy -acodec copy output.mp4
// -ss 开始时间; -t 持续时间

// 视频截图
ffmpeg –i test.mp4 –f image2 -t 0.001 -s 320x240 image-%3d.jpg
// -s 设置分辨率; -f 强迫采用格式fmt;

// 视频分解为图片
ffmpeg –i test.mp4 –r 1 –f image2 image-%3d.jpg
// -r 指定截屏频率

// 将图片合成视频
ffmpeg -f image2 -i image%d.jpg output.mp4

//视频拼接
ffmpeg -f concat -i filelist.txt -c copy output.mp4

// 将视频转为gif
ffmpeg -i input.mp4 -ss 0:0:30 -t 10 -s 320x240 -pix_fmt rgb24 output.gif
// -pix_fmt 指定编码

// 将视频前30帧转为gif
ffmpeg -i input.mp4 -vframes 30 -f gif output.gif

// 旋转视频
ffmpeg -i input.mp4 -vf rotate=PI/2 output.mp4

// 缩放视频
ffmpeg -i input.mp4 -vf scale=iw/2:-1 output.mp4
// iw 是输入的宽度， iw/2就是一半;-1 为保持宽高比

//视频变速
ffmpeg -i input.mp4 -filter:v setpts=0.5*PTS output.mp4

//音频变速
ffmpeg -i input.mp3 -filter:a atempo=2.0 output.mp3

//音视频同时变速，但是音视频为互倒关系
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]" -map "[v]" -map "[a]" output.mp4

// 视频添加水印
ffmpeg -i input.mp4 -i logo.jpg -filter_complex [0:v][1:v]overlay=main_w-overlay_w-10:main_h-overlay_h-10[out] -map [out] -map 0:a -codec:a copy output.mp4
// main_w-overlay_w-10 视频的宽度-水印的宽度-水印边距；
```


场景检测，并且批量分割视频

需要：ffmpeg + PySceneDetect分割视频需

批量分割目录下的所有视频指令：（做成bat)

```bash
for %%i in (*) do \\
scenedetect -i "%%i" -s "%%i.stats.csv" detect-content \\
list-scenes split-video -o "%%i_Output_video" 
```

批量分割，并生成截图

```bash
for %%i in (*) do \\
scenedetect -i "%%i" -s "%%i.stats.csv" detect-content \\
list-scenes save-images -n 1 -o "%%i_Output_images" \\
split-video -o "%%i_Output_video" 
```

批量分割，生成截图，还生成html

```bash
for %%i in (*) do \\
scenedetect -i "%%i" -s "%%i.stats.csv" detect-content \\
list-scenes save-images -n 1 -o "%%i_Output_images" \\
export-html -w 400 \\
split-video -o "%%i_Output_video" 
```

**1. 什么是PySceneDetect**

PySceneDetect是一个命令行工具和Python库，用于分析视频，查找场景更改或剪辑。

PySceneDetect集成了外部工具（例如mkvmerge ， ffmpeg ），可在使用split-video命令时自动将视频分割为单个片段。还可以为视频生成逐帧分析，称为统计文件，以帮助确定最佳阈值或检测特定视频的模式/其他分析方法。

PySceneDetect使用两种主要的检测方法：**detect-threshold**（将每个帧与设置的黑电平进行比较，对于检测从黑色到黑色的淡入和淡出有用）和**detect-content** （比较每个帧，依次查找内容的变化，有用）用于检测视频场景之间的快速切换，尽管处理速度较慢）。每种模式的参数略有不同，并在文档中进行了详细说明.。

通常，如果要使用淡入/淡出/切成黑色来检测场景边界，请使用检测阈值模式。如果视频在内容之间使用大量快速剪切，并且没有明确定义的场景边界，则应使用" 检测内容"模式。一旦知道要使用哪种检测模式，就可以尝试以下建议的参数，或生成统计文件（使用-s / –stats参数），以确定正确的参数-具体来说，是正确的阈值

**2.PySceneDetect的安装**

PySceneDetect依赖于Python模块numpy，OpenCV（cv2模块）和tqdm（进度条模块，用来显示处理进度），安装命令如下：

$ pip install scenedetect

PySceneDetect基于ffmpeg和mkvmerge对视频进行裁剪。

**3. 命令行使用**

PySceneDetect在命令行中使用scenedetect命令进行操作，命令格式如下：

```bash
$ scenedetect --input my_video.mp4 \\
--output my_video_scenes \\
--stats my_video.stats.csv detect-content \\
list-scenes save-images
```

**参数说明：**

常用的参数说明如下：

–input ：输入视频文件的路径

–output ：指定输出目录（可选）

–stats：生成统计文件（可选）

time：用于设置输入视频持续时间/长度或开始/结束时间。

detect-content：切分视频基于内容检测算法。

detect-threshold：切分视频基于阈值检测算法。

list-scenes：打印场景列表并输出到CSV文件。

save-images：为每个场景保存视频中的图像。

split-video：使用ffmpeg或mkvMerge对视频进行分割。

完整的参数列表可使用scenedetect help all命令进行查看。

**4. 在Python中使用**

在Python中使用PySceneDetect主要用到下面几个类：

- VideoManager：用于加载视频并提供搜索；
- SceneManager：用于协调SceneDetector，VideoManager和可选的StatsManager对象的高级管理器；
- FrameTimecode：用于存储时间码以及对时间码值进行算术运算（加/减/比较），并具有帧级的精确度；
- StatsManager：用于存储/缓存帧指标，以加快在同一视频上后续场景检测的运行速度，并可以保存到CSV文件或从CSV中加载缓存；
- SceneDetector：用于实现检测算法的基类，如ContentDetector，ThresholdDetector等。