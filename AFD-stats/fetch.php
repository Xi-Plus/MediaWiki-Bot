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

$time = date("Y-m-d H:i:s");
echo "The time now is " . $time . " (UTC)\n";

login();
$C["edittoken"] = edittoken();

if (isset($argv[1])) {
	$C["fetchuser"] = $argv[1];
}
$C["usersign"] = $C['fetchuser'];
if (isset($argv[2])) {
	$C["usersign"] = $argv[2];
}
if (isset($argv[3])) {
	if (preg_match("/^\d+$/", $argv[3])) {
		$C["timelimit"] = time() - intval($argv[3]) * 86400;
	} else if (preg_match("/^\d+\/\d+\/\d+$/", $argv[3])) {
		$C["timelimit"] = strtotime($argv[3]);
	}
}
echo "fetch " . $C["fetchuser"] . "\n";
echo "sign " . $C["usersign"] . "\n";
echo "timelimit " . date("Y-m-d", $C["timelimit"]) . "\n";

$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
	"action" => "query",
	"action" => "query",
	"format" => "json",
	"list" => "usercontribs",
	"uclimit" => "max",
	"ucuser" => $C["fetchuser"],
	"ucnamespace" => "4",
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
if (isset($res["continue"])) {
	echo "Warning! result not all\n";
}
$pagelist = [];
echo count($res["query"]["usercontribs"]) . "\n";
if (count($res["query"]["usercontribs"]) === 0) {
	exit("no result\n");
}
foreach ($res["query"]["usercontribs"] as $usercontrib) {
	if (strpos($usercontrib["title"], "Wikipedia:頁面存廢討論/記錄/") !== false) {
		if (!in_array($usercontrib["title"], $pagelist)) {
			$pagelist[] = $usercontrib["title"];
		}
	}
}
echo count($pagelist) . "\n";

$voteregex = "/{{({$C['voteregex']}).+?\[\[User:" . str_replace([" ", "_"], "(?: |_)", $C["usersign"]) . "/i";
$nominatorregex = "/提交的維基人及時間：.*?\[\[User:" . str_replace([" ", "_"], "(?: |_)", $C["usersign"]) . "/i";
echo $voteregex . "\n";
echo $nominatorregex . "\n";

$out = "";
foreach ($pagelist as $key => $page) {
	echo $key . " " . $page . "\n";
	if (!preg_match("/^Wikipedia:頁面存廢討論\/記錄\/(\d{4}\/\d{2}\/\d{2})$/", $page, $m)) {
		echo "page name error\n";
		continue;
	} else if (strtotime($m[1]) < $C["timelimit"]) {
		echo "time out of limit\n";
		continue;
	}
	$text = file_get_contents("https://zh.wikipedia.org/wiki/" . $page . "?action=raw");

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^(== *(.+?) *== *)$/m", $hash . "$1", $text);
	$texts = explode($hash, $text);
	unset($texts[0]);
	foreach ($texts as $text) {
		preg_match("/^== *(.+?) *== *$/m", $text, $m);
		$title = $m[1];
		if (preg_match("/\[\[:?(.+?)\]\]/", $title, $m)) {
			$title = $m[1];
		}
		$result = "";
		if (preg_match("/{{delh\|([^\|}]+)/i", $text, $m)) {
			$result = $m[1];
		}
		if (preg_match($nominatorregex, $text)) {
			if (preg_match("/(转交自|轉交自)/", $text)) {
				echo $page . "," . $title . "," . "fwdcsd" . "," . $result . "\n";
				$out .= $page . "," . $title . "," . "fwdcsd" . "," . $result . "\n";
			} else {
				echo $page . "," . $title . "," . "nominator" . "," . $result . "\n";
				$out .= $page . "," . $title . "," . "nominator" . "," . $result . "\n";
			}
		} else if (preg_match($voteregex, $text, $m)) {
			$vote = $m[1];
			echo $page . "," . $title . "," . $vote . "," . $result . "\n";
			$out .= $page . "," . $title . "," . $vote . "," . $result . "\n";
		}
	}
}
file_put_contents(__DIR__ . "/list/" . $C["fetchuser"] . ".csv", $out);

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
