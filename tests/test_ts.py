from TwitterSearch import *

import unittest
import httpretty

class TwitterSearchTest(unittest.TestCase):

    def createTSO(self):
        """ Returns a default TwitterSearchOrder instance """
        tso = TwitterSearchOrder()
        tso.setKeywords(['foo'])
        return tso

    def createTS(self):
        """ Returns a default TwitterSearch instance """
        return TwitterSearch('aaabbb','cccddd','111222','333444', verify=False)

    def apiAnsweringMachine(self, filename):
        """ Generates faked API responses by returing content of a given file """
        for line in open(filename, 'r'):
            yield line

    def setUp(self):
        """ Constructor """
        self.auth_url = TwitterSearch._base_url + TwitterSearch._verify_url
        self.search_url = TwitterSearch._base_url + TwitterSearch._search_url
        self.lang_url = TwitterSearch._base_url + TwitterSearch._lang_url


    ################ TESTS #########################

    @httpretty.activate
    def test_TS_set_supported_languages(self):
        """ Tests TwitterSearch.setSupportedLanguages() """

        httpretty.register_uri(
                httpretty.GET, self.lang_url,
                body=self.apiAnsweringMachine('tests/mock-data/lang.log'),
                streaming=True,
                status=200,
                content_type='text/json' )

        ts = self.createTS()
        tso = self.createTSO()

        try:
            ts.setSupportedLanguages(tso)
            self.assertEqual(tso.iso_6391.sort(), [ 'fi', 'da', 'pl', 'hu', 'fa', 'he' ].sort())
        except Exception as e:
            self.assertTrue(False, "An exception was raised: %s" % e)

    @httpretty.activate
    def test_TS_authenticate(self):
        """ Tests TwitterSearch.authenticate() for valid logins """

        httpretty.register_uri(
                httpretty.GET, self.auth_url,
                body=self.apiAnsweringMachine('tests/mock-data/verify.log'),
                streaming=True,
                status=200,
                content_type='text/json' )

        ts = self.createTS()

        try:
            ts.authenticate(True)
            self.assertTrue(True)

        except TwitterSearchException as e:
            self.assertTrue(False, "An exception was raised: %s" % e)

    @httpretty.activate
    def test_TS_authenticate_fail(self):
        """ Tests TwitterSearch.authenticate() for invalid logins """

        httpretty.register_uri(
                httpretty.GET, self.auth_url,
                body=self.apiAnsweringMachine('tests/mock-data/verify-error.log'),
                streaming=True,
                status=401,
                content_type='text/json' )

        ts = self.createTS()

        try:
            ts.authenticate(True)
            self.assertTrue(False, "Exception should be raised instead")
        except TwitterSearchException as e:
            self.assertEqual(e.code, 401, "Exception code should be 401 but is %i" % e.code)

    @httpretty.activate
    def test_TS_search_tweets_iterable(self):
        """ Tests TwitterSearch.searchTweetsIterable() and .getStatistics() """

        httpretty.register_uri(httpretty.GET, self.search_url,
                        responses=[
                            httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/0.log')),
                            httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/1.log')),
                            httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/2.log')),
                            httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/3.log'))
                            ]
                        )

        cnt = 4
        pages = 4 # 4 pages with 4*4-1 tweets in total
        tso = self.createTSO()
        tso.setCount(cnt)
        ts = self.createTS()

        tweet_cnt = 0
        for tweet in ts.searchTweetsIterable(tso):
            tweet_cnt += 1

        self.assertEqual( (cnt*4-1), tweet_cnt, "Wrong amount of tweets")

        # test statistics
        stats = ts.getStatistics()
        self.assertEqual(stats['tweets'], tweet_cnt, "Tweet counter is NOT working correctly (%i should be %i)" % (stats['tweets'], tweet_cnt))
        self.assertEqual(stats['queries'], pages, "Query counter is NOT working correctly (%i should be %i)" % (stats['queries'], pages))


    @httpretty.activate
    def test_TS_empty_results(self):
        """ Tests TwitterSearch.searchTweetsIterable() with empty results """

        httpretty.register_uri(httpretty.GET, self.search_url, 
                responses=[
                    httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/empty.log')),
                ])

        tso = self.createTSO()
        ts = self.createTS()
        for tweet in ts.searchTweetsIterable(tso):
            self.assertFalse(True, "There should be no tweets to be found")


    @httpretty.activate
    def test_TS_search_tweets(self):
        """ Tests TwitterSearch.searchTweets() """

        httpretty.register_uri(httpretty.GET, self.search_url,
                responses=[
                    httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/0.log')),
                    httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/1.log')),
                    httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/2.log')),
                    httpretty.Response(streaming=True, status=200, content_type='text/json', body=self.apiAnsweringMachine('tests/mock-data/3.log'))
                    ]
                )

        cnt = 4
        tso = self.createTSO()
        tso.setCount(cnt)
        ts = self.createTS()

        todo = True
        next_max_id = 0

        max_ids = []

        while(todo):
            max_ids.append(next_max_id)
            response = ts.searchTweets(tso)
            todo = len(response['content']['statuses']) == cnt
            for tweet in response['content']['statuses']:
                tweet_id = tweet['id']
                if (tweet_id < next_max_id) or (next_max_id == 0):
                     next_max_id = tweet_id
                     next_max_id -= 1
            tso.setMaxID(next_max_id)

        self.assertEqual(max_ids, [0, 355715848851300353, 355714667852726271, 355712782454358015], "Max ids NOT equal")

