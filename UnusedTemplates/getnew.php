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

login();
$edittoken = edittoken();

echo "fetch from database\n";
$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}page`");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$pagelist = array();
foreach ($row as $page) {
	$pagelist[$page["title"]] = $page;
}

echo "fetch list\n";
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "querypage",
	"qppage" => "Unusedtemplates",
	"qplimit" => "max"
)));

if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$results = $res["query"]["querypage"]["results"];

foreach ($results as $page) {
	$title = $page["title"];
	if (!isset($pagelist[$title])) {
		$sth = $G["db"]->prepare("INSERT INTO `{$C['DBTBprefix']}page` (`title`, `starttime`, `maxused`, `maxtime`) VALUES (:title, :starttime, :maxused, :maxtime)");
		$sth->bindValue(":title", $title);
		$sth->bindValue(":starttime", date("Y-m-d H:i:s"));
		$sth->bindValue(":maxused", 0);
		$sth->bindValue(":maxtime", date("Y-m-d H:i:s"));
		$res = $sth->execute();
		if ($res === false) {
			echo $sth->errorInfo()[2]."\n";
		}
		echo "new ".$title."\n";
	} else {
		unset($pagelist[$title]);
	}
}

foreach ($pagelist as $page) {
	$count = @file_get_contents($C["templatecount"].urlencode($page["title"]));
	if ($count !== false) {
		$count = json_decode($count, true);
		if ($count["status"] && $count["result"] > $page["maxused"]) {
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}page` SET `maxused` = :maxused, `starttime` = :starttime, `maxtime` = :maxtime WHERE `title` = :title");
			$sth->bindValue(":title", $page["title"]);
			$sth->bindValue(":maxused", $count["result"]);
			$sth->bindValue(":starttime", ($page["maxused"]==0?date("Y-m-d H:i:s"):$page["starttime"]));
			$sth->bindValue(":maxtime", date("Y-m-d H:i:s"));
			$res = $sth->execute();
			echo "used ".$page["title"]." (".$page["maxused"]."->".$count["result"].")\n";
		}
	} else {
		echo "fetch ".$page["title"]." fail\n";
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
