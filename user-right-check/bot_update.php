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

login("bot");
$edittoken = edittoken();

echo "update userid\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist` WHERE `userid` = 0");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$botlist = array();
foreach ($row as $user) {
	$user["botrights"] = explode("|", $user["botrights"]);
	$botlist[$user["botid"]] = $user;
}

foreach ($botlist as $bot) {
	echo $bot["botname"]."\n";
	$userid = userid($bot["username"]);
	if ($userid != 0) {
		$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}botlist` SET `userid` = :userid WHERE `botid` = :botid");
		$sth->bindValue(":botid", $bot["botid"]);
		$sth->bindValue(":userid", $userid);
		$res = $sth->execute();
		echo "update bot=".$bot["botname"]." owner ".$bot["username"]." userid=".$userid."\n";
		WriteLog("update bot=".$bot["botname"]." owner ".$bot["username"]." userid=".$userid);
	}
}

echo "update bot lastedit\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist` WHERE `userid` > 0");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$botlist = array();
foreach ($row as $bot) {
	$bot["botrights"] = explode("|", $bot["botrights"]);
	$botlist[$bot["botid"]] = $bot;
}

foreach ($botlist as $bot) {
	$botlastedit = lastedit($bot["botname"]);
	$botlastlog = lastlog($bot["botname"]);
	echo $bot["botname"]."\t".$botlastedit."\t".$botlastlog."\n";
	if ($botlastedit != $bot["botlastedit"] || $botlastlog != $bot["botlastlog"]) {
		$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}botlist` SET `botlastedit` = :botlastedit, `botlastlog` = :botlastlog WHERE `botid` = :botid");
		$sth->bindValue(":botid", $bot["botid"]);
		$sth->bindValue(":botlastedit", $botlastedit);
		$sth->bindValue(":botlastlog", $botlastlog);
		$res = $sth->execute();
		echo "updated\n";
		WriteLog("update bot=".$bot["botname"]." lastedit/log");
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
