<?php
require __DIR__ . "/../config/config.php";
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include __DIR__ . "/config.php";
require __DIR__ . "/function.php";
require __DIR__ . "/../function/curl.php";
require __DIR__ . "/../function/login.php";
require __DIR__ . "/../function/edittoken.php";

$time = date("Y-m-d H:i:s");
echo "The time now is " . $time . " (UTC)\n";

login();
$C["edittoken"] = edittoken();

if (isset($argv[1])) {
	$C["page"] = $argv[1];
}
echo "fetch " . $C["page"] . "\n";

$result = [];

echo "section 2\n";
$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
	"action" => "query",
	"prop" => "revisions",
	"format" => "json",
	"rvprop" => "ids|timestamp|user|content",
	"rvlimit" => "max",
	"rvsection" => "2",
	"titles" => $C["page"],
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
if (isset($res["continue"])) {
	echo "Warning! result not all\n";
}
$pages = current($res["query"]["pages"]);
foreach ($pages["revisions"] as $revision) {
	$result[$revision["revid"]] = [
		"revid" => $revision["revid"],
		"user" => $revision["user"],
		"timestamp" => date("Y-m-d H:i:s", strtotime($revision["timestamp"])),
		"support" => 0,
		"oppose" => 0,
		"neutral" => 0,
	];
	$count = preg_match_all("/^#[^#:*]/m", $revision["*"]);
	if (strpos($revision["*"], "===支持===") !== false) {
		$result[$revision["revid"]]["support"] = $count;
	} else if (strpos($revision["*"], "===反對===") !== false) {
		$result[$revision["revid"]]["oppose"] = $count;
	} else if (strpos($revision["*"], "===中立===") !== false) {
		$result[$revision["revid"]]["neutral"] = $count;
	}
}

for ($i = 3; $i <= 5; $i++) {
	echo "section $i\n";
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "ids|timestamp|user|content",
		"rvlimit" => "max",
		"rvsection" => $i,
		"titles" => $C["page"],
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	if (isset($res["continue"])) {
		echo "Warning! result not all\n";
	}
	$pages = current($res["query"]["pages"]);
	foreach ($pages["revisions"] as $revision) {
		$count = preg_match_all("/^#[^#:*]/m", $revision["*"]);
		if (strpos($revision["*"], "===支持===") !== false) {
			$result[$revision["revid"]]["support"] = $count;
		} else if (strpos($revision["*"], "===反對===") !== false) {
			$result[$revision["revid"]]["oppose"] = $count;
		} else if (strpos($revision["*"], "===中立===") !== false) {
			$result[$revision["revid"]]["neutral"] = $count;
		}
	}
}

$out = "";
$count = 0;
echo count($result) . "\n";
ksort($result);
foreach ($result as $row) {
	if ($count) {
		$out .= ",\n";
	}
	if ($row["support"] + $row["oppose"] == 0) {
		$percent = 0;
	} else {
		$percent = round(100 * $row["support"] / ($row["support"] + $row["oppose"]), 1);
	}
	$out .= "[";
	$out .= '"' . $row["timestamp"] . '",';
	$out .= $row["support"] . ',';
	$out .= $row["oppose"] . ',';
	$out .= $row["neutral"] . ',';
	$out .= $percent . ',';
	$out .= '80,';
	$out .= '"' . $row["timestamp"] . " " . $row["user"] . ' ' . $row["support"] . '/' . $row["oppose"] . '/' . $row["neutral"] . ' ' . $percent . '%"';
	$out .= "]";
	$count++;
}
$output = file_get_contents(__DIR__ . "/template.html");
$output = str_replace("<!--title-->", $C["page"], $output);
$output = str_replace("/*title*/", "+'" . $C["page"] . "'", $output);
$output = str_replace("/*data*/", $out, $output);
$output = str_replace("<!--time-->", $time, $output);
$result = array_reverse($result);
$comment = voting_info($result[0]["support"], $result[0]["oppose"]);
$output = str_replace("<!--comment-->", $comment, $output);
$output = str_replace("Wikipedia:申请成为管理员/Example", $C["page"], $output);
@mkdir(__DIR__ . "/list");
$outpath = __DIR__ . "/list/" . str_replace([":", "/"], ["_", "_"], $C["page"]) . ".html";
echo "output: " . $outpath . "\n";
file_put_contents($outpath, $output);

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
