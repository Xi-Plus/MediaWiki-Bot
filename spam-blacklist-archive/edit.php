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

function converttime($chitime) {
	if (preg_match("/(\d{4})年(\d{1,2})月(\d{1,2})日 \(.{3}\) (\d{2})\:(\d{2}) \(UTC\)/", $chitime, $m)) {
		return strtotime($m[1] . "/" . $m[2] . "/" . $m[3] . " " . $m[4] . ":" . $m[5]);
	} else {
		exit("converttime fail\n");
	}
}
function convertdate($chitime) {
	if (preg_match("/(\d{4})年(\d{1,2})月(\d{1,2})日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $chitime, $m)) {
		return strtotime($m[1] . "/" . $m[2] . "/" . $m[3]);
	} else {
		exit("convertdate fail\n");
	}
}
function TimediffFormat($time) {
	if ($time < 60) {
		return $time . "秒";
	}

	if ($time < 60 * 50) {
		return round($time / 60) . "分";
	}

	if ($time < 60 * 60 * 23.5) {
		return round($time / (60 * 60)) . "小時";
	}

	return round($time / (60 * 60 * 24)) . "天";
}

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

login("bot");
$edittoken = edittoken();

$retention_time = file_get_contents($C["retention_time"]);
if ($retention_time === false) {
	$retention_time = $C["retention_time_default"];
	echo "Warning: fetch retention_time fail, use default value\n";
}
echo "archive before " . $retention_time . " ago (" . date("Y-m-d H:i:s", time() - $retention_time) . ")\n";

$retention_bytes = file_get_contents($C["retention_bytes"]);
if ($retention_bytes === false) {
	$retention_bytes = $C["retention_bytes_default"];
	echo "Warning: fetch retention_bytes fail, use default value\n";
}
echo "archive more than " . $retention_bytes . " bytes\n";

$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
	"action" => "query",
	"format" => "json",
	"prop" => "redirects",
	"titles" => "Template:Editprotected",
	"rdprop" => "title",
	"rdlimit" => "max",
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$pages = current($res["query"]["pages"]);
$redirects = $pages["redirects"];
$ep = [];
foreach ($redirects as $redirect) {
	if (preg_match("/^Template:(.+?)$/", $redirect["title"], $m)) {
		$ep[] = $m[1];
	}
}
$ep = "/{{(" . implode("|", $ep) . ")}}/i";
echo "EP match: " . $ep . "\n";

for ($i = $C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $C["from_page"],
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];
	echo "get main page\n";
	$pagesize = strlen($text);
	echo "page size: " . $pagesize . "\n";

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^( *==[^=]+?== *)$/m", $hash . "$1", $text);
	$text = explode($hash, $text);
	echo "find " . count($text) . " sections\n";

	$oldpagetext = $text[0];
	$newpagetext = array();
	$archive_count = array("all" => 0);
	unset($text[0]);
	echo "start split\n";
	foreach ($text as $temp) {
		if (preg_match("/(==[^=]+?==)/", $temp, $m)) {
			echo $m[1] . "\t";
		} else {
			echo "title get fail\t";
		}
		preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $temp, $m);
		$firsttime = time();
		$lasttime = 0;
		foreach ($m[0] as $timestr) {
			$time = converttime($timestr);
			if ($time < $firsttime) {
				$firsttime = $time;
			}

			if ($time > $lasttime) {
				$lasttime = $time;
			}

		}
		echo "time=" . date("Y/m/d H:i:s", $firsttime) . "-" . date("Y/m/d H:i:s", $lasttime) . "\tsize=" . strlen($temp) . "\n";
		if (preg_match($ep, $temp)) {
			$oldpagetext .= $temp;
			echo "not archive (EP)\t";
		} else if (time() - $lasttime > $retention_time || $pagesize > $retention_bytes) {
			$date = date("Y年", $firsttime);
			if (!isset($newpagetext[$date])) {
				$newpagetext[$date] = "";
				$archive_count[$date] = 0;
			}
			$newpagetext[$date] .= $temp;
			$archive_count[$date]++;
			$archive_count["all"]++;
			$pagesize -= strlen($temp);
			echo "archive to " . $date . "\t";
		} else {
			$oldpagetext .= $temp;
			echo "not archive\t";
		}
		echo "total pagesize remain " . $pagesize;
		echo "\n";
	}

	if ($archive_count["all"] === 0) {
		exit("no change\n");
	}

	echo "start edit\n";

	echo "edit main page\n";
	$summary = $C["summary_prefix"] . "：存檔" . $archive_count["all"] . "章節至" . count($newpagetext) . "頁面 (" . $C["summary_config_page"] . "：" . TimediffFormat($retention_time) . "無留言或頁面長度超過" . $retention_bytes . "位元組)";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["from_page"],
		"summary" => $summary,
		"text" => $oldpagetext,
		"minor" => "",
		"bot" => "",
		"token" => $edittoken,
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp,
	);
	echo "edit " . $C["from_page"] . " summary=" . $summary . "\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
	}

	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
		}
	} else {
		break;
	}
}

echo "edit archive page\n";
foreach ($newpagetext as $date => $newtext) {
	$page = $C["to_page_prefix"] . $date;
	$starttimestamp2 = time();
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $page,
	)));
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$oldtext = "{{Talkarchive|MediaWiki talk:Spam-blacklist}}\n";
	$basetimestamp2 = null;
	if (!isset($pages["missing"])) {
		$oldtext = $pages["revisions"][0]["*"];
		$basetimestamp2 = $pages["revisions"][0]["timestamp"];
		echo $page . " exist\n";
	} else {
		echo $page . " not exist\n";
	}

	$summary = $C["summary_prefix"] . "：存檔自[[" . $C["from_page"] . "]]共" . $archive_count[$date] . "個章節";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $page,
		"summary" => $summary,
		"text" => $oldtext . "\n" . $newtext,
		"minor" => "",
		"bot" => "",
		"token" => $edittoken,
		"starttimestamp" => $starttimestamp2,
	);
	if ($basetimestamp2 !== null) {
		$post["basetimestamp"] = $basetimestamp2;
	}
	echo "edit " . $page . " summary=" . $summary . "\n";
	for ($i = $C["fail_retry"]; $i > 0; $i--) {
		if (!$C["test"]) {
			$res = cURL($C["wikiapi"], $post);
		} else {
			$res = false;
		}

		$res = json_decode($res, true);
		if (isset($res["error"])) {
			echo "edit fail\n";
			if ($i === 1) {
				exit("quit\n");
			} else {
				echo "retry\n";
			}
		} else {
			break;
		}
	}
	echo "saved\n";
}

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
