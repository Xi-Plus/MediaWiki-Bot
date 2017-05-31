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

// update userid
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist` WHERE `userid` = 0");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$botlist = array();
foreach ($row as $user) {
	$user["botrights"] = explode("|", $user["botrights"]);
	$botlist[$user["botid"]] = $user;
}

foreach ($botlist as $bot) {
	echo $bot["username"]."\n";
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

// update user lastedit
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}botlist` WHERE `userlastedit` = '0000-00-00 00:00:00' AND `userid` != -1");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$botlist = array();
foreach ($row as $user) {
	$user["botrights"] = explode("|", $user["botrights"]);
	$botlist[$user["botid"]] = $user;
}

foreach ($botlist as $bot) {
	echo $bot["username"]."\n";
	$userlastedit = lastedit($bot["username"]);
	$userlastlog = lastlog($bot["username"]);
	if ($userlastedit != '0000-00-00 00:00:00') {
		$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}botlist` SET `userlastedit` = :userlastedit, `userlastlog` = :userlastlog WHERE `botid` = :botid");
		$sth->bindValue(":botid", $bot["botid"]);
		$sth->bindValue(":userlastedit", $userlastedit);
		$sth->bindValue(":userlastlog", $userlastlog);
		$res = $sth->execute();
		echo "update bot=".$bot["botname"]." owner lastedit/log\n";
		WriteLog("update bot=".$bot["botname"]." owner lastedit/log");
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
