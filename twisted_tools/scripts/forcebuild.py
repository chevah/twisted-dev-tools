"""
Command line adapter for triggering Buildbot builds.
"""

import os, pwd
import webbrowser

from twisted.python import usage
from twisted.internet.defer import inlineCallbacks

from twisted_tools import buildbot, git

class Options(usage.Options):
    synopsis = "force-build [options]"

    optParameters = [
        ['branch', 'b', None,
            'Branch to build. By default it will trigger the current branch.'],
        ['builder', None, None,
            'Trigger specific builder. '
            'By default it triggers all builders (supported or unsupported). '
            'For unsupported builders you still need to explicitly pass the '
            '-u flag even when a specific builder is asked.'],
        ['tests', 't', None, 'Tests to run'],
        ['comments', None, None, 'Comment associated with the build request.'],
        ]

    optFlags = [
        ['open-browser', 'o',
            'Open default web browser at builders page.'],
        ['unsupported', 'u',
            'Launch the unsupported builders. '
            'By default it only operated with supported builders.'],
        ]


@inlineCallbacks
def main(reactor, *argv):
    config = Options()
    config.parseOptions(argv[1:])

    if config['branch'] is None:
        try:
            git.ensureGitRepository(reactor=reactor)
            config['branch'] = yield git.getCurrentSVNBranch(reactor=reactor)
        except git.NotAGitRepository:
            raise SystemExit("Must specify a branch to build or be in a git repository.")
        except git.NotASVNRevision:
            raise SystemExit("Current commit hasn't been pushed to svn.")


    reason = '%s: %s' % (pwd.getpwuid(os.getuid())[0], config['comments'])

    print 'Forcing...'
    url = yield buildbot.forceBuild(
        config['branch'],
        reason,
        config['tests'],
        reactor=reactor,
        builder=config['builder'],
        supported=not config['unsupported'],
        )
    print 'Forced.'

    if config['open-browser']:
        print 'A web browser page will be opened at\n%s' % (url,)
        webbrowser.open(url)
    else:
        print 'See %s for results' % (url,)
