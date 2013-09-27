###
# OTCOrderBook - supybot plugin to keep an order book from irc
# Copyright (C) 2010, Daniel Folkinshteyn <nanotube@users.sourceforge.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot import conf
from supybot import ircdb
from supybot import world
from supybot import ircmsgs

import sqlite3
import time
import os.path

class RatingSystemDB(object):
    def __init__(self, filename):
        self.filename = filename
        self.db = None

    def _commit(self):
        '''a commit wrapper to give it another few tries if it errors.
        
        which sometimes happens due to:
        OperationalError: database is locked'''
        for i in xrange(10):
            try:
                self.db.commit()
            except:
                time.sleep(1)

    def open(self):
        if os.path.exists(self.filename):
            db = sqlite3.connect(self.filename, check_same_thread = False)
            db.text_factory = str
            self.db = db
            return
        
        db = sqlite3.connect(self.filename, check_same_thread = False)
        db.text_factory = str
        self.db = db
        cursor = self.db.cursor()
        cursor.execute("""CREATE TABLE users (
                          id INTEGER PRIMARY KEY,
                          total_rating INTEGER,
                          created_at INTEGER,
                          pos_rating_recv_count INTEGER,
                          neg_rating_recv_count INTEGER,
                          pos_rating_sent_count INTEGER,
                          neg_rating_sent_count INTEGER,
                          nick TEXT UNIQUE ON CONFLICT REPLACE,
                          host TEXT)
                           """)
        cursor.execute("""CREATE TABLE ratings (
                          id INTEGER PRIMARY KEY,
                          rated_user_id INTEGER,
                          rater_user_id INTEGER,
                          created_at INTEGER,
                          rating INTEGER,
                          notes TEXT)
                          """)
        self._commit()
        return

    def close(self):
        self.db.close()

    def get(self, nick):
        cursor = self.db.cursor()
        nick = nick.replace('|','||').replace('_','|_').replace('%','|%')
        cursor.execute("""SELECT * FROM users WHERE nick LIKE ? ESCAPE '|'""", (nick,))
        return cursor.fetchall()

    def getReceivedRatings(self, nick, sign=None):
        # sign can be "> 0" or "< 0", None means all
        cursor = self.db.cursor()
        nick = nick.replace('|','||').replace('_','|_').replace('%','|%')
        if sign is None:
            cursor.execute("""SELECT * FROM users, ratings WHERE users.nick LIKE ? ESCAPE '|'
                              AND ratings.rated_user_id = users.id""",
                           (nick,))
        else:
            cursor.execute("""SELECT * FROM users, ratings WHERE users.nick LIKE ? ESCAPE '|'
                              AND ratings.rated_user_id = users.id AND
                              ratings.rating %s""" % sign,
                           (nick,))
        return cursor.fetchall()

    def getSentRatings(self, nick, sign=None):
        # sign can be "> 0" or "< 0", None means all
        cursor = self.db.cursor()
        nick = nick.replace('|','||').replace('_','|_').replace('%','|%')
        if sign is None:
            cursor.execute("""SELECT * FROM users, ratings WHERE users.nick LIKE ? ESCAPE '|'
                              AND ratings.rater_user_id = users.id""",
                           (nick,))
        else:
            cursor.execute("""SELECT * FROM users, ratings WHERE users.nick LIKE ? ESCAPE '|'
                              AND ratings.rater_user_id = users.id AND
                              ratings.rating %s""" % sign,
                           (nick,))
        return cursor.fetchall()

    def getLevel2Ratings(self, sourcenick, destnick):
        cursor = self.db.cursor()
        sourcenick = sourcenick.replace('|','||').replace('_','|_').replace('%','|%')
        destnick = destnick.replace('|','||').replace('_','|_').replace('%','|%')
        cursor.execute("""SELECT ratings1.rating, ratings2.rating
                    FROM users as users1, users as users2, ratings as ratings1, ratings as ratings2 WHERE
                    users1.nick LIKE ? ESCAPE '|' AND
                    ratings1.rater_user_id = users1.id AND
                    users2.nick LIKE ? ESCAPE '|' AND
                    ratings2.rated_user_id = users2.id AND
                    ratings2.rater_user_id = ratings1.rated_user_id""", (sourcenick,destnick,))
        l2ratings = cursor.fetchall()
        if len(l2ratings) == 0:
            return (0,0,)
        trustlinks = []
        for row in l2ratings:
            if row[0] > 0 and row[1] > 0:
                trustlinks.append(min(row))
            elif row[0] > 0 and row[1] < 0:
                trustlinks.append(-min(row[0],abs(row[1])))
            elif row[0] < 0:
                trustlinks.append(0)
        return (sum(trustlinks), len(trustlinks),)

    def getExistingRating(self, sourceid, targetid):
        cursor = self.db.cursor()
        cursor.execute("""SELECT * from ratings WHERE
                          rater_user_id = ? AND
                          rated_user_id = ?""",
                       (sourceid, targetid))
        return cursor.fetchall()

    def getRatingDetail(self, sourcenick, targetnick):
        cursor = self.db.cursor()
        sourcenick = sourcenick.replace('|','||').replace('_','|_').replace('%','|%')
        targetnick = targetnick.replace('|','||').replace('_','|_').replace('%','|%')
        cursor.execute("""SELECT ratings.created_at, ratings.rating, ratings.notes
                          FROM ratings, users, users as users2 WHERE
                          users.nick LIKE ? ESCAPE '|' AND
                          users2.nick LIKE ? ESCAPE '|' AND
                          ratings.rater_user_id = users.id AND
                          ratings.rated_user_id = users2.id""",
                       (sourcenick, targetnick))
        return cursor.fetchall()

    def getConnections(self, nick):
        cursor = self.db.cursor()
        nick = nick.replace('|','||').replace('_','|_').replace('%','|%')
        cursor.execute("""SELECT * FROM users, ratings
                          WHERE users.nick LIKE ? ESCAPE '|' AND
                          (ratings.rater_user_id = users.id OR
                          ratings.rated_user_id = users.id)""",
                       (nick,))
        return cursor.fetchall()

    def update_counts(self, sourcenick, sourceid, targetnick, targetid):
        """update rating counts here.
        called after every rate/unrate, to generate totals/counts.

        we need to update target's totalrating, and recv counts,
        and source's sent counts"""
        cursor = self.db.cursor()
        cursor.execute("""SELECT sum(rating) FROM ratings WHERE
                          rated_user_id = ?""",
                       (targetid,))
        target_total = cursor.fetchall()[0][0]
        target_pos_count = len(self.getReceivedRatings(targetnick, sign="> 0"))
        target_neg_count = len(self.getReceivedRatings(targetnick, sign="< 0"))

        source_pos_count = len(self.getSentRatings(sourcenick, sign="> 0"))
        source_neg_count = len(self.getSentRatings(sourcenick, sign="< 0"))

        cursor.execute("""UPDATE users SET total_rating = ?,
                          pos_rating_recv_count = ?,
                          neg_rating_recv_count = ? WHERE
                          id = ?""",
                       (target_total, target_pos_count, target_neg_count,
                        targetid))
        cursor.execute("""UPDATE users SET pos_rating_sent_count = ?,
                          neg_rating_sent_count = ? WHERE
                          id = ?""",
                       (source_pos_count, source_neg_count, sourceid))
        self._commit()

    def rate(self, sourcenick, sourceid, targetnick, targetid,
             rating, replacementflag, notes, targethost=None):
        """targetid is none if target user is new
        oldtotal is none if target user is new
        replacementflag is true if this user is updating a preexisting rating of his
        """
        targetnick_escaped = targetnick.replace('|','||').replace('_','|_').replace('%','|%')
        cursor = self.db.cursor()
        timestamp = time.time()
        if targetid is None:
            cursor.execute("""INSERT INTO users VALUES
                              (NULL, ?, ?, ?, ?, ?, ?, ?, ?)""",
                           (rating, timestamp, 0, 0, 0, 0, targetnick, targethost))
            self._commit()
            cursor.execute("""SELECT id FROM users
                              WHERE nick LIKE ? ESCAPE '|'""", (targetnick_escaped,))
            targetid = cursor.fetchall()[0][0]
        if not replacementflag:
            cursor.execute("""INSERT INTO ratings VALUES
                              (NULL, ?, ?, ?, ?, ?)""",
                           (targetid, sourceid, timestamp, rating, notes))
        else:
            cursor.execute("""UPDATE ratings SET rating = ?, notes = ?, created_at = ?
                              WHERE rated_user_id = ? AND
                              rater_user_id = ?""",
                           (rating, notes, timestamp, targetid, sourceid))
        self._commit()
        self.update_counts(sourcenick, sourceid, targetnick, targetid)

    def unrate(self, sourcenick, sourceid, targetnick, targetid):
        targetnick_escaped = targetnick.replace('|','||').replace('_','|_').replace('%','|%')
        cursor = self.db.cursor()
        cursor.execute("""DELETE FROM ratings
                          WHERE rated_user_id = ? AND
                          rater_user_id = ?""",
                       (targetid, sourceid))
        self._commit()
        connections = self.getConnections(targetnick)
        if len(connections) == 0:
            cursor.execute("""DELETE FROM users
                              WHERE nick LIKE ? ESCAPE '|'""", (targetnick_escaped,))
            self._commit()
        self.update_counts(sourcenick, sourceid, targetnick, targetid)

    def deleteuser(self, userid):
        cursor = self.db.cursor()
        cursor.execute("""DELETE FROM users
                            WHERE id = ?""",
                            (userid,))
        cursor.execute("""DELETE FROM ratings
                            WHERE rated_user_id = ? OR
                            rater_user_id = ?""",
                            (userid, userid,))
        self._commit()

class RatingSystem(callbacks.Plugin):
    """This plugin maintains a rating system among IRC users.
    Use commands 'rate' and 'unrate' to enter/remove your ratings.
    Use command 'getrating' to view a user's total rating and other details.
    """
    threaded = True

    def __init__(self, irc):
        self.__parent = super(RatingSystem, self)
        self.__parent.__init__(irc)
        self.filename = conf.supybot.directories.data.dirize('RatingSystem.db')
        self.db = RatingSystemDB(self.filename)
        self.db.open()

    def die(self):
        self.__parent.die()
        self.db.close()

    def _checkGPGAuth(self, irc, prefix):
        return irc.getCallback('GPG')._ident(prefix)

    def _checkGPGAuthByNick(self, irc, nick):
        return irc.getCallback('GPG')._identByNick(nick)

    def _ratingBoundsCheck(self, rating):
        if rating >= self.registryValue('ratingMin') and \
           rating <= self.registryValue('ratingMax'):
            return True
        return False

    def rate(self, irc, msg, args, nick, rating, notes):
        """<nick> <rating> [<notes>]

        Enters a rating for <nick> in the amount of <rating>. Use optional
        <notes> field to enter any notes you have about this user. <nick>
        must be the user's GPG-registered username, Your previously existing rating,
        if any, will be overwritten.
        """
        if nick.upper() in self.registryValue('blockedNicks'):
            irc.noReply()
            return
        if irc.nested:
            irc.error("This command cannot be used in a nested context.")
            return
        gpgauth = self._checkGPGAuth(irc, msg.prefix)
        if gpgauth is None:
            irc.error("For identification purposes, you must be authenticated "
                      "to use the rating system.")
            return
        userrating = self.db.get(gpgauth['nick'])
        if len(userrating) == 0:
            irc.error("You have to have received some ratings in order to rate "
                      "other users.")
            return
        trust = self._gettrust('nanotube', gpgauth['nick'])
        sumtrust = sum([t for t,n in trust])
        if self.registryValue('requirePositiveRating') and sumtrust < 0:
            irc.error("You do not meet qualifications for entering ratings.")
            return
        if gpgauth['nick'].lower() == nick.lower():
            irc.error("You cannot rate yourself.")
            return
        validratings = range(self.registryValue('ratingMin'),
                             self.registryValue('ratingMax')+1)
        validratings.remove(0)
        if rating not in validratings:
            irc.error("Rating must be in the interval [%s, %s] and cannot be zero." % \
                      (min(validratings), max(validratings)))
            return

        result = "Your rating of %s for user %s has been recorded." % (rating, nick,)

        sourceid = userrating[0][0]
        targetuserdata = self.db.get(nick)
        if len(targetuserdata) == 0:
            targetgpgdata = irc.getCallback('GPG').db.getByNick(nick)
            if len(targetgpgdata) == 0:
                irc.error("User doesn't exist in the Rating or GPG databases. User must be "
                                "GPG-registered to receive ratings.")
                return
            targetid = None
            replacementflag = False
        else:
            targetid = targetuserdata[0][0]
            priorrating = self.db.getExistingRating(sourceid, targetid)
            if len(priorrating) == 0:
                replacementflag = False
            else:
                replacementflag = True
                result = "Your rating for user %s has changed from %s to %s." % \
                        (nick, priorrating[0][4], rating,)
        self.db.rate(gpgauth['nick'], sourceid, nick, targetid, rating,
                     replacementflag, notes)
        if not world.testing:
            if not replacementflag:
                logmsg = "New rating | %s > %s > %s | %s" % (gpgauth['nick'],
                        rating, nick, notes)
            else:
                logmsg = "Rating change | Old rating %s | New rating: %s > %s > %s | %s" % \
                        (priorrating[0][4], gpgauth['nick'], rating, nick, notes,)
            irc.queueMsg(ircmsgs.privmsg("#bitcoin-otc-ratings", logmsg))
        irc.reply("Rating entry successful. %s" % (result,))
    rate = wrap(rate, ['something', 'int', optional('text')])

    def rated(self, irc, msg, args, nick):
        """<nick>

        Get the details about the rating you gave to <nick>, if any.
        """
        gpgauth = self._checkGPGAuth(irc, msg.prefix)
        if gpgauth is not None:
            sourcenick = gpgauth['nick']
        else:
            sourcenick = msg.nick
        data = self.db.getRatingDetail(sourcenick, nick)
        if len(data) == 0:
            irc.reply("You have not yet rated user %s" % (nick,))
            return
        data = data[0]
        irc.reply("You rated user %s on %s, with a rating of %s, and "
                  "supplied these additional notes: %s." % \
                  (nick,
                   time.ctime(data[0]),
                   data[1],
                   data[2]))
    rated = wrap(rated, ['something'])

    def unrate(self, irc, msg, args, nick):
        """<nick>

        Remove your rating for <nick> from the database.
        """
        gpgauth = self._checkGPGAuth(irc, msg.prefix)
        if gpgauth is None:
            irc.error("You must be authenticated to perform this operation.")
            return
        userrating = self.db.get(gpgauth['nick'])
        if len(userrating) == 0:
            irc.error("Your nick does not exist in the Rating database.")
            return
        sourceid = userrating[0][0]
        targetuserdata = self.db.get(nick)
        if len(targetuserdata) == 0:
            irc.error("The target nick does not exist in the database.")
            return
        targetid = targetuserdata[0][0]
        priorrating = self.db.getExistingRating(sourceid, targetid)
        if len(priorrating) == 0:
            irc.error("You have not given this nick a rating previously.")
            return
        self.db.unrate(gpgauth['nick'], sourceid, nick, targetid)
        if not world.testing:
            logmsg = "Rating removed | %s > %s > %s | %s" % (gpgauth['nick'],
                    priorrating[0][4], nick, priorrating[0][5])
            irc.queueMsg(ircmsgs.privmsg("#bitcoin-otc-ratings", logmsg))
        irc.reply("Successfully removed your rating for %s." % nick)
    unrate = wrap(unrate, ['something'])

    def _getrating(self, nick):
        """Get cumulative rating for user. For use from other plugins."""
        data = self.db.get(nick)
        if len(data) == 0:
            return None
        data = data[0]
        return data

    def getrating(self, irc, msg, args, nick):
        """<nick>

        Get rating information for <nick>.
        """
        authhost = self._checkGPGAuthByNick(irc, nick)
        if authhost is not None:
            authstatus = "Currently authenticated from hostmask %s ." % (authhost,)
        else:
            authstatus = "\x02WARNING: Currently not authenticated.\x02"
        data = self.db.get(nick)
        if len(data) == 0:
            irc.reply("This user has not yet been rated. " + authstatus)
            return
        data = data[0]
        
        if authhost is not None and authhost.split('!')[0].upper() != data[7].upper():
            authstatus += " CAUTION: irc nick differs from otc registered nick."

        irc.reply("%s User %s, rated since %s. "
                  "Cumulative rating %s, from %s total ratings. "
                  "Received ratings: %s positive, %s negative. "
                  "Sent ratings: %s positive, %s negative. "
                  "Details: %s" % \
                  (authstatus,
                   data[7],
                   time.ctime(data[2]),
                   data[1],
                   int(data[3]) + int(data[4]),
                   data[3],
                   data[4],
                   data[5],
                   data[6],
                   "http://b-otc.com/vrd?nick=%s" % (data[7],)))
    getrating = wrap(getrating, ['something'])

    def _gettrust(self, sourcenick, destnick):
        """Get a list of tuples for l1,l2... trust levels and number of associated
        connections. To be used from other plugins for trust checks.
        """
        result = []
        l1 = self.db.getRatingDetail(sourcenick, destnick)
        if len(l1) > 0:
            result.append((l1[0][1], 1,))
        else:
            result.append((0, 0,))
        l2 = self.db.getLevel2Ratings(sourcenick, destnick)
        if l2[0] is None:
            result.append((0,0,))
        else:
            result.append(l2)
        return result

    def gettrust(self, irc, msg, args, sourcenick, destnick):
        """[<sourcenick>] <destnick>
        
        Get trust paths for <destnick>, starting from <sourcenick>.
        If <sourcenick> is not supplied, your own nick is used as the source.
        See http://wiki.bitcoin-otc.com/wiki/OTC_Rating_System#Notes_about_gettrust
        """
        gpgauth = self._checkGPGAuth(irc, msg.prefix)
        if gpgauth is not None:
            sn = gpgauth['nick']
        else:
            sn = msg.nick
        if destnick is None:
            destnick = sourcenick
            sourcenick = sn

        authhost = self._checkGPGAuthByNick(irc, destnick)
        if authhost is not None:
            authstatus = "Currently authenticated from hostmask %s." % (authhost,)
        else:
            authstatus = "\x02WARNING: Currently not authenticated.\x02"
        if authhost is not None and authhost.split('!')[0].upper() != destnick.upper():
            authstatus += " \x02CAUTION: irc nick differs from otc registered nick.\x02"

        rs = self._getrating(destnick)
        if rs is not None:
            rs = time.ctime(rs[2])
        else:
            rs = 'never'
        trust = self._gettrust(sourcenick, destnick)
        irc.reply("%s Trust relationship from user %s to user %s: "
                        "Level 1: %s, Level 2: %s via %s connections. "
                        "Graph: http://b-otc.com/stg?source=%s&dest=%s | "
                        "WoT data: http://b-otc.com/vrd?nick=%s | "
                        "Rated since: %s" % \
                        (authstatus, sourcenick, destnick,
                        trust[0][0], trust[1][0], trust[1][1],
                        sourcenick, destnick, destnick, rs))
    gettrust = wrap(gettrust, ['something', optional('something')])

    def deleteuser(self, irc, msg, args, nick):
        """<nick>
        
        Delete user, and all his sent/received ratings, from the database.
        
        Requires owner privileges.
        """
        data = self.db.get(nick)
        if len(data) == 0:
            irc.error("No such user in the database.")
            return
        self.db.deleteuser(data[0][0])
        irc.reply("Successfully deleted user %s, id %s" % (nick, data[0][0],))
    deleteuser = wrap(deleteuser, ['owner','something'])


Class = RatingSystem


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
