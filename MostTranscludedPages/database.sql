SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;


CREATE TABLE `MostTranscludedPages_log` (
  `id` int(11) NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `message` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `MostTranscludedPages_page` (
  `wiki` varchar(20) NOT NULL,
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  `count` int(11) NOT NULL,
  `protectedit` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `protectmove` varchar(20) CHARACTER SET utf8 COLLATE utf8_bin NOT NULL,
  `redirect` tinyint(1) NOT NULL,
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE `MostTranscludedPages_page_autoconfrimed` (
`title` varchar(255)
,`count` int(11)
,`protectedit` varchar(20)
,`protectmove` varchar(20)
,`redirect` tinyint(1)
,`time` timestamp
);
CREATE TABLE `MostTranscludedPages_page_sysop` (
`title` varchar(255)
,`count` int(11)
,`protectedit` varchar(20)
,`protectmove` varchar(20)
,`redirect` tinyint(1)
,`time` timestamp
);
DROP TABLE IF EXISTS `MostTranscludedPages_page_autoconfrimed`;

CREATE ALGORITHM=UNDEFINED DEFINER=`xiplus`@`localhost` SQL SECURITY DEFINER VIEW `MostTranscludedPages_page_autoconfrimed`  AS  select `MostTranscludedPages_page`.`title` AS `title`,`MostTranscludedPages_page`.`count` AS `count`,`MostTranscludedPages_page`.`protectedit` AS `protectedit`,`MostTranscludedPages_page`.`protectmove` AS `protectmove`,`MostTranscludedPages_page`.`redirect` AS `redirect`,`MostTranscludedPages_page`.`time` AS `time` from `MostTranscludedPages_page` where ((`MostTranscludedPages_page`.`count` < 5000) and (`MostTranscludedPages_page`.`count` >= 500) and (`MostTranscludedPages_page`.`protectedit` = '') and (not((`MostTranscludedPages_page`.`title` like '模块:%'))) and (`MostTranscludedPages_page`.`wiki` = 'zhwiki') and (not((`MostTranscludedPages_page`.`title` like 'MediaWiki:%'))) and (not((`MostTranscludedPages_page`.`title` regexp '^User:.+.(js|css)$')))) ;
DROP TABLE IF EXISTS `MostTranscludedPages_page_sysop`;

CREATE ALGORITHM=UNDEFINED DEFINER=`xiplus`@`localhost` SQL SECURITY DEFINER VIEW `MostTranscludedPages_page_sysop`  AS  select `MostTranscludedPages_page`.`title` AS `title`,`MostTranscludedPages_page`.`count` AS `count`,`MostTranscludedPages_page`.`protectedit` AS `protectedit`,`MostTranscludedPages_page`.`protectmove` AS `protectmove`,`MostTranscludedPages_page`.`redirect` AS `redirect`,`MostTranscludedPages_page`.`time` AS `time` from `MostTranscludedPages_page` where ((`MostTranscludedPages_page`.`count` >= 5000) and (`MostTranscludedPages_page`.`protectedit` <> 'sysop') and (`MostTranscludedPages_page`.`wiki` = 'zhwiki') and (not((`MostTranscludedPages_page`.`title` like 'MediaWiki:%'))) and (not((`MostTranscludedPages_page`.`title` like '模块:CGroup/%'))) and (not((`MostTranscludedPages_page`.`title` regexp '^User:.+.(js|css)$')))) ;


ALTER TABLE `MostTranscludedPages_log`
  ADD PRIMARY KEY (`id`);


ALTER TABLE `MostTranscludedPages_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
