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
require(__DIR__."/function.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

echo "fetch from database\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist`");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$userlist = array();
foreach ($row as $user) {
	$userlist[$user["name"]] = $user;
}

echo "fetch from web\n";
$text = file_get_contents($C["quarry"]);
if ($text === false) {
	echo "fetch fail\n";
	continue;
}
if (!preg_match('/"qrun_id": (\d+),/', $text, $m)) {
	echo "match fail\n";
	continue;
}
$text = file_get_contents("https://quarry.wmflabs.org/run/".$m[1]."/output/0/json");
if ($text === false) {
	echo "fetch fail\n";
	continue;
}
$text = json_decode($text, true);
$data = $text["rows"];

echo "start check\n";
foreach ($data as $key => $user) {
	$name = $user[0];
	if (!isset($userlist[$name])) {
		echo $name." (new)\t";
		$lastedit = lastedit($name);

		echo "lastedit: ".$lastedit." ".$user[2]." ".strlen($user[1])."\n";

		$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}userlist` (`name`, `lastedit`, `sign`, `signlen`) VALUES (:name, :lastedit, :sign, :signlen)");
		$sth->bindValue(":name", $name);
		$sth->bindValue(":lastedit", $lastedit);
		$sth->bindValue(":sign", $user[1]);
		$sth->bindValue(":signlen", $user[2]);
		$res = $sth->execute();
		if ($res === false) {
			echo $sth->errorInfo()[2]."\n";
		}
	} else {
		if ($user[1] !== $userlist[$name]["sign"]) {
			echo $name." (update)\t";
			$lastedit = lastedit($name);

			echo "lastedit: ".$lastedit." ".$user[2]." ".strlen($user[1])."\n";

			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}userlist` SET `sign` = :sign, `signlen` = :signlen WHERE `name` = :name");
			$sth->bindValue(":name", $name);
			$sth->bindValue(":sign", $user[1]);
			$sth->bindValue(":signlen", $user[2]);
			$res = $sth->execute();
			if ($res === false) {
				echo $sth->errorInfo()[2]."\n";
			}
		}
		unset($userlist[$name]);
	}
}
foreach ($userlist as $user) {
	$sth = $G["db"]->prepare("DELETE FROM `{$C['DBTBprefix']}userlist` WHERE `name` = :name");
	$sth->bindValue(":name", $user["name"]);
	$res = $sth->execute();
	echo "remove ".$user["name"]."\n";
}
