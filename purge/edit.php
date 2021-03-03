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

function purge($pages)
{
	global $edittoken, $C;

	if (!is_array($pages)) {
		$pages = [$pages];
	}
	$pages = implode('|', $pages);

	if ($C["sleep"] !== 0) {
		usleep($C["sleep"] * 1000 * 1000);
	}
	echo "purge " . $pages . "\n";

	$post = array(
		"action" => "purge",
		"format" => "json",
		"titles" => $pages,
		"forcelinkupdate" => "1",
		"token" => $edittoken,
	);
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "purge fail\n";
		var_dump($res["error"]);
	}
}
function multipurge($pages)
{
	foreach (array_chunk($pages, 10) as $chunkedpages) {
		purge($chunkedpages);
	}
}

$options = getopt("c:t:p:", ["target:", "sleep:"]);
if ($options === false) {
	exit("parse parameter failed\n");
}

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

if (isset($options["target"])) {
	$target = $options["target"];
	if (!isset($C["target"][$target])) {
		exit("target not accepted: " . implode("、", array_keys($C["target"])) . "\n");
	}
	foreach ($C["target"][$target] as $key => $value) {
		$C[$key] = $value;
	}
}
if (isset($options["sleep"])) {
	$C["sleep"] = $options["sleep"];
}

login("user");
$edittoken = edittoken();

echo "wikiapi = " . $C["wikiapi"] . "\n";
echo "sleep = " . $C["sleep"] . "\n";

if (!isset($options["p"]) && !isset($options["c"]) && !isset($options["t"])) {
	echo "no options given, input pages:\n";
	$options["p"] = [];
	while (true) {
		$line = trim(fgets(STDIN));
		if ($line === "") {
			break;
		}
		$options["p"][] = $line;
	}
}

$pages = [];

if (isset($options["p"])) {
	if (is_string($options["p"])) {
		$options["p"] = [$options["p"]];
	}
	$pages = array_merge($pages, $options["p"]);
}

if (isset($options["t"])) {
	if (is_string($options["t"])) {
		$options["t"] = [$options["t"]];
	}
	foreach ($options["t"] as $template) {
		echo "template " . $template . "\n";
		$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
			"action" => "query",
			"format" => "json",
			"list" => "embeddedin",
			"eititle" => $template,
			"eilimit" => "max",
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);
		$pagelist = $res["query"]["embeddedin"];
		foreach ($pagelist as $page) {
			$pages[] = $page["title"];
		}
		$pages[] = $template;
	}
}

if (isset($options["c"])) {
	if (is_string($options["c"])) {
		$options["c"] = [$options["c"]];
	}
	foreach ($options["c"] as $category) {
		if (!preg_match("/^(cat|category|分類|分类):/i", $category)) {
			$category = "Category:" . $category;
		}
		echo "category " . $category . "\n";
		$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
			"action" => "query",
			"format" => "json",
			"list" => "categorymembers",
			"cmtitle" => $category,
			"cmlimit" => "max",
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);
		$pagelist = $res["query"]["categorymembers"];
		foreach ($pagelist as $page) {
			$pages[] = $page["title"];
		}
		$pages[] = $category;
	}
}

multipurge($pages);
