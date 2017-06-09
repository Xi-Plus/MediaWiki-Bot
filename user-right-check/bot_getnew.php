<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");
require(__DIR__."/../function/log.php");
require(__DIR__."/function.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

// get bot list from database
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist`");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$botlist = array();
foreach ($row as $user) {
	$user["botrights"] = explode("|", $user["botrights"]);
	$botlist[$user["botid"]] = $user;
}

// query bot list
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "allusers",
	"augroup" => "bot",
	"auprop" => "groups",
	"aulimit" => "max"
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$allusers = $res["query"]["allusers"];
$count = 1;
foreach ($allusers as $bot) {
	echo ($count++)." ".$bot["name"]." ".$bot["userid"]."\n";
	if (!isset($botlist[$bot["userid"]])) {
		// get bot owner
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"prop" => "revisions",
			"format" => "json",
			"rvprop" => "content|timestamp",
			"titles" => "User:".$bot["name"]
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);
		$pages = current($res["query"]["pages"]);
		$userid = 0;
		$username = "";
		if (isset($pages["revisions"][0]["*"])) {
			$text = $pages["revisions"][0]["*"];
			if (preg_match("/{{Bot\|([^}]+)/i", $text, $m)) {
				$args = explode("|", $m[1]);
				foreach ($args as $arg) {
					if (strpos($arg, "=") === false) {
						$username = ucfirst($arg);
						break;
					}
				}
				
				$userid = userid($username);
				$userlastedit = lastedit($username);
				$userlastlog = lastlog($username);
			}
		}

		echo "owner: ".$username."\n";
		echo "owner userid: ".$userid."\n";
		echo "owner lastedit: ".$userlastedit."\n";
		echo "owner lastlog: ".$userlastlog."\n";

		$botlastedit = lastedit($bot["name"]);
		$botlastlog = lastlog($bot["name"]);

		echo "bot lastedit: ".$botlastedit."\n";
		echo "bot lastlog: ".$botlastlog."\n";

		$botrights = implode("|", userright($bot["name"]));
		echo "botrights: ".$botrights."\n";

		$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}botlist` (`botid`, `botname`, `botlastedit`, `botlastlog`, `botrights`, `userid`, `username`, `userlastedit`, `userlastlog`) VALUES (:botid, :botname, :botlastedit, :botlastlog, :botrights, :userid, :username, :userlastedit, :userlastlog)");
		$sth->bindValue(":botid", $bot["userid"]);
		$sth->bindValue(":botname", $bot["name"]);
		$sth->bindValue(":botlastedit", $botlastedit);
		$sth->bindValue(":botlastlog", $botlastlog);
		$sth->bindValue(":botrights", $botrights);
		$sth->bindValue(":userid", $userid);
		$sth->bindValue(":username", $username);
		$sth->bindValue(":userlastedit", $userlastedit);
		$sth->bindValue(":userlastlog", $userlastlog);
		$res = $sth->execute();
		WriteLog("new bot: ".$bot["name"]." ".$bot["userid"]);
	} else {
		sort($bot["groups"]);
		$rights = implode("|", $bot["groups"]);
		$botlist[$bot["userid"]]["botrights"] = implode("|", $botlist[$bot["userid"]]["botrights"]);
		if ($botlist[$bot["userid"]]["botrights"] != $rights) {
			echo $botlist[$bot["userid"]]["botrights"]." -> ".$rights."\n";
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}botlist` SET `botrights` = :botrights WHERE `botid` = :botid");
			$sth->bindValue(":botid", $bot["userid"]);
			$sth->bindValue(":botrights", $rights);
			$res = $sth->execute();
			WriteLog("update bot rights: ".$bot["name"]." ".$botlist[$bot["userid"]]["botrights"]."->".$rights);
		}
		unset($botlist[$bot["userid"]]);
	}
}
foreach ($botlist as $bot) {
	$sth = $G["db"]->prepare("DELETE FROM `{$C['DBTBprefix']}botlist` WHERE `botid` = :botid");
	$sth->bindValue(":botid", $bot["botid"]);
	$res = $sth->execute();
	echo "remove ".$bot["botname"]."\n";
	WriteLog("remove bot: ".$bot["botname"]." ".$bot["botid"]);
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
