##  @package seal.cld.ui.video
#   Provides VideoData.

from seal.app.html import *


##  Returns a RawFile representing the contents of a video.

def VideoData (source):
    if isinstance(source, str):
        return RawFile(source, 'mp4')
    else:
        raise HttpException('Bad video source: %s' % repr(source))


# class VideoEditor (HtmlDirectory):
# 
#     pass
