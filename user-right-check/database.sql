SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;


CREATE TABLE `user_right_check_botlist` (
  `botid` int(11) NOT NULL,
  `botname` varchar(255) NOT NULL,
  `botlastedit` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `botlastlog` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `botrights` varchar(255) NOT NULL DEFAULT '',
  `userid` int(11) NOT NULL DEFAULT '0',
  `username` varchar(255) NOT NULL DEFAULT '',
  `userlastedit` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `userlastlog` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `reported` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `user_right_check_log` (
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `message` text NOT NULL,
  `hash` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `user_right_check_userlist` (
  `name` varchar(255) CHARACTER SET utf8mb4 NOT NULL,
  `lastedit` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `lastlog` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `lastusergetrights` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `lasttime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `noticetime` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `rights` varchar(255) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


ALTER TABLE `user_right_check_botlist`
  ADD UNIQUE KEY `userid` (`botid`);

ALTER TABLE `user_right_check_log`
  ADD UNIQUE KEY `hash` (`hash`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
