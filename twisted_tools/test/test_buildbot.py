from twisted.trial.unittest import TestCase
from twisted.internet import defer

from twisted_tools import buildbot



class BuildbotTests(TestCase):
    """
    Tests for L{builbot} helpers.
    """

    def setUp(self):
        super(BuildbotTests, self).setUp()
        # Captured requests during test run.
        self.requests = []


    def riggedGetMethod(
            self, url, headers, allow_redirects=False, reactor=None):
        """
        Fake treq.get method to capture GET requests in tests.
        """
        self.requests.append({
            'url': url,
            'headers': headers,
            'allow_redirects': allow_redirects,
            'reactor': reactor,
            })
        return defer.succeed(None)


    def assertBuilbotPath(self, expected_path, url):
        """
        Check that C{url} is a buildbot url for C{expected_path}.
        """
        _, path = url.split(buildbot.BASE_URL)
        self.assertEqual(expected_path, path)


    def assertBuildbotRequest(self, path, branch, reason, builder, scheduler):
        """
        Check that a buildbot request was done on C{expected_path} to trigger
        a build for C{branch}.
        """
        last_request = self.requests.pop(0)

        # A GET request is made with buildbot option encoded in the URL.
        _, request_path_with_args = last_request['url'].split(
            buildbot.BASE_URL)
        request_path, arguments = request_path_with_args.split('?', 1)
        arguments = arguments.split('&')

        self.assertEqual(path, request_path)
        self.assertItemsEqual([
            'branch=' + branch,
            'reason=' + reason,
            'selected=' + builder,
            'forcescheduler=' + scheduler,
            'username=twisted',
            'passwd=matrix',
            'submit=Force%20Build',
            'revision=',
            ],
            arguments)


    def test_forceBuildDefaultBuilder(self):
        """
        When no builder is specified it triggers all supported builders
        and returns the link for all builders.
        """
        deferred = buildbot.forceBuild(
            branch='/branches/some-branch',
            reason='testing',
            get_method=self.riggedGetMethod,
            )

        url = self.successResultOf(deferred)

        self.assertBuilbotPath(
            '/boxes-supported?branch=/branches/some-branch', url)
        self.assertBuildbotRequest(
            path='/builders/_all/forceall',
            branch='/branches/some-branch',
            reason='testing',
            scheduler='force-supported',
            builder='',
            )

    def test_forceBuildShortBranchName(self):
        """
        Branch names are expanded to SVN branch path.
        """
        deferred = buildbot.forceBuild(
            branch='some-branch',
            reason='testing',
            get_method=self.riggedGetMethod,
            )

        url = self.successResultOf(deferred)

        self.assertBuilbotPath(
            '/boxes-supported?branch=/branches/some-branch', url)


    def test_forceBuildSpecificBuilder(self):
        """
        When a builder is specified it triggers builders
        and returns the link for the specific builder and branch.
        """
        deferred = buildbot.forceBuild(
            branch='some-branch',
            reason='testing',
            builder='some-builder',
            get_method=self.riggedGetMethod,
            )

        url = self.successResultOf(deferred)

        self.assertBuilbotPath(
            '/boxes-supported?builder=some-builder&branch=/branches/some-branch',
            url)
        self.assertBuildbotRequest(
            path='/builders/_selected/forceselected',
            branch='/branches/some-branch',
            scheduler='force-supported',
            reason='testing',
            builder='some-builder',
            )


    def test_forceBuildUnsupportedBuilder(self):
        """
        When C{supported} flag is C{False} and no builder is specified it
        will trigger all unsupported builders.
        """
        deferred = buildbot.forceBuild(
            branch='name',
            reason='testing',
            supported=False,
            get_method=self.riggedGetMethod,
            )

        url = self.successResultOf(deferred)

        self.assertBuilbotPath(
            '/boxes-unsupported?branch=/branches/name',
            url)
        self.assertBuildbotRequest(
            path='/builders/_all/forceall',
            branch='/branches/name',
            reason='testing',
            builder='',
            scheduler='force-unsupported',
            )


    def test_forceBuildSpecificUnsupportedBuilder(self):
        """
        Unsupported builders need to be explicitly requested.
        """
        deferred = buildbot.forceBuild(
            branch='name',
            reason='testing',
            builder='some-builder',
            supported=False,
            get_method=self.riggedGetMethod,
            )

        url = self.successResultOf(deferred)

        self.assertBuilbotPath(
            '/boxes-unsupported?builder=some-builder&branch=/branches/name',
            url)
        self.assertBuildbotRequest(
            path='/builders/_selected/forceselected',
            branch='/branches/name',
            reason='testing',
            builder='some-builder',
            scheduler='force-unsupported',
            )
