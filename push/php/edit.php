<?php
require __DIR__ . "/../../config/config.php";
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include __DIR__ . "/config.php";
require __DIR__ . "/../../function/curl.php";
require __DIR__ . "/../../function/login.php";
require __DIR__ . "/../../function/edittoken.php";

if ($C["test"]) {
	echo "test mode on\n";
}

echo "===== project =====\n";
$project = null;
if (count(array_keys($C["project"])) == 1) {
	$project = array_values($C["project"])[0];
}
while (is_null($project)) {
	echo "project list:\n";
	foreach (array_keys($C["project"]) as $key => $name) {
		echo "\t" . ($key + 1) . "\t" . $name . "\n";
	}
	echo "select a project:";
	$input = (int) fgets(STDIN) - 1;
	$project = @array_values($C["project"])[$input] ?? null;
}
var_dump($project);
echo "\n";

echo "===== web =====\n";
$web = null;
if (count($project["web"]) == 1) {
	$web = $C["web"][$project["web"][0]];
}
while (is_null($web)) {
	echo "web list:\n";
	foreach ($project["web"] as $key => $name) {
		echo "\t" . ($key + 1) . "\t" . $name . "\n";
	}
	echo "select a web:";
	$input = (int) fgets(STDIN) - 1;
	$web = @$C["web"][$project["web"][$input]] ?? null;
}
var_dump($web);
echo "\n";

echo "===== source =====\n";
$source = null;
if (count($project["source"]) == 1) {
	$source = $C["source"][$project["source"][0]];
}
while (is_null($source)) {
	echo "source list:\n";
	foreach ($project["source"] as $key => $name) {
		echo "\t" . ($key + 1) . "\t" . $name . "\n";
	}
	echo "select a source:";
	$input = (int) fgets(STDIN) - 1;
	$source = @$C["source"][$project["source"][$input]] ?? null;
}
var_dump($source);
echo "\n";

echo "===== target =====\n";
$target = null;
if (count($project["target"]) == 1) {
	$target = $C["target"][$project["target"][0]];
}
while (is_null($target)) {
	echo "target list:\n";
	foreach ($project["target"] as $key => $name) {
		echo "\t" . ($key + 1) . "\t" . $name . "\n";
	}
	echo "select a target:";
	$input = (int) fgets(STDIN) - 1;
	$target = @$C["target"][$project["target"][$input]] ?? null;
}
var_dump($target);
echo "\n";

echo "===== files =====\n";
$files = [];
if (count($project["files"]) == 1) {
	$files = $project["files"];
}
echo "files list:\n";
$key = 0;
foreach ($project["files"] as $from => $to) {
	echo "\t" . (++$key) . "\t" . $from . "\t" . $to . "\n";
}
echo "select a files:";
$input = fgets(STDIN);
$input = str_replace([" ", ","], " ", $input);
$input = explode(" ", $input);
foreach ($input as $key) {
	$key = (int) $key - 1;
	if (isset(array_keys($project["files"])[$key])) {
		$files[array_keys($project["files"])[$key]] = array_values($project["files"])[$key];
	}
}
if (count($files) == 0) {
	$files = $project["files"];
}
var_dump($files);
echo "\n";

$summary = $project["summary"];
echo "summary:" . $summary . "\n";
echo "new summary:";
$input = trim(fgets(STDIN));
if ($input !== "") {
	$summary = $input;
}
var_dump($summary);
echo "\n";

$C["wikiapi"] = $web["wikiapi"];
$C["user"] = $web["user"];
$C["pass"] = $web["pass"];
$C["cookiefile"] = $web["cookiefile"];

echo "wikiapi = " . $C["wikiapi"] . "\n";
echo "source = " . $source . "\n";
echo "target = " . $target . "\n";
echo "summary = \"" . $summary . "\"\n";
echo "files (" . count($files) . ") =\n";
foreach ($files as $from => $to) {
	echo "\t" . $source . $from . "\t" . $target . $to . "\n";
}
echo "\n";

login($web["bot"] ? "bot" : "user");
$edittoken = edittoken();

echo "\npress any key to continue\n";
fgets(STDIN);

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

foreach ($files as $from => $to) {
	$from = $source . $from;
	$to = $target . $to;
	echo $from . " -> " . $to . "\n";
	$text = @file_get_contents($from);
	if ($text === false) {
		echo "fetch from fail\n";
		continue;
	}

	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $to,
		"summary" => $summary,
		"text" => $text,
		"token" => $edittoken,
	);
	if ($web["minor"]) {
		$post["minor"] = "";
	}
	if ($web["bot"]) {
		$post["bot"] = "";
	}
	if ($web["nocreate"]) {
		$post["nocreate"] = "";
	}
	echo "edit " . $to . " summary=" . $summary . "\n";
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
}
