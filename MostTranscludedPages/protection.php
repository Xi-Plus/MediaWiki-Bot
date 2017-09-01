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

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}page`");
$sth->execute();
$pagelist = $sth->fetchAll(PDO::FETCH_ASSOC);

$pagelist = array_chunk($pagelist, 500, true);

foreach ($pagelist as $pagelist2) {
	$titles = [];
	foreach ($pagelist2 as $page) {
		$titles []= $page["title"];
	}
	$titles = implode("|", $titles);

	$res = cURL($C["wikiapi"], array(
		"action" => "query",
		"format" => "json",
		"prop" => "info",
		"titles" => $titles,
		"inprop" => "protection"
	));
	if ($res === false) {
		exit("fetch fail\n");
	}
	$res = json_decode($res, true);
	$results = $res["query"]["pages"];

	foreach ($results as $result) {
		$protect = ["edit" => "", "move" => ""];
		foreach ($result["protection"] as $protection) {
			$protect[$protection["type"]] = $protection["level"];
		}

		$sth = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}page` SET `protectedit` = :protectedit, `protectmove` = :protectmove, `time` = :time WHERE `title` = :title");
		$sth->bindValue(":title", $result["title"]);
		$sth->bindValue(":protectedit", $protect["edit"]);
		$sth->bindValue(":protectmove", $protect["move"]);
		$sth->bindValue(":time", date("Y-m-d H:i:s"));
		$res = $sth->execute();
		echo $result["title"]." edit=".$protect["edit"]." move=".$protect["move"]."\n";
	}
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
