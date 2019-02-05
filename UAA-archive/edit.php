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

$year = date("Y");
$half = (date("n") <= 6);

for ($i = $C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $cfg["main_page_name"],
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];
	echo "get main page\n";

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^(\*\s*{{\s*user-uaa\s*\|)/mi", $hash . "$1", $text);
	$text = explode($hash, $text);
	$oldpagetext = $text[0];
	$newpagetext = "";
	unset($text[0]);
	echo "find " . count($text) . " reports\n";

	$archive_count = 0;
	foreach ($text as $temp) {
		$temp = trim($temp);
		$blocked = false;
		$starttime = time();
		$lasttime = 0;
		if (preg_match("/{{user-uaa\|(?:1=)?(.+?)}}/", $temp, $m)) {
			$user = $m[1];
			echo "User:" . $user . "\t";
			$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
				"action" => "query",
				"format" => "json",
				"list" => "users",
				"usprop" => "blockinfo",
				"ususers" => $user,
			)));
			if ($res === false) {
				exit("fetch page fail\n");
			}
			$res = json_decode($res, true);
			if (isset($res["query"]["users"][0]["blockexpiry"]) && $res["query"]["users"][0]["blockexpiry"] === "infinity") {
				$blocked = true;
				$lasttime = strtotime($res["query"]["users"][0]["blockedtimestamp"]);
			}
		} else if (preg_match("/^\* *{{deltalk|/i", $temp)) {
			echo "Deltalk\t";
			$blocked = true;
		} else {
			echo "Unknown user\t";
		}
		echo ($blocked ? "blocked" : "not blocked") . "\t";

		if (preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $temp, $m)) {
			foreach ($m[0] as $timestr) {
				$time = converttime($timestr);
				if ($time < $starttime) {
					$starttime = $time;
				}

				if ($time > $lasttime) {
					$lasttime = $time;
				}

			}
		} else {
			$lasttime = time();
			$temp .= "{{subst:Unsigned-before|~~~~~}}";
		}
		echo date("Y/m/d H:i", $starttime) . "\t";
		echo date("Y/m/d H:i", $lasttime) . "\t";

		if (
			(
				$blocked
				&& time() - $lasttime > $cfg["time_to_live_for_blocked"])
			|| (
				!$blocked
				&& time() - $lasttime > $cfg["time_to_live_for_not_blocked"]
				&& time() - $starttime > $cfg["minimum_time_to_live_for_not_blocked"])
		) {
			echo "archive\n";
			$newpagetext .= "\n" . $temp;
			$archive_count++;
		} else {
			echo "not archive\n";
			$oldpagetext .= "\n" . $temp;
		}
	}

	if ($archive_count === 0) {
		exit("no change\n");
	}

	echo "start edit\n";

	echo "edit main page\n";
	$summary = sprintf($cfg["main_page_summary"], $archive_count);
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $cfg["main_page_name"],
		"summary" => $summary,
		"text" => $oldpagetext,
		"token" => $edittoken,
		"minor" => "",
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp,
	);
	echo "edit " . $cfg["main_page_name"] . " summary=" . $summary . "\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents("out1.txt", $oldpagetext);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
			continue;
		}
	} else {
		echo "saved\n";
	}

	echo "edit archive page\n";
	$page = sprintf(
		$cfg["archive_page_name"],
		$year,
		($half ? $cfg["archive_page_name_first_half_year"] : $cfg["archive_page_name_second_half_year"])
	);
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

	$oldtext = sprintf(
		$cfg["archive_page_preload"],
		$year,
		($half ? $cfg["first_half_year"] : $cfg["second_half_year"])
	);

	$basetimestamp2 = null;
	if (!isset($pages["missing"])) {
		$oldtext = trim($pages["revisions"][0]["*"]);
		$basetimestamp2 = $pages["revisions"][0]["timestamp"];
		echo $page . " exist\n";
	} else {
		echo $page . " not exist\n";
	}

	$oldtext .= "\n" . trim($newpagetext);

	$text = preg_replace("/\n{3,}/", "\n\n", $oldtext);

	$summary = sprintf($cfg["archive_page_summary"], $archive_count);
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $page,
		"summary" => $summary,
		"text" => $text,
		"token" => $edittoken,
		"minor" => "",
		"starttimestamp" => $starttimestamp2,
	);
	if ($basetimestamp2 !== null) {
		$post["basetimestamp"] = $basetimestamp2;
	}
	echo "edit " . $page . " summary=" . $summary . "\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents("out2.txt", $text);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
			continue;
		}
	} else {
		echo "saved\n";
		break;
	}
}

$spendtime = (microtime(true) - $starttime);
echo "spend " . $spendtime . " s.\n";
