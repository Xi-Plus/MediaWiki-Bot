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

echo "fetch from database\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}page` WHERE `wiki` = :wiki");
$sth->bindValue(":wiki", $wiki);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$pagelist = array();
foreach ($row as $page) {
	$pagelist[$page["title"]] = $page;
}

echo "fetch list\n";
$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "querypage",
	"qppage" => "Mostlinkedtemplates",
	"qplimit" => "max",
)));

if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$results = $res["query"]["querypage"]["results"];
if (count($results) === 0) {
	exit("No result returned\n");
}

foreach ($results as $page) {
	$title = $page["title"];
	if ($page['value'] < $C["min_usage"]) {
		continue;
	}
	if (!isset($pagelist[$title])) {
		$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}page` (`wiki`, `title`, `count`, `protectedit`, `protectmove`, `redirect`, `time`) VALUES (:wiki, :title, :count, :protectedit, :protectmove, :redirect, :time)");
		$sth->bindValue(":wiki", $wiki);
		$sth->bindValue(":title", $title);
		$sth->bindValue(":count", $page["value"]);
		$sth->bindValue(":protectedit", "");
		$sth->bindValue(":protectmove", "");
		$sth->bindValue(":redirect", 2);
		$sth->bindValue(":time", $C["TIME_MIN"]);
		$res = $sth->execute();
		if ($res === false) {
			echo $sth->errorInfo()[2] . "\n";
		}
		echo "new " . $page["title"] . " (" . $page["value"] . ")\n";
	} else {
		if ($pagelist[$title]["count"] != $page["value"]) {
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}page` SET `count` = :count WHERE `wiki` = :wiki AND `title` = :title");
			$sth->bindValue(":count", $page["value"]);
			$sth->bindValue(":wiki", $wiki);
			$sth->bindValue(":title", $title);
			$res = $sth->execute();
			if ($res === false) {
				echo $sth->errorInfo()[2] . "\n";
			}
			echo "update " . $page["title"] . " (" . $pagelist[$title]["count"] . "->" . $page["value"] . ")\n";
		}
		unset($pagelist[$title]);
	}
}

foreach ($pagelist as $page) {
	$sth = $G["db"]->prepare("DELETE FROM `{$C['DBTBprefix']}page` WHERE `wiki` = :wiki AND `title` = :title");
	$sth->bindValue(":wiki", $wiki);
	$sth->bindValue(":title", $page["title"]);
	$res = $sth->execute();
	echo "remove " . $page["title"] . " (" . $page["count"] . ")\n";
}

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
