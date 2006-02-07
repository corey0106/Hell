"""

SmartPar - Functions for identifying potential par files from their their real filename
(as defined in their uuenc/yenc headers), and only downloading them when needed

(c) Copyright 2005 Philip Jenvey
[See end of file]
"""
import re, Hellanzb
from twisted.internet import reactor
from xml.sax import make_parser, SAXParseException
from xml.sax.handler import ContentHandler, feature_external_ges, feature_namespaces
from Hellanzb.Log import *
from Hellanzb.PostProcessorUtil import getParName, getParRecoveryName, isPar, isPar1, \
    isPar2, PAR1, PAR2
from Hellanzb.Util import isHellaTemp, FatalError
from Hellanzb.NZBLeecher.ArticleDecoder import setRealFileName, stripArticleData, \
    tryFinishNZB, ySplit

__id__ = '$Id$'

def dequeueIfExtraPar(segment, inMainThread = False):
    """ This function is called after downloading the first segment of every nzbFile

    It determines whether or not the segment's parent nzbFile is part of a par archive. If
    it is and is also an 'extra' par file ('extra' pars are pars other than the first
    par. the first par nzbFiles should contain only verification data, and no recovery
    data), this function will determine whether or not the rest of the nzbFile segments
    need to be downloaded (dequeueing them necessary)

    Optionally specifying tryFinishWhenSkipped will attempt to ArticleDecoder.tryFinishNZB
    upon completition (completely stop the downloader loop when there are no files left to
    download) """
    if segment.number != 1:
        raise FatalError('dequeueIfExtraPar on number > 1')

    dequeuedCount = 0
    
    if segment.nzbFile.filename is None or isHellaTemp(segment.nzbFile.filename):
        segment.loadArticleDataFromDisk()
        stripArticleData(segment.articleData)

        # A stripped down version of the Article.parseArticleData loop: find the real
        # filename in the downlaoded segment data as quickly as possible
        index = -1
        for line in segment.articleData:
            index += 1

            # Don't prolong the search
            if index > 20:
                break

            if line.startswith('=ybegin'):
                ybegin = ySplit(line)
                setRealFileName(segment.nzbFile, ybegin['name'],
                                settingSegmentNumber = segment.number)
                break

            elif line.startswith('begin '):
                filename = line.rstrip().split(' ', 2)[2]
                setRealFileName(segment.nzbFile, filename,
                                settingSegmentNumber = segment.number)
                break

    if segment.nzbFile.filename == None:
        # We can't do anything 'smart' without the filename
        return dequeuedCount

    identifyPar(segment.nzbFile)

    if segment.nzbFile.isParFile:
        parTypeName = getParName(segment.nzbFile.parType)
            
        size = segment.nzbFile.totalBytes / 1024 / 1024
        if segment.nzbFile.isExtraParFile:
            # Extra par2 -- dequeue the rest of its segments
            dequeueSegments = segment.nzbFile.todoNzbSegments.copy()
            dequeueSegments.remove(segment)
            dequeuedCount = len(dequeueSegments)

            # Ensure the dequeue work is done in the reactor, so don't have to lock
            if inMainThread:
                Hellanzb.queue.dequeueSegments(dequeueSegments)
            else:
                reactor.callFromThread(Hellanzb.queue.dequeueSegments, dequeueSegments)
                
            segment.nzbFile.isSkippedPar = True
            info('Skipped %s: %s (%iMB)' % (parTypeName, segment.nzbFile.filename, size))
        else:
            info('Queued %s: %s (%iMB, %i %s)' % (parTypeName, segment.nzbFile.filename, size,
                                                  getParSize(segment.nzbFile.filename),
                                                  getParRecoveryName(segment.nzbFile.parType)))
    return dequeuedCount

def queueExtraPars(failedSegment):
    """ Determine an estimated recovery blocks value for the known invalid segment file, and
    requeue that number of extra pars files """
    # If par1: return 1 -- how do we know we need par 1 files? (if all known extra par
    # files are par1s?)
    
    # if par2: ... how do we know we need par2 files?
    pass

PAR2_VOL_RE = re.compile(r'(.*)\.vol(\d*)\+(\d*)\.par2', re.I)
def identifyPar(nzbFile):
    """ Mark the nzbFile object as isParFile, and if so, also mark its parType and
    isExtraParFile vars """
    if isPar(nzbFile.filename):
        nzbFile.isParFile = True
    
        if isPar2(nzbFile.filename):
            nzbFile.parType = PAR2
            if not PAR2_VOL_RE.match(nzbFile.filename):
                return
        elif isPar1(nzbFile.filename):
            nzbFile.parType = PAR1
            if nzbFile.filename.lower().endswith('.par'):
                return

        # Does not match, mark the nzbFile as an extra par file
        if nzbFile.nzb.isParRecovery and nzbFile.nzb.parPrefix in nzbFile.subject and \
                nzbFile.nzb.neededBlocks > 0:
            nzbFile.nzb.neededBlocks -= getParSize(nzbFile.filename)
        else:
            # This nzbFile should be completely skipped
            nzbFile.isExtraParFile = True

GET_PAR2_SIZE_RE = re.compile(r'(?i).*\.vol\d{1,8}\+(\d{1,8}).par2$')
def getParSize(filename):
    """ Determine the par 'size' (type of size depends on the parType) of the par file with
    the specified filename """
    if isPar1(filename):
        return 1
    elif isPar2(filename):
        size = GET_PAR2_SIZE_RE.sub(r'\1', filename)
        if filename != size:
            return int(size)
    return 0

"""
/*
 * Copyright (c) 2005 Philip Jenvey <pjenvey@groovie.org>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the author or contributors may not be used to endorse or
 *    promote products derived from this software without specific prior
 *    written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * $Id$
 */
"""
