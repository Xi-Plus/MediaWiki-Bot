<?php
require __DIR__ . "/../config/config.php";
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include __DIR__ . "/config.php";
require __DIR__ . "/../function/curl.php";
require __DIR__ . "/../function/login.php";
require __DIR__ . "/../function/edittoken.php";
require __DIR__ . "/../function/log.php";
require __DIR__ . "/function.php";

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

login("bot");
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($C["other_update_timelimit"]));

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime");
$sth->bindValue(":lasttime", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$userlist = array();
foreach ($row as $user) {
	$user["rights"] = explode("|", $user["rights"]);
	$userlist[$user["name"]] = $user;
}

echo "result count: " . count($userlist) . "\n";

$count = 0;
foreach ($userlist as $user) {
	echo (++$count) . " " . $user["name"] . "\t";
	$lastedit = lastedit($user["name"]);
	$lastlog = lastlog($user["name"]);
	$lastusergetrights = lastusergetrights($user["name"]);
	$lasttime = $user["lasttime"];
	if ($lastedit <= $user["lastedit"] && $lastlog <= $user["lastlog"] && $lastusergetrights <= $user["lastusergetrights"]) {
		echo "no update\n";
		continue;
	}
	$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}userlist` SET `lastedit` = :lastedit, `lastlog` = :lastlog, `lastusergetrights` = :lastusergetrights , `lasttime` = :lasttime WHERE `name` = :name");
	$sth->bindValue(":name", $user["name"]);
	$sth->bindValue(":lastedit", $lastedit);
	$sth->bindValue(":lastlog", $lastlog);
	$sth->bindValue(":lastusergetrights", $lastusergetrights);
	$sth->bindValue(":lasttime", max($lastedit, $lastlog, $lastusergetrights, $lasttime));
	$res = $sth->execute();
	echo " update lastedit=" . $lastedit . " lastlog=" . $lastlog . " lastusergetrights=" . $lastusergetrights . "\n";
	WriteLog("update user=" . $user["name"] . " lastedit=" . $lastedit . " lastlog=" . $lastlog . " lastusergetrights=" . $lastusergetrights);
}

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
