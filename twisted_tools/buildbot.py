import os, sys
import urllib
import treq
import twisted

BASE_URL = 'http://buildbot.twistedmatrix.com'
USER_AGENT = (
    "force-builds (%(name)s; %(platform)s) Twisted/%(twisted)s "
    "Python/%(python)s" % dict(
        name=os.name, platform=sys.platform,
        twisted=twisted.__version__, python=hex(sys.hexversion)))



def _getURLForBranch(branch, builder=None, supported=True):
    """
    Get URL for build results corresponding to a branch and an optional
    builder.

    When no builder is specified it returns the link to supported builders.
    """
    if supported:
        base = 'boxes-supported?'
    else:
        base = 'boxes-unsupported?'

    if builder:
        base += 'builder=%s&' % (builder,)

    return '/%sbranch=%s' % (base, urllib.quote(branch))



def forceBuild(
        branch, reason, tests=None, reactor=None, builder=None,
        get_method=None, supported=True,
        ):
    """
    Force a build of a given branch.

    @return: URL where build results can be found.
    """
    if not branch.startswith('/branches/'):
        branch = '/branches/' + branch

    if not get_method:
        get_method = treq.get

    if not builder:
        target = '/builders/_all/forceall'
        selected_builder = ''
    else:
        target = '/builders/_selected/forceselected'
        selected_builder = builder

    if supported:
        force_scheduler = 'force-supported'
    else:
        force_scheduler = 'force-unsupported'

    args = [
        ('username', 'twisted'),
        ('passwd', 'matrix'),
        ('forcescheduler', force_scheduler),
        ('revision', ''),
        ('submit', 'Force Build'),
        ('branch', branch),
        ('reason', reason),
        ('selected', selected_builder),
        ]

    if tests is not None:
        args += [('test-case-name', tests)]

    url = BASE_URL + target
    url = url + '?' + '&'.join([k + '=' + urllib.quote(v) for (k, v) in args])
    headers = {'user-agent': [USER_AGENT]}
    # We don't actually care about the result and buildbot returns a
    # relative redirect here. Until recently (#5434) twisted didn't
    # handle them, so avoid following the redirect to support released
    # versions of twisted.
    d = get_method(url, headers, allow_redirects=False, reactor=reactor)
    d.addCallback(
        lambda _: BASE_URL + _getURLForBranch(branch, builder, supported))
    return d
