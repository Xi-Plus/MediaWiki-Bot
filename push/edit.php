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

$options = getopt("", ["summary:"]);
if ($options === false) {
	exit("解析參數失敗\n");
}
if (isset($options["summary"])) {
	$C["summary_prefix"] = $options["summary"];
}
echo "summary = \"".$C["summary_prefix"]."\"\n";
fgets(STDIN);

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

foreach ($C["list"] as $local => $remote) {
	$local = $C["localprefix"].$remote;
	$remote = $C["remoteprefix"].$remote;
	echo $local." -> ".$remote."\n";
	$text = file_get_contents($local);
	if ($text === false) {
		echo "fetch local fail\n";
		continue;
	}

	$summary = $C["summary_prefix"];
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $remote,
		"summary" => $summary,
		"text" => $text,
		"token" => $edittoken
	);
	if (isset($C["minor"])) {
		$post["minor"] = "";
	}
	if (isset($C["bot"])) {
		$post["bot"] = "";
	}
	echo "edit ".$remote." summary=".$summary."\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__."/out.txt", $text);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
	}
}
