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

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

login("bot");
$edittoken = edittoken();

echo "fetch from database\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}`");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$userlist = array();
foreach ($row as $user) {
	$userlist[$user["name"]] = $user;
}

$aufrom = "";
while (true) {
	echo "fetch userlist\n";
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "allusers",
		"aufrom" => $aufrom,
		"aulimit" => "max",
		"auactiveusers" => 1,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$allusers = $res["query"]["allusers"];
	foreach ($allusers as $user) {
		if (!isset($userlist[$user["name"]])) {
			$res2 = cURL($C["wikiapi"] . "?" . http_build_query(array(
				"action" => "antispoof",
				"format" => "json",
				"username" => $user["name"],
			)));
			if ($res2 === false) {
				exit("fetch page fail\n");
			}
			$res2 = json_decode($res2, true);
			if (isset($res2["antispoof"]["normalised"])) {
				$normalised = substr($res2["antispoof"]["normalised"], 3);
			} else {
				$normalised = "";
			}
			$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}` (`name`, `normalised`, `recentactions`, `recenteditcount`) VALUES (:name, :normalised, :recentactions, :recenteditcount)");
			$sth->bindValue(":name", $user["name"]);
			$sth->bindValue(":normalised", $normalised);
			$sth->bindValue(":recentactions", $user["recentactions"]);
			$sth->bindValue(":recenteditcount", $user["recenteditcount"]);
			$res2 = $sth->execute();
			if ($res2 === false) {
				echo $sth->errorInfo()[2] . "\n";
			}
			echo $user["name"] . " " . $normalised . "\n";
		} else {
			unset($userlist[$user["name"]]);
		}
	}
	if (!isset($res["continue"])) {
		echo "fetch done\n";
		break;
	}
	$aufrom = $res["continue"]["aufrom"];
}

foreach ($userlist as $user) {
	$sth = $G["db"]->prepare("DELETE FROM `{$C['DBTBprefix']}` WHERE `name` = :name");
	$sth->bindValue(":name", $user["name"]);
	$res = $sth->execute();
	echo "remove " . $user["name"] . "\n";
}

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
