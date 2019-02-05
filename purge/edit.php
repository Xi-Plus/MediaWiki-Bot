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

function purge($page) {
	echo "purge " . $page . "\n";
	global $edittoken, $C;

	$starttimestamp = time();
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $page,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	if (!isset($res["query"]["pages"])) {
		echo $page . " not found!\n";
		return;
	}
	$pages = current($res["query"]["pages"]);
	if (isset($pages["missing"])) {
		echo $page . " not found!\n";
		return;
	}
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];

	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $page,
		"summary" => "purge",
		"text" => $text,
		"token" => $edittoken,
		"minor" => "",
		"nocreate" => "",
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp,
	);
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__ . "/out.txt", $text);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		var_dump($res["error"]);
	}
	if ($C["sleep"] !== 0) {
		usleep($C["sleep"] * 1000 * 1000);
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
if (isset($options["p"])) {
	if (is_string($options["p"])) {
		$options["p"] = [$options["p"]];
	}
	foreach ($options["p"] as $page) {
		purge($page);
	}
}
if (isset($options["t"])) {
	if (is_string($options["t"])) {
		$options["t"] = [$options["t"]];
	}
	foreach ($options["t"] as $template) {
		if (!preg_match("/^(t|template|模板)?:/i", $template)) {
			$template = "Template:" . $template;
		}
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
			purge($page["title"]);
		}
		purge($template);
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
			purge($page["title"]);
		}
		purge($category);
	}
}
