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

function purge($page) {
	echo "purge ".$page."\n";
	global $edittoken, $C;

	$starttimestamp = time();
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $page
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
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
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp
	);
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__."/out.txt", $text);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		var_dump($res["error"]);
	}
}

$options = getopt("c:t:p:");
if ($options === false) {
	exit("parse parameter failed\n");
}

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login("user");
$edittoken = edittoken();

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
		if (!preg_match("/^(t|template|模板):/i", $template)) {
			$template = "Template:".$template;
		}
		echo "template ".$template."\n";
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"format" => "json",
			"list" => "embeddedin",
			"eititle" => $template,
			"eilimit" => "max"
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
			$category = "Category:".$category;
		}
		echo "category ".$category."\n";
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"format" => "json",
			"list" => "categorymembers",
			"cmtitle" => $category,
			"cmlimit" => "max"
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
