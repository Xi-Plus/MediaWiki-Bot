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

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login("bot");
$edittoken = edittoken();

echo "fetch from database\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}`");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$blocklist = array();
foreach ($row as $block) {
	$blocklist[$block["id"]] = $block;
}

$bkcontinue = "";
while (true) {
	echo "fetch blocklist\n";
	$post = array(
		"action" => "query",
		"format" => "json",
		"list" => "blocks",
		"bklimit" => "max",
		"bkprop" => "id|user|expiry",
		"bkshow" => "temp|!account"
	);
	if ($bkcontinue !== "") {
		$post["bkcontinue"] = $bkcontinue;
	}
	$res = cURL($C["wikiapi"]."?".http_build_query($post));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$blocks = $res["query"]["blocks"];
	echo "get ".count($blocks)."\n";
	foreach ($blocks as $block) {
		if (!isset($blocklist[$block["id"]])) {
			if (!isset($block["user"])) {
				continue;
			}
			$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}` (`id`, `user`, `expiry`) VALUES (:id, :user, :expiry)");
			$sth->bindValue(":id", $block["id"]);
			$sth->bindValue(":user", $block["user"]);
			$sth->bindValue(":expiry", date("Y-m-d H:i:s", strtotime($block["expiry"])));
			$res2 = $sth->execute();
			if ($res2 === false) {
				echo $sth->errorInfo()[2]."\n";
			}
			echo $block["id"]." ".$block["user"]." ".$block["expiry"]."\n";
		} else {
			unset($blocklist[$block["id"]]);
		}
	}
	if (!isset($res["continue"])) {
		echo "fetch done\n";
		break;
	}
	$bkcontinue = $res["continue"]["bkcontinue"];
}

foreach ($blocklist as $block) {
	$sth = $G["db"]->prepare("DELETE FROM `{$C['DBTBprefix']}` WHERE `id` = :id");
	$sth->bindValue(":id", $block["id"]);
	$res = $sth->execute();
	echo "remove ".$block["user"]."\n";
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
