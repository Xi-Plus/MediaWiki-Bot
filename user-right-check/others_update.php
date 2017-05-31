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
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lastusergetrights` = '0000-00-00 00:00:00'");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$userlist = array();
foreach ($row as $user) {
	$user["rights"] = explode("|", $user["rights"]);
	$userlist[$user["userid"]] = $user;
}

foreach ($userlist as $user) {
	echo $user["name"]."\n";
	$lastusergetrights = lastusergetrights($user["name"]);
	$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}userlist` SET `lastusergetrights` = :lastusergetrights WHERE `userid` = :userid");
	$sth->bindValue(":userid", $user["userid"]);
	$sth->bindValue(":lastusergetrights", $lastusergetrights);
	$res = $sth->execute();
	echo "update user=".$user["name"]." lastusergetrights=".$lastusergetrights."\n";
	WriteLog("update user=".$user["name"]." lastusergetrights=".$lastusergetrights);
	echo "\n";
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
