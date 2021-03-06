#Written by Niels Zeilemaker
import sys
from time import time
from itertools import islice
from random import random, shuffle
from traceback import print_exc

from Tribler.dispersy.authentication import MemberAuthentication
from Tribler.dispersy.community import Community
from Tribler.dispersy.conversion import DefaultConversion
from Tribler.dispersy.destination import CandidateDestination,\
    CommunityDestination
from Tribler.dispersy.dispersydatabase import DispersyDatabase
from Tribler.dispersy.distribution import DirectDistribution,\
    FullSyncDistribution
from Tribler.dispersy.member import DummyMember, Member
from Tribler.dispersy.message import Message
from Tribler.dispersy.resolution import PublicResolution


from Tribler.community.search.conversion import SearchConversion
from Tribler.community.search.payload import SearchRequestPayload,\
    SearchResponsePayload, TorrentRequestPayload, TorrentCollectRequestPayload,\
    TorrentCollectResponsePayload, TasteIntroPayload
from Tribler.community.channel.community import ChannelCommunity
from Tribler.community.channel.preview import PreviewChannelCommunity
from Tribler.community.channel.payload import TorrentPayload
from Tribler.dispersy.bloomfilter import BloomFilter
from Tribler.dispersy.requestcache import Cache
from Tribler.dispersy.candidate import CANDIDATE_WALK_LIFETIME,\
    WalkCandidate, BootstrapCandidate
from Tribler.dispersy.dispersy import IntroductionRequestCache
from Tribler.Core.RemoteTorrentHandler import RemoteTorrentHandler
from Tribler.Core.TorrentDef import TorrentDef
from os import path
from Tribler.Core.CacheDB.sqlitecachedb import bin2str

if __debug__:
    from Tribler.dispersy.dprint import dprint
    from lencoder import log

DEBUG = True
SWIFT_INFOHASHES = 0

class SearchCommunity(Community):
    """
    A single community that all Tribler members join and use to disseminate .torrent files.
    """
    @classmethod
    def get_master_members(cls):
#generated: Mon May  7 17:43:59 2012
#curve: high <<< NID_sect571r1 >>>
#len: 571 bits ~ 144 bytes signature
#pub: 170 3081a7301006072a8648ce3d020106052b81040027038192000405c09348b2243e53fa190f17fc8c9843d61fc67e8ea22d7b031913ffc912897b57be780c06213dbf937d87e3ef1d48bf8f76e03d5ec40b1cdb877d9fa1ec1f133a412601c262d9ef01840ffc49d6131b1df9e1eac41a8ff6a1730d4541a64e733ed7cee415b220e4a0d2e8ace5099520bf8896e09cac3800a62974f5574910d75166d6529dbaf016e78090afbfaf8373
#pub-sha1 2782dc9253cef6cc9272ee8ed675c63743c4eb3a
#-----BEGIN PUBLIC KEY-----
#MIGnMBAGByqGSM49AgEGBSuBBAAnA4GSAAQFwJNIsiQ+U/oZDxf8jJhD1h/Gfo6i
#LXsDGRP/yRKJe1e+eAwGIT2/k32H4+8dSL+PduA9XsQLHNuHfZ+h7B8TOkEmAcJi
#2e8BhA/8SdYTGx354erEGo/2oXMNRUGmTnM+187kFbIg5KDS6KzlCZUgv4iW4Jys
#OACmKXT1V0kQ11Fm1lKduvAW54CQr7+vg3M=
#-----END PUBLIC KEY-----
#       master_key = "3081a7301006072a8648ce3d020106052b81040027038192000405c09348b2243e53fa190f17fc8c9843d61fc67e8ea22d7b031913ffc912897b57be780c06213dbf937d87e3ef1d48bf8f76e03d5ec40b1cdb877d9fa1ec1f133a412601c262d9ef01840ffc49d6131b1df9e1eac41a8ff6a1730d4541a64e733ed7cee415b220e4a0d2e8ace5099520bf8896e09cac3800a62974f5574910d75166d6529dbaf016e78090afbfaf8373".decode("HEX")
       master_key = "3081a7301006072a8648ce3d020106052b81040027038192000407a7857439f8a9b29adb351a8cf90e4e79fcf0272c56c23211d0f626621baf3a81346261a8c7d6b1ea3b2a2112eef4fa7e3196bea668577eb2560295b67a67670bc324a2bb7b84a104de819ef872f67dfa6f8cc7ef47ab58a30793df986f7213d4e60e17ec85ab4ec5be6f53bb004f672c5d74d7eb5382e758898382459f636c8a87b39d3448f7d36c1ab21daf185c90".decode("HEX")
       master = Member(master_key)
       return [master]

    @classmethod
    def load_community(cls, master, my_member, integrate_with_tribler = True):
        dispersy_database = DispersyDatabase.get_instance()
        try:
            dispersy_database.execute(u"SELECT 1 FROM community WHERE master = ?", (master.database_id,)).next()
        except StopIteration:
            return cls.join_community(master, my_member, my_member, integrate_with_tribler = integrate_with_tribler)
        else:
            return super(SearchCommunity, cls).load_community(master, integrate_with_tribler = integrate_with_tribler)

    def __init__(self, master, integrate_with_tribler = True):
        super(SearchCommunity, self).__init__(master)
        
        self.integrate_with_tribler = integrate_with_tribler
        self.taste_buddies = []
        
        if self.integrate_with_tribler:
            from Tribler.Core.CacheDB.SqliteCacheDBHandler import ChannelCastDBHandler, TorrentDBHandler, MyPreferenceDBHandler
            from Tribler.Core.CacheDB.Notifier import Notifier 
        
            # tribler channelcast database
            self._channelcast_db = ChannelCastDBHandler.getInstance()
            self._torrent_db = TorrentDBHandler.getInstance()
            self._mypref_db = MyPreferenceDBHandler.getInstance()
            self._notifier = Notifier.getInstance()
            
            # torrent collecting
            self._rtorrent_handler = RemoteTorrentHandler.getInstance()
        else:
            self._channelcast_db = ChannelCastDBStub(self._dispersy)
            self._torrent_db = None
            self._mypref_db = None
            self._notifier = None
            
        self.taste_bloom_filter = None
        self.taste_bloom_filter_key = None
        
        self.dispersy.callback.register(self.create_torrent_collect_requests, delay = CANDIDATE_WALK_LIFETIME)

    def initiate_meta_messages(self):
        return [Message(self, u"search-request", MemberAuthentication(encoding="sha1"), PublicResolution(), DirectDistribution(), CandidateDestination(), SearchRequestPayload(), self.check_search, self.on_search),
                Message(self, u"search-response", MemberAuthentication(encoding="sha1"), PublicResolution(), DirectDistribution(), CandidateDestination(), SearchResponsePayload(), self.check_search_response, self.on_search_response),
                Message(self, u"torrent-request", MemberAuthentication(encoding="sha1"), PublicResolution(), DirectDistribution(), CandidateDestination(), TorrentRequestPayload(), self.check_torrent_request, self.on_torrent_request),
                Message(self, u"torrent-collect-request", MemberAuthentication(encoding="sha1"), PublicResolution(), DirectDistribution(), CandidateDestination(), TorrentCollectRequestPayload(), self.check_torrent_collect_request, self.on_torrent_collect_request),
                Message(self, u"torrent-collect-response", MemberAuthentication(encoding="sha1"), PublicResolution(), DirectDistribution(), CandidateDestination(), TorrentCollectResponsePayload(), self.check_torrent_collect_response, self.on_torrent_collect_response),
                Message(self, u"torrent", MemberAuthentication(encoding="sha1"), PublicResolution(), FullSyncDistribution(enable_sequence_number=False, synchronization_direction=u"ASC", priority=128), CommunityDestination(node_count=0), TorrentPayload(), self.check_torrent, self.on_torrent)
                ]
        
    def _initialize_meta_messages(self):
        Community._initialize_meta_messages(self)

        ori = self._meta_messages[u"dispersy-introduction-request"]
        self._disp_intro_handler = ori.handle_callback
        
        new = Message(self, ori.name, ori.authentication, ori.resolution, ori.distribution, ori.destination, TasteIntroPayload(), ori.check_callback, self.on_taste_intro)
        self._meta_messages[u"dispersy-introduction-request"] = new
        
    def initiate_conversions(self):
        return [DefaultConversion(self), SearchConversion(self)]

    @property
    def dispersy_auto_download_master_member(self):
        # there is no dispersy-identity for the master member, so don't try to download
        return False
    
    def dispersy_claim_sync_bloom_filter(self, identifier):
        # disable sync bloom filter
        return None
    
    def add_taste_buddies(self, new_taste_buddies):
        for new_tb_tuple in new_taste_buddies[:]:
            for tb_tuple in self.taste_buddies:
                if tb_tuple[-1].sock_addr == new_tb_tuple[-1].sock_addr:
                    
                    #update similarity
                    tb_tuple[0] = max(new_tb_tuple[0], tb_tuple[0])
                    new_taste_buddies.remove(new_tb_tuple)
                    break
            else:
                self.taste_buddies.append(new_tb_tuple)
                    
        self.taste_buddies.sort(reverse = True)
        self.taste_buddies = self.taste_buddies[:10]
        
        #Send ping to all new candidates
        if len(new_taste_buddies) > 0:
            self._create_torrent_collect_requests([tb_tuple[-1] for tb_tuple in new_taste_buddies])
            
    def get_nr_connections(self):
        return len(self.get_connections())
    
    def get_connections(self):
        #add 10 taste buddies and 20 - len(taste_buddies) to candidates
        candidates = set(candidate for _,_,candidate in self.taste_buddies)
        sock_addresses = set(candidate.sock_addr for _,_,candidate in self.taste_buddies)
        
        for candidate in self._dispersy.yield_candidates(self):
            if len(candidates) == 20:
                break
            
            if candidate.sock_addr not in sock_addresses:
                candidates.add(candidate)
                sock_addresses.add(candidate.sock_addr)
        return candidates
    
    def create_introduction_request(self, destination):
        assert isinstance(destination, WalkCandidate), [type(destination), destination]
        
        if DEBUG:
            print >> sys.stderr, "SearchCommunity: sending introduction request to",destination

        self._dispersy._statistics.increment_walk_attempt()
        destination.walk(self, time())

        # temporary cache object
        identifier = self._dispersy.request_cache.claim(IntroductionRequestCache(self, destination))
        advice = True

        taste_bloom_filter = None

        num_preferences = 0
        if not isinstance(destination, BootstrapCandidate):
            myPreferences = self._mypref_db.getMyPrefListInfohash(limit = 500)
            myPreferences.sort()
            num_preferences = len(myPreferences)
            
            myPref_key = ",".join(map(bin2str, myPreferences))
            if myPref_key != self.taste_bloom_filter_key:
                if num_preferences > 0:
                    #no prefix changing, we want false positives (make sure it is a single char)
                    self.taste_bloom_filter = BloomFilter(0.005, len(myPreferences), prefix=' ')
                    self.taste_bloom_filter.add_keys(myPreferences)
                else:
                    self.taste_bloom_filter = None
                
                self.taste_bloom_filter_key = myPref_key

            taste_bloom_filter = self.taste_bloom_filter
        
        meta_request = self.get_meta_message(u"dispersy-introduction-request")
        request = meta_request.impl(authentication=(self.my_member,),
                                    distribution=(self.global_time,),
                                    destination=(destination,),
                                    payload=(destination.get_destination_address(self._dispersy._wan_address), self._dispersy._lan_address, self._dispersy._wan_address, advice, self._dispersy._connection_type, None, identifier, num_preferences, taste_bloom_filter))
        
        self._dispersy.store_update_forward([request], False, False, True)
        return request
    
    def on_taste_intro(self, messages):
        self._disp_intro_handler(messages)
        
        messages = [message for message in messages if not isinstance(self._dispersy.get_candidate(message.candidate.sock_addr), BootstrapCandidate)]
        if any(message.payload.taste_bloom_filter for message in messages):
            myPreferences = self._mypref_db.getMyPrefListInfohash(limit = 500)
        else:
            myPreferences = []
        
        newTasteBuddies = []
        if len(myPreferences) > 0:
            myRoot = 1.0/(len(myPreferences) ** .5)
            
            for message in messages:
                taste_bloom_filter = message.payload.taste_bloom_filter
                num_preferences = message.payload.num_preferences
                
                if taste_bloom_filter:    
                    overlap = sum(infohash in taste_bloom_filter for infohash in myPreferences)
                    sim = overlap * (myRoot * (1.0/(num_preferences ** .5)))
                
                    newTasteBuddies.append([sim, time(), message.candidate])
        else:
            for message in messages:
                newTasteBuddies.append([0, time(), message.candidate])
        
        if len(newTasteBuddies) > 0:
            self.add_taste_buddies(newTasteBuddies)
            
        if self._notifier:
            from Tribler.Core.simpledefs import NTFY_ACT_MEET, NTFY_ACTIVITIES, NTFY_INSERT
            for message in messages:
                self._notifier.notify(NTFY_ACTIVITIES, NTFY_INSERT, NTFY_ACT_MEET, "%s:%d"%message.candidate.sock_addr)
        
    class SearchRequest(Cache):
        timeout_delay = 30.0
        cleanup_delay = 0.0

        def __init__(self, keywords, callback):
            self.keywords = keywords
            self.callback = callback

        def on_timeout(self):
            pass
    
    def create_search(self, keywords, callback):
        #register callback/fetch identifier
        identifier = self._dispersy.request_cache.claim(SearchCommunity.SearchRequest(keywords, callback))
        
        candidates = self.get_connections()
        if len(candidates) > 0:
            if DEBUG:
                print >> sys.stderr, "SearchCommunity: sending search request for",keywords,"to",map(str, candidates)
            
            #create channelcast request message
            meta = self.get_meta_message(u"search-request")
            message = meta.impl(authentication=(self._my_member,),
                                distribution=(self.global_time,), payload=(identifier, keywords))
            
            if __debug__:
                self._dispersy.statistics.outgoing(u"search-request", len(message.packet))
            self._dispersy.endpoint.send(candidates, [message.packet])
        
        return len(candidates)
    
    def check_search(self, messages):
        return messages

    def on_search(self, messages):
        for message in messages:
            keywords = message.payload.keywords
            
            if DEBUG:
                print >> sys.stderr, "SearchCommunity: got search request for",keywords
            
            results = []
            dbresults = self._torrent_db.searchNames(keywords, local = False)
            if len(dbresults) > 0:
                for dbresult in dbresults:
                    results.append((dbresult['infohash'], dbresult['name'], dbresult['length'], dbresult['num_files'], dbresult['category'], dbresult['creation_date'], dbresult['num_seeders'], dbresult['num_leechers'], dbresult['swift_hash'], dbresult['swift_torrent_hash'], dbresult['channel_cid']))
                
                self._create_search_response(message.payload.identifier, results, message.candidate)
                
            elif DEBUG:
                self._create_search_response(message.payload.identifier, results, message.candidate)
                print >> sys.stderr, "SearchCommunity: no results"
    
    def _create_search_response(self, identifier, results, candidate):
        #create search-response message
        meta = self.get_meta_message(u"search-response")
        message = meta.impl(authentication=(self._my_member,),
                            distribution=(self.global_time,), payload=(identifier, results))
        if __debug__:
            self._dispersy.statistics.outgoing(u"search-response", len(message.packet))
        self._dispersy.endpoint.send([candidate], [message.packet])
        
        if DEBUG:
            print >> sys.stderr, "SearchCommunity: returning",len(results),"results to",candidate
    
    def check_search_response(self, messages):
        return messages
    
    def on_search_response(self, messages):
        for message in messages:
            #fetch callback using identifier
            search_request = self._dispersy.request_cache.get(message.payload.identifier, SearchCommunity.SearchRequest)
            if search_request:
                if DEBUG:
                    print >> sys.stderr, "SearchCommunity: got search response for",search_request.keywords, len(message.payload.results), message.candidate
                
                if len(message.payload.results)> 0:
                    self._torrent_db.on_search_response(message.payload.results)
                    
                    #see if we need to join some channels
                    channels = set([result[10] for result in message.payload.results if result[10]])
                    if channels:
                        channels = self._get_unknown_channels(channels)
                    
                        if DEBUG:
                            print >> sys.stderr, "SearchCommunity: joining %d preview communities"%len(channels)
                        
                        for cid in channels:
                            community = self._get_channel_community(cid)
                            community.disp_create_missing_channel(message.candidate, includeSnapshot = False)
                
                search_request.callback(search_request.keywords, message.payload.results, message.candidate)
            else:
                if DEBUG:
                    print >> sys.stderr, "SearchCommunity: got search response identifier not found", message.payload.identifier
    
    def create_torrent_request(self, torrents, candidate):
        torrentdict = {}
        for torrent in torrents:
            if isinstance(torrent, list):
                cid, infohash = torrent
            else:
                cid = self._master_member.mid
                infohash = torrent
            torrentdict.setdefault(cid, set()).add(infohash)
        
        #create torrent-request message
        meta = self.get_meta_message(u"torrent-request")
        message = meta.impl(authentication=(self._my_member,),
                            distribution=(self.global_time,), payload=(torrentdict,))
        if __debug__:
            self._dispersy.statistics.outgoing(u"torrent-request", len(message.packet))
        self._dispersy.endpoint.send([candidate], [message.packet])
        
        if DEBUG:
            nr_requests = sum([len(cid_torrents) for cid_torrents in torrentdict.values()])
            print >> sys.stderr, "SearchCommunity: requesting",nr_requests,"TorrentMessages from",candidate
    
    def check_torrent_request(self, messages):
        return messages
    
    def on_torrent_request(self, messages):
        for message in messages:
            requested_packets = []
            for cid, torrents in message.payload.torrents.iteritems():
                reqmessages = self._get_messages_from_infohashes(cid, torrents)
                for reqmessage in reqmessages:
                    requested_packets.append(reqmessage.packet)

            if requested_packets:
                if __debug__:
                    self._dispersy.statistics.outgoing(u"torrent-response", sum([len(packet) for packet in requested_packets]))
                self._dispersy.endpoint.send([message.candidate], requested_packets)
            
            if DEBUG:
                print >> sys.stderr, "SearchCommunity: got request for ",len(requested_packets),"torrents from",message.candidate
    
    class PingRequestCache(IntroductionRequestCache):
        def __init__(self, community, candidate):
            self.candidate = candidate
            IntroductionRequestCache.__init__(self, community, None)
        
        def on_timeout(self):
            refreshIf = time() - CANDIDATE_WALK_LIFETIME
            remove = None
            for taste_buddy in self.community.taste_buddies:
                if taste_buddy[2] == self.candidate:
                    if taste_buddy[1] < refreshIf:
                        remove = taste_buddy
                    break
            
            if remove:
                if DEBUG:
                    print >> sys.stderr, "SearchCommunity: no response on ping, removing from taste_buddies",self.candidate
                self.community.taste_buddies.remove(remove)
    
    def create_torrent_collect_requests(self):
        while True:
            refreshIf = time() - CANDIDATE_WALK_LIFETIME
            try:
                #determine to which peers we need to send a ping
                candidates = [candidate for _,prev,candidate in self.taste_buddies if prev < refreshIf]
                self._create_torrent_collect_requests(candidates)
            except:
                print_exc()
                
            yield 5.0
    
    def _create_torrent_collect_requests(self, candidates):
        if len(candidates) > 0:
            self._create_pingpong(u"torrent-collect-request", candidates)
    
    def check_torrent_collect_request(self, messages):
        if __debug__: dprint(len(messages))
        return messages
    
    def on_torrent_collect_request(self, messages):
        if __debug__: dprint(len(messages))
        candidates = [message.candidate for message in messages]
        identifiers = [message.payload.identifier for message in messages]
        
        self._create_pingpong(u"torrent-collect-response", candidates, identifiers)
        self.on_torrent_collect_response(messages, verifyRequest = False)
    
    def check_torrent_collect_response(self, messages):
        if __debug__: dprint(len(messages))
        return messages
    
    def on_torrent_collect_response(self, messages, verifyRequest = True):
        if __debug__: dprint(len(messages))
        toInsert = {}
        toCollect = {}
        toPopularity = {}
        for message in messages:
            if verifyRequest:
                pong_request = self._dispersy.request_cache.pop(message.payload.identifier, SearchCommunity.PingRequestCache)
                if __debug__: dprint("pop", pong_request.helper_candidate)
            else:
                if __debug__: dprint("no-pop")
                pong_request = True
                
            if pong_request and message.payload.hashtype == SWIFT_INFOHASHES:
                for roothash, infohash, seeders, leechers, ago in message.payload.torrents:
                    toInsert[infohash] = [infohash, roothash]
                    toPopularity[infohash] = [seeders, leechers, time() - (ago * 60)]
                    toCollect.setdefault(infohash, []).append(message.candidate)

        self._torrent_db.on_torrent_collect_response(toInsert.values())
        
        hashesToCollect = self._torrent_db.selectSwiftTorrentsToCollect(toCollect.keys())
        for infohash, roothash in hashesToCollect[:5]:
            for candidate in toCollect[infohash]:
                if DEBUG:
                    from Tribler.Core.CacheDB.sqlitecachedb import bin2str
                    print >> sys.stderr, "SearchCommunity: requesting .torrent after receiving ping/pong ", candidate, bin2str(infohash), bin2str(roothash)

                self._rtorrent_handler.download_torrent(candidate, infohash, roothash, prio = 2)
    
    def _create_pingpong(self, meta_name, candidates, identifiers = None):
        max_len = self.dispersy_sync_bloom_filter_bits/8
        limit = int(max_len/44)
        
        #we want roughly 1/3 random, 2/3 recent
        limitRecent = int(limit * 0.66)
        limitRandom = limit - limitRecent
        
        torrents = self._torrent_db.getRecentlyCollectedSwiftHashes(limit = limitRecent) or []
        if len(torrents) == limitRecent:
            leastRecent = torrents[-1][5]
            randomTorrents = self._torrent_db.getRandomlyCollectedSwiftHashes(leastRecent, limit = limitRandom) or []
        else:
            randomTorrents = []
            
        #combine random and recent + shuffle to obscure categories
        torrents = [tor[:5] for tor in torrents] + randomTorrents
        shuffle(torrents)
        
        #fix leechers, seeders to max 2**16 (shift values +2 to accomodate -2 and -1 values)
        for torrent in torrents:
            torrent[2] = min((2 ** 16) - 1, (torrent[2] or -1) + 2)
            torrent[3] = min((2 ** 16) - 1, (torrent[3] or -1) + 2)
            
            #convert to minutes
            torrent[4] /= 60
            if torrent[4] > ((2 ** 16) - 1):
                torrent[4] = 0
            
        
        for index, candidate in enumerate(candidates):
            if identifiers:
                identifier = identifiers[index]
            else:
                identifier = self._dispersy.request_cache.claim(SearchCommunity.PingRequestCache(self, candidate))
    
            #create torrent-collect-request/response message
            meta = self.get_meta_message(meta_name)
            message = meta.impl(authentication=(self._my_member,),
                                distribution=(self.global_time,), payload=(identifier, SWIFT_INFOHASHES, torrents))
            if __debug__:
                self._dispersy.statistics.outgoing(meta_name, len(message.packet))
            self._dispersy.endpoint.send([candidate], [message.packet])
    
            if DEBUG:
                print >> sys.stderr, "SearchCommunity: send",meta_name,"to", candidate
        
        addresses = [candidate.sock_addr for candidate in candidates]
        for taste_buddy in self.taste_buddies:
            if taste_buddy[2].sock_addr in addresses:
                taste_buddy[1] = time()
    
    def create_torrent(self, filename, store=True, update=True, forward=True):
        if path.exists(filename):
            try:
                torrentdef = TorrentDef.load(filename)
                files = torrentdef.get_files_as_unicode_with_length()
                
                return self._disp_create_torrent(torrentdef.get_infohash(), long(time()), torrentdef.get_name_as_unicode(), tuple(files), torrentdef.get_trackers_as_single_tuple(), store, update, forward)
            except:
                print_exc()
        return False

    def _disp_create_torrent(self, infohash, timestamp, name, files, trackers, store=True, update=True, forward=True):
        meta = self.get_meta_message(u"torrent")
        message = meta.impl(authentication=(self._my_member,),
                            distribution=(self.claim_global_time(),),
                            payload=(infohash, timestamp, name, files, trackers))
        
        self._dispersy.store_update_forward([message], store, update, forward)
        self._torrent_db.updateTorrent(infohash, notify = False, dispersy_id = message.packet_id)
        return message        
    
    def check_torrent(self, messages):
        return messages
    
    def on_torrent(self, messages):
        for message in messages:
            self._torrent_db.addExternalTorrentNoDef(message.payload.infohash, message.payload.name, message.payload.files, message.payload.trackers, message.payload.timestamp, "DISP_SC", {'dispersy_id':message.packet_id})
    
    def _get_channel_id(self, cid):
        assert isinstance(cid, str)
        assert len(cid) == 20
        
        return self._channelcast_db._db.fetchone(u"SELECT id FROM Channels WHERE dispersy_cid = ?", (buffer(cid),))
    
    def _get_unknown_channels(self, cids):
        assert all(isinstance(cid, str) for cid in cids)
        assert all(len(cid) == 20 for cid in cids)

        parameters = u",".join(["?"] * len(cids))
        known_cids = self._channelcast_db._db.fetchall(u"SELECT dispersy_cid FROM Channels WHERE dispersy_cid in ("+parameters+")", map(buffer, cids))
        known_cids = map(str, known_cids)
        return [cid for cid in cids if cid not in known_cids]
        
    def _get_channel_community(self, cid):
        assert isinstance(cid, str)
        assert len(cid) == 20
        
        try:
            return self._dispersy.get_community(cid, True)
        except KeyError:
            if __debug__: dprint("join preview community ", cid.encode("HEX"))
            return PreviewChannelCommunity.join_community(DummyMember(cid), self._my_member, self.integrate_with_tribler) 

    def _get_messages_from_infohashes(self, cid, infohashes):
        messages = []
        
        def add_message(dispersy_id):
            if dispersy_id and dispersy_id > 0:
                try:
                    message = self._get_message_from_dispersy_id(dispersy_id, "torrent")
                    if message:
                        messages.append(message)
                    
                except RuntimeError:
                    pass
        
        if cid == self._master_member.mid:
            channel_id = None
        else:
            channel_id = self._get_channel_id(cid)
        
        for infohash in infohashes:
            dispersy_id = None
            
            #1. try to find the torrentmessage for this cid, infohash combination
            if channel_id:
                dispersy_id = self._channelcast_db.getTorrentFromChannelId(channel_id, infohash, ['ChannelTorrents.dispersy_id'])
            else:
                torrent = self._torrent_db.getTorrent(infohash, ['dispersy_id', 'torrent_file_name'], include_mypref = False)
                if torrent:
                    dispersy_id = torrent['dispersy_id'] 

                    #2. if still not found, create a new torrentmessage and return this one
                    if not dispersy_id and torrent['torrent_file_name'] and path.isfile(torrent['torrent_file_name']):
                        message = self.create_torrent(torrent['torrent_file_name'], store = True, update = False, forward = False)
                        if message:
                            messages.append(message)
            
            add_message(dispersy_id)
        return messages

    def _get_message_from_dispersy_id(self, dispersy_id, messagename):
        # 1. get the packet
        try:
            packet, packet_id = self._dispersy.database.execute(u"SELECT sync.packet, sync.id FROM community JOIN sync ON sync.community = community.id WHERE sync.id = ?", (dispersy_id,)).next()
        except StopIteration:
            raise RuntimeError("Unknown dispersy_id")

        # 2. convert packet into a Message instance
        message = self._dispersy.convert_packet_to_message(str(packet))        
        if message:
            message.packet_id = packet_id
        else:
            raise RuntimeError("Unable to convert packet")
        
        if message.name == messagename:
            return message
        
        raise RuntimeError("Message is of an incorrect type, expecting a '%s' message got a '%s'"%(messagename, message.name))

class ChannelCastDBStub():
    def __init__(self, dispersy):
        self._dispersy = dispersy

        self.cachedTorrents = None
    
    def convert_to_messages(self, results):
        messages = self._dispersy.convert_packets_to_messages(str(packet) for packet, _ in results)
        for packet_id, message in zip((packet_id for _, packet_id in results), messages):
            if message:
                message.packet_id = packet_id
                yield message.community.cid, message

    def newTorrent(self, message):
        self._cachedTorrents[message.payload.infohash] = message

    def hasTorrents(self, channel_id, infohashes):
        returnAr = []
        for infohash in infohashes:
            if infohash in self._cachedTorrents:
                returnAr.append(True)
            else:
                returnAr.append(False)
        return returnAr
    
    def getTorrentFromChannelId(self, channel_id, infohash, keys):
        if infohash in self._cachedTorrents:
            return self._cachedTorrents[infohash].packet_id
        
    def on_dynamic_settings(self, channel_id):
        pass
    
    @property
    def _cachedTorrents(self):
        if self.cachedTorrents is None:
            self.cachedTorrents = {}
            self._cacheTorrents()
        
        return self.cachedTorrents
    
    def _cacheTorrents(self):
        sql = u"SELECT sync.packet, sync.id FROM sync JOIN meta_message ON sync.meta_message = meta_message.id JOIN community ON community.id = sync.community WHERE meta_message.name = 'torrent'"
        results = list(self._dispersy.database.execute(sql))
        messages = self.convert_to_messages(results)
        
        for _, message in messages:
            self._cachedTorrents[message.payload.infohash] = message
