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
	} else {
		unset($pagelist[$title]);
	}
}

foreach ($pagelist as $page) {
	$count = file_get_contents($C["templatecount"].$page["title"]);
	if ($res !== false) {
		$res = json_decode($res, true);
		if ($res["status"] && $res["result"] > $page["maxcount"]) {
			$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}page` SET `maxcount` = :maxcount, `starttime` = :starttime, `time` = :time WHERE `title` = :title");
			$sth->bindValue(":title", $result["title"]);
			$sth->bindValue(":maxcount", $res["result"]);
			$sth->bindValue(":starttime", date("Y-m-d H:i:s"));
			$sth->bindValue(":maxtime", date("Y-m-d H:i:s"));
			$res = $sth->execute();
		}
	} else {
		echo "fetch ".$page["title"]." fail\n";
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
