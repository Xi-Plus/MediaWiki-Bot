<?php
if (count($argv) < 2) {
	exit("Require 1 arg.\n");
}

$wiki = $argv[1];

require __DIR__ . "/../config/config.php";
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include __DIR__ . "/config.$wiki.php";
require __DIR__ . "/../function/curl.php";
require __DIR__ . "/../function/login.php";
require __DIR__ . "/../function/edittoken.php";

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

login("user");
$edittoken = edittoken();

$protection_update = $C["protection_update"];
if (isset($argv[2])) {
	$protection_update = $argv[2];
}

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}page` WHERE `wiki` = :wiki AND `time` < :time");
$sth->bindValue(":wiki", $wiki);
$sth->bindValue(":time", date("Y-m-d H:i:s", strtotime($protection_update)));
$sth->execute();
$pagelist = $sth->fetchAll(PDO::FETCH_ASSOC);
$pages = [];
foreach ($pagelist as $temp) {
	$pages[$temp["title"]] = $temp;
}
echo "update " . count($pagelist) . " pages\n";

$pagelist = array_chunk($pagelist, 500, true);

foreach ($pagelist as $pagelist2) {
	$titles = [];
	foreach ($pagelist2 as $page) {
		$titles[] = $page["title"];
	}
	$titles = implode("|", $titles);

	echo "fetching\n";
	$res = cURL($C["wikiapi"], array(
		"action" => "query",
		"format" => "json",
		"prop" => "info",
		"titles" => $titles,
		"inprop" => "protection",
	));
	echo "fetched\n";
	if ($res === false) {
		exit("fetch fail\n");
	}
	$res = json_decode($res, true);
	$results = $res["query"]["pages"];

	foreach ($results as $result) {
		$title = $result["title"];
		if (!isset($pages[$title])) {
			echo "skip {$title}\n";
			continue;
		}
		$protect = ["edit" => "", "move" => ""];
		$redirect = (isset($result["redirect"]) ? 1 : 0);
		foreach ($result["protection"] as $protection) {
			$protect[$protection["type"]] = $protection["level"];
		}
		if (isset($protect["create"])) {
			$protect["edit"] = $protect["create"];
			$protect["move"] = "create";
			unset($protect["create"]);
		}
		if ($protect["edit"] != $pages[$title]["protectedit"] || $protect["move"] != $pages[$title]["protectmove"] || $redirect != $pages[$title]["redirect"]) {
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}page` SET `protectedit` = :protectedit, `protectmove` = :protectmove, `redirect` = :redirect, `time` = :time WHERE `wiki` = :wiki AND `title` = :title");
			$sth->bindValue(":wiki", $wiki);
			$sth->bindValue(":title", $title);
			$sth->bindValue(":protectedit", $protect["edit"]);
			$sth->bindValue(":protectmove", $protect["move"]);
			$sth->bindValue(":redirect", $redirect);
			$sth->bindValue(":time", date("Y-m-d H:i:s"));
			$res = $sth->execute();
			echo $result["title"] . " edit=" . $protect["edit"] . " move=" . $protect["move"] . " " . ($redirect ? "(redirect)" : "") . "\n";
			if ($res === false) {
				echo $sth->errorInfo()[2] . "\n";
			}
		} else {
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}page` SET `time` = :time WHERE `wiki` = :wiki AND `title` = :title");
			$sth->bindValue(":wiki", $wiki);
			$sth->bindValue(":title", $title);
			$sth->bindValue(":time", date("Y-m-d H:i:s"));
			$res = $sth->execute();
		}
	}
}

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
