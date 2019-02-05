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

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

$config_page = file_get_contents($C["config_page"]);
if ($config_page === false) {
	exit("get config failed\n");
}
$cfg = json_decode($config_page, true);

if (!$cfg["enable"]) {
	exit("disabled\n");
}

var_dump($cfg);

login("bot");
$edittoken = edittoken();

$count = 0;
$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "categorymembers",
	"cmtitle" => $cfg["category"],
	"cmnamespace" => $cfg["namespace"],
	"cmlimit" => "max",
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$pagelist = $res["query"]["categorymembers"];

$logpage = [];
foreach ($pagelist as $page) {
	echo $page["title"] . "\n";
	$starttimestamp = time();
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"pageids" => $page["pageid"],
	)));
	if ($res === false) {
		echo "fetch page fail\n";
		continue;
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];

	if (preg_match($cfg["underconstruction_regex"], $text)) {
		$text = preg_replace($cfg["underconstruction_regex"], "", $text);
		$summary = $cfg["underconstruction_summary"];
	}
	if (preg_match($cfg["newpage_regex"], $text)) {
		$text = preg_replace($cfg["newpage_regex"], "", $text);
		$summary = $cfg["newpage_summary"];
	}
	if (preg_match($cfg["inuse_regex"], $text)) {
		$text = preg_replace($cfg["inuse_regex"], "", $text);
		$summary = $cfg["inuse_summary"];
	}

	if ($pages["revisions"][0]["*"] !== $text) {
		$logpage[] = $page["title"];
	}

	$post = array(
		"action" => "edit",
		"format" => "json",
		"pageid" => $page["pageid"],
		"summary" => $summary,
		"text" => $text,
		"token" => $edittoken,
		"minor" => "",
		"bot" => "",
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp,
	);
	echo "edit " . $page["title"] . " summary=" . $summary . "\n";

	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
	}

	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
	}
}

if (count($logpage) != 0 && $cfg["record"]) {
	$text = "";
	foreach ($logpage as $page) {
		$text .= "*[[" . $page . "]]\n";
	}
	$text .= "~~~~";

	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $cfg["log_page"],
		"summary" => $cfg["log_summary"],
		"text" => $text,
		"token" => $edittoken,
	);
	echo "edit " . $cfg["log_page"] . " summary=" . $cfg["log_summary"] . "\n";

	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
	}

	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
	}
}

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
