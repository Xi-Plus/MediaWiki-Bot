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

$options = getopt("", ["summary:", "file:", "wp", "github:"]);
if ($options === false) {
	exit("解析參數失敗\n");
}
if (isset($options["summary"])) {
	$C["summary_prefix"] = $options["summary"];
}
$files = [];
if (isset($options["file"])) {
	if (is_array($options["file"])) {
		foreach ($options["file"] as $file) {
			if (!isset($C["list"][$file])) {
				exit("--file ".$file." not found\n");
			} else {
				$files[]= $file;
			}
		}
	} else {
		if (!isset($C["list"][$options["file"]])) {
			exit("--file ".$options["file"]." not found\n");
		} else {
			$files[]= $options["file"];
		}
	}
} else {
	$files = array_keys($C["list"]);
}
if (isset($options["wp"])) {
	$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
	$C["cookiefile"] = __DIR__."/../tmp/push-wp-cookie.txt";
}
echo "target = ".$C["wikiapi"]."\n";
if (isset($options["github"])) {
	echo "source: ".$C["githubprefix"].$options["github"]."\n";
} else {
	echo "source: ".$C["localprefix"]."\n";
}
echo "summary = \"".$C["summary_prefix"]."\"\n";
echo "files = (".count($files).")\n  ".implode("\n  ", $files)."\n";

login($C["bot"]?"bot":"user");
$edittoken = edittoken();

echo "\npress any key to continue\n";
fgets(STDIN);

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

foreach ($C["list"] as $local => $remote) {
	if (!in_array($local, $files)) {
		continue;
	}
	if (isset($options["github"])) {
		$local = $C["githubprefix"].$options["github"]."/".$local;
	} else {
		$local = $C["localprefix"].$local;
	}
	$remote = $C["remoteprefix"].$remote;
	echo $local." -> ".$remote."\n";
	$text = @file_get_contents($local);
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
		var_dump($res["error"]);
	}
}
